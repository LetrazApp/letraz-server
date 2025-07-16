import datetime
import json
import logging

import pytz
import requests
from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed
from letraz_server import settings
from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.{__name__}'
logger = logging.getLogger(__module_name)


class ClerkSDK:
    def __init__(self, frontend_api_url, secret_key):
        self.API_URL = "https://api.clerk.com/v1"
        self.FRONTEND_API_URL = frontend_api_url
        self.SECRET_KEY = secret_key
        self.CACHE_KEY = "jwks_data"

    def fetch_user_info(self, user_id: str):

        logger.debug(f'Data For user id: {user_id}')
        if not user_id:
            raise AuthenticationFailed('Invalid user!')
        response = requests.get(
            f"{self.API_URL}/users/{user_id}",
            headers={'Authorization': f'Bearer {self.SECRET_KEY}'}
        )
        logger.debug(f'User:  {json.dumps(response.json())}')
        if response.status_code == 200:
            data = response.json()
            return True, {
                "email_address": data["email_addresses"][0]["email_address"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "avatar_url": data.get("image_url", ""),
                "last_login": datetime.datetime.fromtimestamp(
                    data["last_sign_in_at"] / 1000, tz=pytz.timezone(settings.TIME_ZONE)
                ),
            }
        else:
            return False, {
                "email_address": "",
                "first_name": "",
                "last_name": "",
                "avatar_url": "",
                "last_login": None
            }

    def get_jwks(self):
        """Get JWKS from the configured frontend API URL"""
        return self._fetch_jwks(self.FRONTEND_API_URL)
    
    def get_jwks_from_issuer(self, issuer_url):
        """Get JWKS from the issuer URL (extracted from JWT token)"""
        return self._fetch_jwks(issuer_url)
    
    def _fetch_jwks(self, base_url):
        """Internal method to fetch JWKS from a given base URL"""
        # Create cache key based on the base URL
        cache_key = f"jwks_data_{base_url.replace('https://', '').replace('/', '_')}"
        
        jwks_data = cache.get(cache_key)
        if not jwks_data:
            jwks_url = f'{base_url}/.well-known/jwks.json'
            logger.info(f'Fetching JWKS from: {jwks_url}')
            
            try:
                response = requests.get(jwks_url, timeout=10)
                logger.info(f'JWKS response status: {response.status_code}')
                
                if response.status_code == 200:
                    jwks_data = response.json()
                    logger.debug(f'JWKS Keys: {jwks_data}')
                    # Add cache timeout to prevent indefinite caching
                    cache.set(cache_key, jwks_data, timeout=300)  # 5 minutes
                else:
                    logger.error(f'Failed to fetch JWKS. Status: {response.status_code}, Response: {response.text}')
                    raise AuthenticationFailed(f'Failed to fetch JWKS! Status: {response.status_code}')
            except requests.exceptions.RequestException as e:
                logger.error(f'Request error when fetching JWKS: {str(e)}')
                raise AuthenticationFailed(f'JWKS request failed: {str(e)}')
            except ValueError as e:
                logger.error(f'Invalid JSON response from JWKS endpoint: {str(e)}')
                raise AuthenticationFailed('Invalid JWKS response format')
            except Exception as e:
                logger.error(f'Unexpected error fetching JWKS: {str(e)}')
                raise AuthenticationFailed(f'Unexpected JWKS error: {str(e)}')
        
        return jwks_data
