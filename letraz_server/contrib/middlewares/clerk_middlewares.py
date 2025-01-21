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
from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.{__name__}'
logger = logging.getLogger(__module_name)


class ClerkAuthenticationMiddleware(BaseAuthentication):
    def __init__(self):
        self.clerk = ClerkSDK(
            frontend_api_url=settings.CLERK_FRONTEND_API_URL,
            secret_key=settings.CLERK_SECRET_KEY
        )

    def authenticate(self, request):
        start_time = datetime.datetime.now()
        authentication_header = request.headers.get('Authorization')
        logger.debug(authentication_header)
        if not authentication_header:
            return None, None
        try:
            if not authentication_header.split(' ')[0] == 'Bearer':
                raise AuthenticationFailed('Token must be a bearer token!')
            token = authentication_header.split(' ')[1]
            # logger.debug(request_state)
        except IndexError:
            raise AuthenticationFailed('Bearer token not provided!')
        except Exception as e:
            logger.exception(e)
            raise AuthenticationFailed('Invalid bearer token provided!')
        user = self.decode_jwt(token)
        end_time = datetime.datetime.now()
        logger.debug('Authenticated user: ', user)
        logger.debug('Time taken for authentication: ', end_time-start_time, 'ms')
        return user, None

    def decode_jwt(self, token):
        jwks_data = self.clerk.get_jwks()
        public_key = RSAAlgorithm.from_jwk(jwks_data['keys'][0])
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_signature": True}
            )
            logger.debug('decode_jwt Payload: ', json.dumps(payload))
            user_id = payload.get('sub') if payload else None
            logger.debug('decode_jwt user_id: ', user_id)
            if user_id:
                user, created = User.objects.get_or_create(id=user_id)

                logger.debug('decode_jwt user, created: ', user, ' | ', created)
                if created:
                    found, info = self.clerk.fetch_user_info(user.id)
                    logger.debug('decode_jwt found, info: ', found, ' | ', info)
                    if not user:
                        return None
                    else:
                        if found:
                            user.email = info["email_address"]
                            user.first_name = info["first_name"]
                            user.last_name = info["last_name"]
                            user.last_login = info["last_login"]
                        user.save()
                logger.debug('decode_jwt user: ', user)
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
