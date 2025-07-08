import datetime
import json
import traceback
from datetime import time

import jwt
from jwt.algorithms import RSAAlgorithm
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import logging

from PROFILE.models import User
from letraz_server import settings
from letraz_server.contrib.sdks.clerk import ClerkSDK
from letraz_server.contrib.sdks.knock import KnockSDK
from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.{__name__}'
logger = logging.getLogger(__module_name)


class ClerkAuthenticationMiddleware(BaseAuthentication):
    def __init__(self):
        self.clerk = ClerkSDK(
            frontend_api_url=settings.CLERK_FRONTEND_API_URL,
            secret_key=settings.CLERK_SECRET_KEY
        )
        self.knock = KnockSDK(api_key=settings.KNOCK_API_KEY)

    def authenticate(self, request):
        authentication_cookies = request.COOKIES
        authentication_header = request.headers.get('Authorization')
        if not (authentication_cookies.get('__session') or authentication_header):
            return None, None
        try:
            if authentication_cookies.get('__session'):
                logger.debug(f'AUTH_TYPE :: {request.method}: {request.get_full_path()} -> Authenticate with Cookies')
                token = authentication_cookies.get('__session')
            elif authentication_header.split(' ')[0] == 'Bearer':
                logger.debug(f'AUTH_TYPE :: {request.method}: {request.get_full_path()} -> Authenticate with Header')
                token = authentication_header.split(' ')[1]
            else:
                raise AuthenticationFailed('Token must be a bearer token or session cookie.')
        except IndexError:
            raise AuthenticationFailed('Bearer token not provided!')
        except Exception as e:
            logger.exception(e)
            raise AuthenticationFailed('Invalid bearer token provided!')
        user = self.decode_jwt(token)
        logger.debug(f'Authenticated user: {user}')
        return user, None

    def decode_jwt(self, token):
        jwks_data = self.clerk.get_jwks()
        try:
            if not jwks_data.get('keys'):
                logger.error('Invalid JWKS: missing or empty keys array')
                raise AuthenticationFailed('Invalid JWKS format')
            
            jwk_data = jwks_data['keys'][0]
            try:
                jwk_str = json.dumps(jwk_data)
            except (TypeError, ValueError) as e:
                logger.error(f'Failed to serialize JWK: {e}')
                raise AuthenticationFailed('Invalid key format in JWKS')
                
            public_key = RSAAlgorithm.from_jwk(jwk_str)
        except IndexError:
            logger.error('Invalid JWKS: keys array is empty')
            raise AuthenticationFailed('Invalid JWKS format')
        except Exception as e:
            logger.error(f'Failed to parse JWKS: {e}')
            raise AuthenticationFailed('Failed to process JWKS')
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_signature": True}
            )
            logger.debug(f'decode_jwt Payload: {json.dumps(payload)}')
            user_id = payload.get('sub') if payload else None
            if user_id:
                user, created = User.objects.get_or_create(id=user_id)

                logger.debug(f'decode_jwt user, created: {user} | {created}')
                if created:
                    found, info = self.clerk.fetch_user_info(user.id)
                    if not user:
                        return None
                    else:
                        if found:
                            user.email = info["email_address"]
                            user.first_name = info["first_name"]
                            user.last_name = info["last_name"]
                            user.last_login = info["last_login"]
                        user.save()
                        
                        # Create customer in Knock after successful user creation
                        self.knock.create_customer_from_user(user)
                        
                return user
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired!")
        except jwt.DecodeError as e:
            raise AuthenticationFailed("Token decode error!")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token!")
        except Exception as e:
            logger.exception(e)
            raise AuthenticationFailed("Unexpected Token decode error!")
        return None
