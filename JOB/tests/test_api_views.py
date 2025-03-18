import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
import mock_helpers
from JOB.models import Job

@pytest.mark.api
class TestJobAPI:
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def authenticated_client(self, api_client, user):
        """Returns an authenticated API client"""
        with patch('letraz_server.contrib.middlewares.clerk_middlewares.ClerkAuthenticationMiddleware.authenticate') as mock_auth:
            mock_auth.return_value = (user, None)
            api_client.credentials(HTTP_AUTHORIZATION='Bearer mock-token')
            return api_client
    
    @pytest.mark.django_db
    def test_get_job_by_id(self, api_client, job):
        """Test getting a job by its ID"""
        url = reverse('job-detail', kwargs={'job_id': job.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == job.id
        assert response.data['title'] == job.title
        assert response.data['company_name'] == job.company_name
    
    @pytest.mark.django_db
    def test_get_nonexistent_job(self, api_client):
        """Test getting a job that doesn't exist"""
        url = reverse('job-detail', kwargs={'job_id': 'job_nonexistent'})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.django_db
    def test_update_job_unauthenticated(self, api_client, job):
        """Test that unauthenticated users cannot update jobs"""
        url = reverse('job-detail', kwargs={'job_id': job.id})
        data = {
            'title': 'Updated Title',
            'description': 'Updated description'
        }
        
        response = api_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Verify the job wasn't changed
        job.refresh_from_db()
        assert job.title != 'Updated Title'
    
    @pytest.mark.django_db
    def test_update_job_authenticated(self, authenticated_client, job):
        """Test that authenticated users can update jobs"""
        url = reverse('job-detail', kwargs={'job_id': job.id})
        data = {
            'title': 'Updated Title',
            'description': 'Updated description'
        }
        
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Title'
        assert response.data['description'] == 'Updated description'
        
        # Verify the changes were saved to the database
        job.refresh_from_db()
        assert job.title == 'Updated Title'
        assert job.description == 'Updated description' 