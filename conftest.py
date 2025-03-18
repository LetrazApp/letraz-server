import pytest
from django.contrib.auth import get_user_model
from CORE.models import Waitlist, Skill, Country
from JOB.models import Job
from RESUME.models import Resume, ResumeSection

User = get_user_model()

@pytest.fixture
def user():
    return User.objects.create(
        id="user_testid123",
        email="test@example.com",
        first_name="Test",
        last_name="User"
    )

@pytest.fixture
def country():
    return Country.objects.create(
        code="USA",
        name="United States of America"
    )

@pytest.fixture
def job():
    return Job.objects.create(
        title="Software Engineer",
        company_name="Test Company",
        description="Test job description"
    )

@pytest.fixture
def skill():
    return Skill.objects.create(
        name="Python",
        category="Programming"
    )

@pytest.fixture
def resume(user, job):
    return Resume.objects.create(
        user=user,
        job=job,
        version=1
    )

@pytest.fixture
def resume_section(resume):
    return ResumeSection.objects.create(
        resume=resume,
        index=0,
        type="EDUCATION"
    ) 