import pytest
from JOB.serializers import JobSerializer
from JOB.models import Job

@pytest.mark.serializer
class TestJobSerializer:
    def test_valid_job_data(self):
        """Test that valid job data validates successfully"""
        data = {
            "title": "Software Engineer",
            "company_name": "Test Company",
            "location": "Remote",
            "description": "A test job description"
        }
        serializer = JobSerializer(data=data)
        assert serializer.is_valid()
    
    def test_minimal_valid_job_data(self):
        """Test that minimal valid job data validates successfully"""
        data = {
            "title": "Software Engineer",
            "company_name": "Test Company"
        }
        serializer = JobSerializer(data=data)
        assert serializer.is_valid()
    
    def test_invalid_job_data(self):
        """Test that invalid job data fails validation"""
        data = {
            "title": "",  # Empty title
            "company_name": "Test Company"
        }
        serializer = JobSerializer(data=data)
        assert not serializer.is_valid()
        assert "title" in serializer.errors
        
        data = {
            "title": "Software Engineer"
            # Missing required company_name
        }
        serializer = JobSerializer(data=data)
        assert not serializer.is_valid()
        assert "company_name" in serializer.errors
    
    @pytest.mark.django_db
    def test_create_job(self):
        """Test creating a job using the serializer"""
        data = {
            "title": "Software Engineer",
            "company_name": "Test Company",
            "location": "Remote",
            "description": "A test job description",
            "requirements": ["Python", "Django"],
            "responsibilities": ["Build web apps", "Write tests"],
            "benefits": ["Remote work", "Flexible hours"]
        }
        serializer = JobSerializer(data=data)
        assert serializer.is_valid()
        
        job = serializer.save()
        assert job.title == data["title"]
        assert job.company_name == data["company_name"]
        assert job.location == data["location"]
        assert job.description == data["description"]
        assert job.requirements == data["requirements"]
        assert job.responsibilities == data["responsibilities"]
        assert job.benefits == data["benefits"]
    
    @pytest.mark.django_db
    def test_update_job(self, job):
        """Test updating a job using the serializer"""
        data = {
            "title": "Updated Title",
            "description": "Updated description",
            "salary_min": 90000,
            "salary_max": 130000,
            "currency": "USD"
        }
        
        serializer = JobSerializer(job, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_job = serializer.save()
        assert updated_job.title == data["title"]
        assert updated_job.description == data["description"]
        assert updated_job.salary_min == data["salary_min"]
        assert updated_job.salary_max == data["salary_max"]
        assert updated_job.currency == data["currency"]
        assert updated_job.company_name == job.company_name  # Unchanged field 