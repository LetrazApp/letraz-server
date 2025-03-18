import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
import mock_helpers
from RESUME.models import Resume, ResumeSection, Education, Experience

@pytest.mark.api
class TestResumeViewSet:
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
    def test_list_resumes_unauthenticated(self, api_client):
        """Test listing resumes without authentication"""
        url = reverse('resume-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.django_db
    def test_list_resumes_authenticated(self, authenticated_client, user, job):
        """Test listing resumes with authentication"""
        # Create resumes for the user
        Resume.objects.create(user=user, job=job, version=1)
        Resume.objects.create(user=user, base=True, version=1)
        
        url = reverse('resume-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    @pytest.mark.django_db
    def test_create_resume_authenticated(self, authenticated_client, user, job):
        """Test creating a resume with authentication"""
        url = reverse('resume-list')
        data = {
            'user': user.id,
            'job': job.id,
            'version': 1,
            'base': False
        }
        
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user'] == user.id
        assert response.data['job'] == job.id
        assert response.data['version'] == 1
        assert not response.data['base']
        
        # Verify the resume was created
        assert Resume.objects.count() == 1
    
    @pytest.mark.django_db
    def test_get_resume_detail(self, authenticated_client, resume):
        """Test getting resume details"""
        url = reverse('resume-detail', kwargs={'pk': resume.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == resume.id
        assert response.data['user'] == resume.user.id
        assert response.data['job'] == resume.job.id
        assert response.data['version'] == resume.version

@pytest.mark.api
class TestEducationViewSet:
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
    def test_list_education_entries(self, authenticated_client, user, resume, country):
        """Test listing education entries for a resume"""
        # Create an education section and entry
        section = resume.create_section(ResumeSection.ResumeSectionType.Education)
        Education.objects.create(
            user=user,
            resume_section=section,
            institution_name="Test University",
            field_of_study="Computer Science",
            country=country
        )
        
        url = reverse('education-list', kwargs={'resume_id': resume.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['institution_name'] == "Test University"
        assert response.data[0]['field_of_study'] == "Computer Science"
    
    @pytest.mark.django_db
    def test_create_education_entry(self, authenticated_client, user, resume, country):
        """Test creating an education entry for a resume"""
        # Create an education section
        section = resume.create_section(ResumeSection.ResumeSectionType.Education)
        
        url = reverse('education-list', kwargs={'resume_id': resume.id})
        data = {
            'user': user.id,
            'resume_section': str(section.id),
            'institution_name': 'Test University',
            'field_of_study': 'Computer Science',
            'degree': 'Bachelor',
            'country': country.code,
            'started_from_year': 2018,
            'finished_at_year': 2022
        }
        
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['institution_name'] == 'Test University'
        assert response.data['field_of_study'] == 'Computer Science'
        assert response.data['degree'] == 'Bachelor'
        assert response.data['country'] == country.code
        
        # Verify the education entry was created
        assert Education.objects.count() == 1

@pytest.mark.api
class TestExperienceViewSet:
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
    def test_list_experience_entries(self, authenticated_client, user, resume, country):
        """Test listing experience entries for a resume"""
        # Create an experience section and entry
        section = resume.create_section(ResumeSection.ResumeSectionType.Experience)
        Experience.objects.create(
            user=user,
            resume_section=section,
            title="Software Engineer",
            company_name="Test Company",
            employment_type=Experience.EmploymentType.FULL_TIME,
            country=country
        )
        
        url = reverse('experience-list', kwargs={'resume_id': resume.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['title'] == "Software Engineer"
        assert response.data[0]['company_name'] == "Test Company"
        assert response.data[0]['employment_type'] == Experience.EmploymentType.FULL_TIME
    
    @pytest.mark.django_db
    def test_create_experience_entry(self, authenticated_client, user, resume, country):
        """Test creating an experience entry for a resume"""
        # Create an experience section
        section = resume.create_section(ResumeSection.ResumeSectionType.Experience)
        
        url = reverse('experience-list', kwargs={'resume_id': resume.id})
        data = {
            'user': user.id,
            'resume_section': str(section.id),
            'title': 'Software Engineer',
            'company_name': 'Test Company',
            'employment_type': Experience.EmploymentType.FULL_TIME,
            'location': 'Test City',
            'country': country.code,
            'started_from_year': 2020,
            'current': True
        }
        
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Software Engineer'
        assert response.data['company_name'] == 'Test Company'
        assert response.data['employment_type'] == Experience.EmploymentType.FULL_TIME
        
        # Verify the experience entry was created
        assert Experience.objects.count() == 1 