import pytest
import jwt
from rest_framework.exceptions import AuthenticationFailed
from unittest.mock import patch, MagicMock
from django.http import HttpRequest
import mock_helpers
from letraz_server.contrib.middlewares.clerk_middlewares import ClerkAuthenticationMiddleware
from PROFILE.models import User

@pytest.mark.middleware
class TestClerkMiddleware:
    @pytest.fixture
    def middleware(self):
        return ClerkAuthenticationMiddleware()
    
    @pytest.fixture
    def mock_request(self):
        request = MagicMock(spec=HttpRequest)
        request.COOKIES = {}
        request.headers = {}
        return request
    
    def test_no_auth_token(self, middleware, mock_request):
        """Test authentication with no token"""
        user, auth = middleware.authenticate(mock_request)
        assert user is None
        assert auth is None
    
    @pytest.mark.django_db
    @patch('letraz_server.contrib.sdks.clerk.ClerkSDK')
    def test_auth_with_session_cookie(self, mock_clerk_sdk, middleware, mock_request):
        """Test authentication with session cookie"""
        # Create a mock SDK
        mock_sdk_instance = mock_clerk_sdk.return_value
        mock_sdk_instance.get_jwks.return_value = mock_helpers.mock_clerk_jwks()
        mock_sdk_instance.fetch_user_info.return_value = (True, {
            "email_address": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "last_login": "2023-01-01T00:00:00Z"
        })
        
        # Set the cookie
        mock_request.COOKIES = {'__session': 'test_token'}
        
        # Mock jwt decode to return a valid payload
        with patch('jwt.decode') as mock_decode:
            mock_decode.return_value = {'sub': 'user_test123'}
            
            # Test authentication
            user, auth = middleware.authenticate(mock_request)
            
            assert user is not None
            assert isinstance(user, User)
            assert user.id == 'user_test123'
            assert user.email == 'test@example.com'
            assert user.first_name == 'Test'
            assert user.last_name == 'User'
    
    @pytest.mark.django_db
    @patch('letraz_server.contrib.sdks.clerk.ClerkSDK')
    def test_auth_with_bearer_token(self, mock_clerk_sdk, middleware, mock_request):
        """Test authentication with bearer token"""
        # Create a mock SDK
        mock_sdk_instance = mock_clerk_sdk.return_value
        mock_sdk_instance.get_jwks.return_value = mock_helpers.mock_clerk_jwks()
        mock_sdk_instance.fetch_user_info.return_value = (True, {
            "email_address": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "last_login": "2023-01-01T00:00:00Z"
        })
        
        # Set the authorization header
        mock_request.headers = {'Authorization': 'Bearer test_token'}
        
        # Mock jwt decode to return a valid payload
        with patch('jwt.decode') as mock_decode:
            mock_decode.return_value = {'sub': 'user_test123'}
            
            # Test authentication
            user, auth = middleware.authenticate(mock_request)
            
            assert user is not None
            assert isinstance(user, User)
            assert user.id == 'user_test123'
    
    @pytest.mark.django_db
    @patch('letraz_server.contrib.sdks.clerk.ClerkSDK')
    def test_auth_with_invalid_token(self, mock_clerk_sdk, middleware, mock_request):
        """Test authentication with invalid token"""
        # Create a mock SDK
        mock_sdk_instance = mock_clerk_sdk.return_value
        mock_sdk_instance.get_jwks.return_value = mock_helpers.mock_clerk_jwks()
        
        # Set the authorization header
        mock_request.headers = {'Authorization': 'Bearer invalid_token'}
        
        # Mock jwt decode to raise an exception
        with patch('jwt.decode') as mock_decode:
            mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")
            
            # Test authentication
            with pytest.raises(AuthenticationFailed):
                middleware.authenticate(mock_request)
    
    @pytest.mark.django_db
    @patch('letraz_server.contrib.sdks.clerk.ClerkSDK')
    def test_auth_with_expired_token(self, mock_clerk_sdk, middleware, mock_request):
        """Test authentication with expired token"""
        # Create a mock SDK
        mock_sdk_instance = mock_clerk_sdk.return_value
        mock_sdk_instance.get_jwks.return_value = mock_helpers.mock_clerk_jwks()
        
        # Set the authorization header
        mock_request.headers = {'Authorization': 'Bearer expired_token'}
        
        # Mock jwt decode to raise an exception
        with patch('jwt.decode') as mock_decode:
            mock_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")
            
            # Test authentication
            with pytest.raises(AuthenticationFailed):
                middleware.authenticate(mock_request)
    
    @pytest.mark.django_db
    @patch('letraz_server.contrib.sdks.clerk.ClerkSDK')
    def test_auth_with_invalid_jwks(self, mock_clerk_sdk, middleware, mock_request):
        """Test authentication with invalid JWKS"""
        # Create a mock SDK
        mock_sdk_instance = mock_clerk_sdk.return_value
        mock_sdk_instance.get_jwks.return_value = {'keys': []}  # Empty keys array
        
        # Set the authorization header
        mock_request.headers = {'Authorization': 'Bearer test_token'}
        
        # Test authentication
        with pytest.raises(AuthenticationFailed):
            middleware.authenticate(mock_request) 