from rest_framework import serializers

from CORE.serializers import CountrySerializer
from JOB.serializers import JobShortSerializer, JobFullSerializer
from PROFILE.serializers import UserInfoSerializer
from RESUME.models import Resume, ResumeSection, Education, Experience


class ResumeShortSerializer(serializers.ModelSerializer):
    job = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = ('id', 'base', 'user', 'job')
        read_only_fields = ['id']

    @staticmethod
    def get_job(obj: Resume):
        return JobShortSerializer(obj.job).data


class ResumeFullSerializer(serializers.ModelSerializer):
    job = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = ('id', 'base', 'user', 'job', 'sections')
        read_only_fields = ['id']

    @staticmethod
    def get_job(resume: Resume):
        return JobFullSerializer(resume.job).data

    @staticmethod
    def get_user(resume: Resume):
        return UserInfoSerializer(resume.user).data

    @staticmethod
    def get_sections(resume: Resume):
        return ResumeSectionFullSerializer(resume.resumesection_set.order_by('index'), many=True).data


class ResumeSectionFullSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    class Meta:
        model = ResumeSection
        fields = ('id', 'resume', 'index', 'type', 'data')
        read_only_fields = ['id']

    @staticmethod
    def get_type(resume_section: ResumeSection):
        return resume_section.get_type_display()

    @staticmethod
    def get_data(resume_section: ResumeSection):
        if resume_section.type == ResumeSection.ResumeSectionType.Education:
            return EducationFullSerializer(resume_section.education).data
        elif resume_section.type == ResumeSection.ResumeSectionType.Experience:
            return ExperienceFullSerializer(resume_section.experience).data
        else:
            return None


class EducationFullSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()

    class Meta:
        model = Education
        fields = (
            'id', 'user', 'resume_section', 'institution_name', 'field_of_study',
            'degree', 'country', 'started_from_month', 'started_from_year',
            'finished_at_month', 'finished_at_year', 'current', 'description',
            'created_at', 'updated_at'
        )
        read_only_fields = ['id', 'created_at', 'updated_at']

    @staticmethod
    def get_country(education: Education):
        return CountrySerializer(education.country).data if education.country else None


class EducationUpsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = "__all__"


class ExperienceFullSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()
    employment_type = serializers.SerializerMethodField()

    class Meta:
        model = Experience
        fields = (
            'id', 'user', 'resume_section', 'company_name', 'job_title', 'employment_type',
            'city', 'country', 'started_from_month', 'started_from_year', 'finished_at_month',
            'finished_at_year', 'current', 'description', 'created_at', 'updated_at'
        )
        read_only_fields = ['id', 'created_at', 'updated_at']

    @staticmethod
    def get_country(experience: Experience):
        return CountrySerializer(experience.country).data if experience.country else None

    @staticmethod
    def get_employment_type(experience: Experience):
        return experience.get_employment_type_display() if experience.employment_type else None


class ExperienceUpsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = '__all__'
