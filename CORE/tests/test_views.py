import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from CORE.models import Waitlist, Skill

@pytest.mark.api
class TestWaitlistAPI:
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.mark.django_db
    def test_create_waitlist_entry(self, api_client):
        url = reverse('waitlist-crud')
        data = {
            "email": "test@example.com",
            "referrer": "website"
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == data['email']
        assert Waitlist.objects.count() == 1
        
    @pytest.mark.django_db
    def test_list_waitlist_entries(self, api_client):
        # First create some entries
        Waitlist.objects.create(email="test1@example.com", referrer="website")
        Waitlist.objects.create(email="test2@example.com", referrer="website")
        
        # Then get the list
        url = reverse('waitlist-crud')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]['email'] == "test1@example.com"
        assert response.data[1]['email'] == "test2@example.com"

@pytest.mark.api
class TestHealthCheckAPI:
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    def test_health_check(self, api_client):
        url = reverse('health-check')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'status' in response.data
        assert 'details' in response.data
        assert 'sentry' in response.data['details']
        assert 'clerk' in response.data['details']
        assert 'DB' in response.data['details']

@pytest.mark.api
class TestSkillAPI:
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.mark.django_db
    def test_list_skills(self, api_client):
        # Create some skills
        Skill.objects.create(name="Python", category="Programming")
        Skill.objects.create(name="JavaScript", category="Programming")
        
        # Get the list
        url = reverse('get-all-skill')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]['name'] == "Python"
        assert response.data[1]['name'] == "JavaScript" 