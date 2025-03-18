import time
import jwt
from unittest.mock import MagicMock

def mock_clerk_jwks():
    """Create a mock JWKS response"""
    return {
        "keys": [
            {
                "kty": "RSA",
                "e": "AQAB",
                "use": "sig",
                "kid": "test-key-id",
                "alg": "RS256",
                "n": "test-key-data"
            }
        ]
    }

def create_mock_jwt(user_id, expiry=None):
    """Create a mock JWT token for testing"""
    payload = {
        "sub": user_id,
        "exp": expiry or (int(time.time()) + 3600)
    }
    # Note: In real tests, we would use a proper RSA key
    return jwt.encode(payload, "test-secret", algorithm="HS256")

def mock_clerk_sdk():
    """Create a mock Clerk SDK instance"""
    mock = MagicMock()
    mock.get_jwks.return_value = mock_clerk_jwks()
    mock.fetch_user_info.return_value = (
        True, 
        {
            "email_address": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "last_login": "2023-01-01T00:00:00Z"
        }
    )
    return mock 