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
                "last_login": datetime.datetime.fromtimestamp(
                    data["last_sign_in_at"] / 1000, tz=pytz.timezone(settings.TIME_ZONE)
                ),
            }
        else:
            return False, {
                "email_address": "",
                "first_name": "",
                "last_name": "",
                "last_login": None
            }

    def get_jwks(self):
        jwks_data = cache.get(self.CACHE_KEY)
        if not jwks_data:
            response = requests.get(f'{self.FRONTEND_API_URL}/.well-known/jwks.json')
            if response.status_code == 200:
                jwks_data = response.json()
                logger.debug(f'JWKS Keys:  {jwks_data}')
                cache.set(self.CACHE_KEY, jwks_data)
            else:
                raise AuthenticationFailed('Failed to fetch JWKS!')
        return jwks_data
