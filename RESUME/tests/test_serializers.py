import pytest
from RESUME.serializers import ResumeSerializer, EducationSerializer, ExperienceSerializer, ProficiencySerializer
from RESUME.models import Resume, ResumeSection, Education, Experience, Proficiency
from CORE.models import Skill

@pytest.mark.serializer
class TestResumeSerializer:
    @pytest.mark.django_db
    def test_serialize_resume(self, resume):
        """Test serializing a resume object"""
        serializer = ResumeSerializer(resume)
        data = serializer.data
        
        assert data['id'] == resume.id
        assert data['user'] == resume.user.id
        assert data['job'] == resume.job.id
        assert data['version'] == resume.version
        assert not data['base']  # Default value
    
    @pytest.mark.django_db
    def test_deserialize_valid_resume_data(self, user, job):
        """Test deserializing valid resume data"""
        data = {
            'user': user.id,
            'job': job.id,
            'version': 1,
            'base': False
        }
        
        serializer = ResumeSerializer(data=data)
        assert serializer.is_valid()
        
        resume = serializer.save()
        assert resume.user == user
        assert resume.job == job
        assert resume.version == 1
        assert not resume.base
    
    @pytest.mark.django_db
    def test_deserialize_invalid_resume_data(self):
        """Test deserializing invalid resume data"""
        # Missing required fields
        data = {
            'version': 1,
            'base': False
        }
        
        serializer = ResumeSerializer(data=data)
        assert not serializer.is_valid()
        assert 'user' in serializer.errors  # Missing required field

@pytest.mark.serializer
class TestEducationSerializer:
    @pytest.mark.django_db
    def test_serialize_education(self, user, resume, country):
        """Test serializing an education object"""
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
        
        serializer = EducationSerializer(education)
        data = serializer.data
        
        assert data['id'] == str(education.id)
        assert data['institution_name'] == education.institution_name
        assert data['field_of_study'] == education.field_of_study
        assert data['degree'] == education.degree
        assert data['country'] == education.country.code
        assert data['started_from_year'] == education.started_from_year
        assert data['finished_at_year'] == education.finished_at_year
        assert not data['current']
    
    @pytest.mark.django_db
    def test_deserialize_valid_education_data(self, user, resume_section, country):
        """Test deserializing valid education data"""
        data = {
            'user': user.id,
            'resume_section': str(resume_section.id),
            'institution_name': 'Test University',
            'field_of_study': 'Computer Science',
            'degree': 'Bachelor',
            'country': country.code,
            'started_from_year': 2018,
            'finished_at_year': 2022,
            'current': False
        }
        
        serializer = EducationSerializer(data=data)
        assert serializer.is_valid()
        
        education = serializer.save()
        assert education.user == user
        assert education.resume_section == resume_section
        assert education.institution_name == 'Test University'
        assert education.field_of_study == 'Computer Science'
        assert education.degree == 'Bachelor'
        assert education.country == country
        assert education.started_from_year == 2018
        assert education.finished_at_year == 2022
        assert not education.current

@pytest.mark.serializer
class TestExperienceSerializer:
    @pytest.mark.django_db
    def test_serialize_experience(self, user, resume, country):
        """Test serializing an experience object"""
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
        
        serializer = ExperienceSerializer(experience)
        data = serializer.data
        
        assert data['id'] == str(experience.id)
        assert data['title'] == experience.title
        assert data['company_name'] == experience.company_name
        assert data['employment_type'] == experience.employment_type
        assert data['location'] == experience.location
        assert data['country'] == experience.country.code
        assert data['started_from_year'] == experience.started_from_year
        assert data['current'] == experience.current
    
    @pytest.mark.django_db
    def test_deserialize_valid_experience_data(self, user, resume, country):
        """Test deserializing valid experience data"""
        section = resume.create_section(ResumeSection.ResumeSectionType.Experience)
        
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
        
        serializer = ExperienceSerializer(data=data)
        assert serializer.is_valid()
        
        experience = serializer.save()
        assert experience.user == user
        assert experience.resume_section == section
        assert experience.title == 'Software Engineer'
        assert experience.company_name == 'Test Company'
        assert experience.employment_type == Experience.EmploymentType.FULL_TIME
        assert experience.location == 'Test City'
        assert experience.country == country
        assert experience.started_from_year == 2020
        assert experience.current 