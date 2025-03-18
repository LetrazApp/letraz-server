import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
import mock_helpers
from PROFILE.models import User
from JOB.models import Job
from RESUME.models import Resume, ResumeSection, Education, Experience
from CORE.models import Country, Skill, Waitlist

@pytest.mark.integration
class TestCompleteWorkflows:
    @pytest.fixture
    def authenticated_client(self, api_client, user):
        """Returns an authenticated API client"""
        with patch('letraz_server.contrib.middlewares.clerk_middlewares.ClerkAuthenticationMiddleware.authenticate') as mock_auth:
            mock_auth.return_value = (user, None)
            api_client.credentials(HTTP_AUTHORIZATION='Bearer mock-token')
            return api_client
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.mark.django_db
    def test_create_profile_and_complete_resume(self, authenticated_client, user, country):
        """
        Test a complete user workflow:
        1. Update user profile
        2. Create a job
        3. Create a resume for the job
        4. Add education to the resume
        5. Add experience to the resume
        6. Add skills to the resume
        """
        # 1. Update user profile
        user_url = reverse('user-profile')
        user_data = {
            'first_name': 'Updated',
            'last_name': 'User',
            'profile_text': 'Experienced software engineer',
            'country': country.code,
            'city': 'New York',
            'website': 'https://example.com'
        }
        response = authenticated_client.patch(user_url, user_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        user_id = response.data['id']
        
        # 2. Create a job
        job_data = {
            'title': 'Senior Python Developer',
            'company_name': 'Tech Corporation',
            'location': 'Remote',
            'description': 'A senior Python developer position',
            'requirements': ['Python', 'Django', 'AWS'],
            'responsibilities': ['Develop web applications', 'Code reviews'],
            'benefits': ['Remote work', 'Health insurance']
        }
        # Directly create the job in the database
        job = Job.objects.create(**job_data)
        
        # 3. Create a resume for the job
        resume_url = reverse('resume-list')
        resume_data = {
            'user': user_id,
            'job': job.id,
            'version': 1
        }
        response = authenticated_client.post(resume_url, resume_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        resume_id = response.data['id']
        
        # 4. Add education to the resume
        # First create an education section
        resume = Resume.objects.get(id=resume_id)
        edu_section = resume.create_section(ResumeSection.ResumeSectionType.Education)
        
        education_url = reverse('education-list', kwargs={'resume_id': resume_id})
        education_data = {
            'user': user_id,
            'resume_section': str(edu_section.id),
            'institution_name': 'Test University',
            'field_of_study': 'Computer Science',
            'degree': 'Bachelor',
            'country': country.code,
            'started_from_year': 2015,
            'finished_at_year': 2019
        }
        response = authenticated_client.post(education_url, education_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # 5. Add experience to the resume
        # First create an experience section
        exp_section = resume.create_section(ResumeSection.ResumeSectionType.Experience)
        
        experience_url = reverse('experience-list', kwargs={'resume_id': resume_id})
        experience_data = {
            'user': user_id,
            'resume_section': str(exp_section.id),
            'title': 'Software Engineer',
            'company_name': 'Previous Tech',
            'employment_type': Experience.EmploymentType.FULL_TIME,
            'location': 'San Francisco',
            'country': country.code,
            'started_from_year': 2019,
            'finished_at_year': 2022,
            'description': 'Developed web applications using Python and Django'
        }
        response = authenticated_client.post(experience_url, experience_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # 6. Add skills to the resume
        # Use the add_skill method to add skills
        skill1 = resume.add_skill("Python", "Programming", "EXPERT")
        skill2 = resume.add_skill("Django", "Framework", "ADVANCED")
        skill3 = resume.add_skill("AWS", "Cloud", "INTERMEDIATE")
        
        # Verify the complete resume has all the components
        response = authenticated_client.get(reverse('resume-detail', kwargs={'pk': resume_id}))
        assert response.status_code == status.HTTP_200_OK
        
        # Verify education was added
        response = authenticated_client.get(education_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['institution_name'] == 'Test University'
        
        # Verify experience was added
        response = authenticated_client.get(experience_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['title'] == 'Software Engineer'
        
        # Verify the skills were added (would be a different endpoint in a real integration test)
        skill_section = resume.get_skill_resume_section()
        assert skill_section.proficiency_set.count() == 3
    
    @pytest.mark.django_db
    def test_joining_waitlist_to_profile_creation(self, api_client):
        """
        Test a user's journey from waitlist to profile creation:
        1. Join the waitlist
        2. Create a user profile (simulating authentication)
        3. Get user profile
        """
        # 1. Join the waitlist
        waitlist_url = reverse('waitlist-crud')
        waitlist_data = {
            'email': 'newuser@example.com',
            'referrer': 'twitter'
        }
        response = api_client.post(waitlist_url, waitlist_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'newuser@example.com'
        
        # 2. Create a user profile (simulating user creation after authentication)
        user = User.objects.create(
            id='user_waitlist123',
            email='newuser@example.com',
            first_name='New',
            last_name='User'
        )
        
        # Mock authentication for this user
        with patch('letraz_server.contrib.middlewares.clerk_middlewares.ClerkAuthenticationMiddleware.authenticate') as mock_auth:
            mock_auth.return_value = (user, None)
            api_client.credentials(HTTP_AUTHORIZATION='Bearer mock-token')
            
            # 3. Get user profile
            user_url = reverse('user-profile')
            response = api_client.get(user_url)
            assert response.status_code == status.HTTP_200_OK
            assert response.data['email'] == 'newuser@example.com'
            assert response.data['first_name'] == 'New' 