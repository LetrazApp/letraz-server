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
from CORE.models import Waitlist
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
        # First, decode the JWT header to get the kid
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            if not kid:
                logger.error('JWT header missing kid')
                raise AuthenticationFailed('Invalid token: missing key ID')
        except jwt.DecodeError as e:
            logger.error(f'Failed to decode JWT header: {e}')
            raise AuthenticationFailed('Invalid token format')
        
        # Get JWKS data
        jwks_data = self.clerk.get_jwks()
        try:
            if not jwks_data.get('keys'):
                logger.error('Invalid JWKS: missing or empty keys array')
                raise AuthenticationFailed('Invalid JWKS format')
            
            # Find the key that matches the kid
            jwk_data = None
            for key in jwks_data['keys']:
                if key.get('kid') == kid:
                    jwk_data = key
                    break
            
            if not jwk_data:
                logger.error(f'No matching key found for kid: {kid}')
                raise AuthenticationFailed('Invalid token: key not found')
            
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

                        # Remove waitlist entry if user email matches
                        if found and info.get("email_address"):
                            self._remove_waitlist_entry(info["email_address"])

                        # Create customer in Knock with email conflict handling
                        if found:
                            self._create_knock_customer_for_new_user(user, info)
                        else:
                            # Even without Clerk info, we should handle email conflicts
                            # Convert Django user to user_info format for consistency
                            user_info_from_django = {
                                'email_address': user.email or '',
                                'first_name': user.first_name or '',
                                'last_name': user.last_name or '',
                                'last_login': user.last_login
                            }
                            self._create_knock_customer_for_new_user(user, user_info_from_django)

                return user
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            raise AuthenticationFailed("Token has expired!")
        except jwt.DecodeError as e:
            logger.error(f"JWT decode error: {e}")
            raise AuthenticationFailed("Token decode error!")
        except jwt.InvalidSignatureError as e:
            logger.error(f"JWT signature verification failed: {e}")
            raise AuthenticationFailed("Invalid token signature!")
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT token validation failed: {e}")
            raise AuthenticationFailed("Invalid token!")
        except Exception as e:
            logger.exception(f"Unexpected JWT decode error: {e}")
            raise AuthenticationFailed("Unexpected Token decode error!")
        return None

    def _create_knock_customer_for_new_user(self, user, user_info: dict) -> bool:
        """
        Create a customer in Knock for a new user with email conflict handling.
        
        Args:
            user: The Django User instance
            user_info: Dict containing user information from Clerk
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use the new email conflict handling method
            return self.knock.create_customer_with_email_conflict_handling(user.id, user_info)
        except Exception as e:
            logger.error(f"Failed to create Knock customer for user {user.id}: {str(e)}")
            return False

    def _remove_waitlist_entry(self, email: str) -> bool:
        """
        Remove waitlist entry for a user when they create an account.
        
        Args:
            email: The email address to remove from waitlist
            
        Returns:
            bool: True if successfully removed or not found, False if error occurred
        """
        try:
            waitlist_entry = Waitlist.objects.filter(email=email).first()
            if waitlist_entry:
                waitlist_entry.delete()
                logger.info(f"Removed waitlist entry for email: {email}")
                return True
            else:
                logger.debug(f"No waitlist entry found for email: {email}")
                return True  # Not an error if the entry doesn't exist
        except Exception as e:
            logger.error(f"Failed to remove waitlist entry for email {email}: {str(e)}")
            return False
