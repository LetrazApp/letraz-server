import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from PROFILE.models import User
import mock_helpers

@pytest.mark.api
class TestUserProfileAPI:
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def authenticated_client(self, api_client, user):
        """Returns an authenticated API client"""
        # Mock the authentication middleware to return our test user
        with patch('letraz_server.contrib.middlewares.clerk_middlewares.ClerkAuthenticationMiddleware.authenticate') as mock_auth:
            mock_auth.return_value = (user, None)
            api_client.credentials(HTTP_AUTHORIZATION='Bearer mock-token')
            return api_client
    
    @pytest.mark.django_db
    def test_get_current_user_profile_unauthenticated(self, api_client):
        """Test that unauthenticated requests cannot access user profile"""
        url = reverse('user-profile')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.django_db
    def test_get_current_user_profile(self, authenticated_client, user):
        """Test getting the current user's profile when authenticated"""
        url = reverse('user-profile')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == user.id
        assert response.data['email'] == user.email
        assert response.data['first_name'] == user.first_name
        
    @pytest.mark.django_db
    def test_update_current_user_profile(self, authenticated_client, user):
        """Test updating the current user's profile"""
        url = reverse('user-profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'profile_text': 'This is an updated profile text'
        }
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'
        assert response.data['last_name'] == 'Name'
        assert response.data['profile_text'] == 'This is an updated profile text'
        
        # Verify the changes were saved to the database
        user.refresh_from_db()
        assert user.first_name == 'Updated'
        assert user.last_name == 'Name'
        assert user.profile_text == 'This is an updated profile text' 