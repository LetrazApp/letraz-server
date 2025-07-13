import logging
from functools import wraps
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.{__name__}'
logger = logging.getLogger(__module_name)


def admin_api_key_required(view_func):
    """
    Decorator to require admin API key authentication for admin endpoints.
    
    Checks for 'x-admin-api-key' header and validates it against ADMIN_API_KEY setting.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if admin API key is configured
        if not settings.ADMIN_API_KEY:
            error_response = ErrorResponse(
                code=ErrorCode.UNAUTHORIZED,
                message='Admin API key not configured on server',
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            logger.error(f'UUID -> {error_response.uuid} | Admin API key not configured')
            return error_response.response
        
        # Get the API key from header
        api_key = request.headers.get('x-admin-api-key')
        
        if not api_key:
            error_response = ErrorResponse(
                code=ErrorCode.UNAUTHORIZED,
                message='Admin API key required. Please provide x-admin-api-key header.',
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            logger.warning(f'UUID -> {error_response.uuid} | Admin API key missing from request')
            return error_response.response
        
        # Validate the API key
        if api_key != settings.ADMIN_API_KEY:
            error_response = ErrorResponse(
                code=ErrorCode.UNAUTHORIZED,
                message='Invalid admin API key',
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            logger.warning(f'UUID -> {error_response.uuid} | Invalid admin API key provided')
            return error_response.response
        
        # API key is valid, proceed with the view
        logger.info(f'Admin API access granted for endpoint: {request.path}')
        return view_func(request, *args, **kwargs)
    
    return wrapper


class AdminAPIKeyAuthentication:
    """
    Authentication class for admin API key validation.
    Can be used as a class-based view mixin or standalone.
    """
    
    def authenticate_admin_api_key(self, request):
        """
        Authenticate admin API key from request headers.
        
        Returns:
            tuple: (is_valid, error_response) where is_valid is boolean
                   and error_response is Response object if invalid
        """
        # Check if admin API key is configured
        if not settings.ADMIN_API_KEY:
            error_response = ErrorResponse(
                code=ErrorCode.UNAUTHORIZED,
                message='Admin API key not configured on server',
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            logger.error(f'UUID -> {error_response.uuid} | Admin API key not configured')
            return False, error_response.response
        
        # Get the API key from header
        api_key = request.headers.get('x-admin-api-key')
        
        if not api_key:
            error_response = ErrorResponse(
                code=ErrorCode.UNAUTHORIZED,
                message='Admin API key required. Please provide x-admin-api-key header.',
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            logger.warning(f'UUID -> {error_response.uuid} | Admin API key missing from request')
            return False, error_response.response
        
        # Validate the API key
        if api_key != settings.ADMIN_API_KEY:
            error_response = ErrorResponse(
                code=ErrorCode.UNAUTHORIZED,
                message='Invalid admin API key',
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            logger.warning(f'UUID -> {error_response.uuid} | Invalid admin API key provided')
            return False, error_response.response
        
        # API key is valid
        logger.info(f'Admin API access granted for endpoint: {request.path}')
        return True, None 