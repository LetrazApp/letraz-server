import pytest
from django.db import IntegrityError
from RESUME.models import Resume, ResumeSection, Education, Experience, Proficiency
from PROFILE.models import User
from CORE.models import Skill, Country
from JOB.models import Job

@pytest.mark.model
class TestResumeModel:
    @pytest.mark.django_db
    def test_create_resume(self, user, job):
        """Test creating a resume with minimal required fields"""
        resume = Resume.objects.create(
            user=user,
            job=job,
            version=1
        )
        assert resume.user == user
        assert resume.job == job
        assert resume.version == 1
        assert resume.base is False  # Default value
        assert resume.id.startswith("rsm_")  # Resume ID should start with 'rsm_'
    
    @pytest.mark.django_db
    def test_create_base_resume(self, user):
        """Test creating a base resume"""
        resume = Resume.objects.create(
            user=user,
            base=True,
            version=1
        )
        assert resume.user == user
        assert resume.job is None
        assert resume.base is True
        assert resume.version == 1

    @pytest.mark.django_db
    def test_unique_base_resume_constraint(self, user):
        """Test that a user can only have one base resume"""
        Resume.objects.create(
            user=user,
            base=True,
            version=1
        )
        
        # Trying to create another base resume for the same user should fail
        with pytest.raises(IntegrityError):
            Resume.objects.create(
                user=user,
                base=True,
                version=2
            )
    
    @pytest.mark.django_db
    def test_unique_job_resume_constraint(self, user, job):
        """Test that a user can only have one resume per job"""
        Resume.objects.create(
            user=user,
            job=job,
            version=1
        )
        
        # Trying to create another resume for the same user and job should fail
        with pytest.raises(IntegrityError):
            Resume.objects.create(
                user=user,
                job=job,
                version=2
            )
    
    @pytest.mark.django_db
    def test_create_section(self, resume):
        """Test creating a resume section"""
        section = resume.create_section(ResumeSection.ResumeSectionType.Education)
        assert section.resume == resume
        assert section.type == ResumeSection.ResumeSectionType.Education
        assert section.index == 0  # First section should have index 0
        
        # Create another section
        section2 = resume.create_section(ResumeSection.ResumeSectionType.Experience)
        assert section2.resume == resume
        assert section2.type == ResumeSection.ResumeSectionType.Experience
        assert section2.index == 1  # Second section should have index 1
    
    @pytest.mark.django_db
    def test_add_skill(self, resume, skill):
        """Test adding a skill to a resume"""
        # Add a new skill
        proficiency = resume.add_skill("Python", "Programming", "EXPERT")
        assert proficiency.skill.name == "Python"
        assert proficiency.skill.category == "Programming"
        assert proficiency.level == "EXPERT"
        
        # Add an existing skill
        proficiency = resume.add_skill(skill.name, skill.category)
        assert proficiency.skill.name == skill.name
        assert proficiency.skill.category == skill.category
        assert proficiency.level is None  # Default value

@pytest.mark.model
class TestResumeSectionModel:
    @pytest.mark.django_db
    def test_create_resume_section(self, resume):
        """Test creating a resume section"""
        section = ResumeSection.objects.create(
            resume=resume,
            index=0,
            type=ResumeSection.ResumeSectionType.Education
        )
        assert section.resume == resume
        assert section.index == 0
        assert section.type == ResumeSection.ResumeSectionType.Education
    
    @pytest.mark.django_db
    def test_unique_index_constraint(self, resume):
        """Test that a resume can't have two sections with the same index"""
        ResumeSection.objects.create(
            resume=resume,
            index=0,
            type=ResumeSection.ResumeSectionType.Education
        )
        
        # Trying to create another section with the same index should fail
        with pytest.raises(IntegrityError):
            ResumeSection.objects.create(
                resume=resume,
                index=0,
                type=ResumeSection.ResumeSectionType.Experience
            )

@pytest.mark.model
class TestEducationModel:
    @pytest.mark.django_db
    def test_create_education(self, user, resume, country):
        """Test creating an education entry"""
        section = resume.create_section(ResumeSection.ResumeSectionType.Education)
        education = Education.objects.create(
            user=user,
            resume_section=section,
            institution_name="Test University",
            field_of_study="Computer Science",
            degree="Bachelor",
            country=country,
            started_from_year=2018,
            finished_at_year=2022
        )
        
        assert education.user == user
        assert education.resume_section == section
        assert education.institution_name == "Test University"
        assert education.field_of_study == "Computer Science"
        assert education.degree == "Bachelor"
        assert education.country == country
        assert education.started_from_year == 2018
        assert education.finished_at_year == 2022
        assert education.current is False  # Default value

@pytest.mark.model
class TestExperienceModel:
    @pytest.mark.django_db
    def test_create_experience(self, user, resume, country):
        """Test creating an experience entry"""
        section = resume.create_section(ResumeSection.ResumeSectionType.Experience)
        experience = Experience.objects.create(
            user=user,
            resume_section=section,
            title="Software Engineer",
            company_name="Test Company",
            employment_type=Experience.EmploymentType.FULL_TIME,
            location="Test City",
            country=country,
            started_from_year=2020,
            current=True
        )
        
        assert experience.user == user
        assert experience.resume_section == section
        assert experience.title == "Software Engineer"
        assert experience.company_name == "Test Company"
        assert experience.employment_type == Experience.EmploymentType.FULL_TIME
        assert experience.location == "Test City"
        assert experience.country == country
        assert experience.started_from_year == 2020
        assert experience.current is True 