import pytest
from JOB.models import Job

@pytest.mark.model
class TestJobModel:
    @pytest.mark.django_db
    def test_create_job(self):
        """Test creating a job with minimal required fields"""
        job = Job.objects.create(
            title="Software Engineer",
            company_name="Test Company"
        )
        assert job.title == "Software Engineer"
        assert job.company_name == "Test Company"
        assert job.id.startswith("job_")  # Job ID should start with 'job_'
    
    @pytest.mark.django_db
    def test_create_job_with_all_fields(self):
        """Test creating a job with all fields"""
        requirements = ["Python", "Django", "PostgreSQL"]
        responsibilities = ["Develop web applications", "Code reviews"]
        benefits = ["Remote work", "Health insurance"]
        
        job = Job.objects.create(
            title="Senior Backend Developer",
            company_name="Tech Corp",
            location="Remote",
            currency="USD",
            salary_min=80000,
            salary_max=120000,
            requirements=requirements,
            description="A great job opportunity",
            responsibilities=responsibilities,
            benefits=benefits,
            job_url="https://example.com/jobs/123"
        )
        
        assert job.title == "Senior Backend Developer"
        assert job.company_name == "Tech Corp"
        assert job.location == "Remote"
        assert job.currency == "USD"
        assert job.salary_min == 80000
        assert job.salary_max == 120000
        assert job.requirements == requirements
        assert job.description == "A great job opportunity"
        assert job.responsibilities == responsibilities
        assert job.benefits == benefits
        assert job.job_url == "https://example.com/jobs/123" 