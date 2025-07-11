from rest_framework import serializers
from CORE.serializers import CountrySerializer, SkillSerializer
from JOB.serializers import JobShortSerializer, JobFullSerializer
from PROFILE.serializers import UserSerializer
from RESUME.models import Resume, ResumeSection, Education, Experience, Proficiency, Project, Certification


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
        return UserSerializer(resume.user).data

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
            try:
                return EducationFullSerializer(resume_section.education).data
            except Education.DoesNotExist:
                resume_section.delete()
                return None
        elif resume_section.type == ResumeSection.ResumeSectionType.Experience:
            try:
                return ExperienceFullSerializer(resume_section.experience).data
            except Experience.DoesNotExist:
                resume_section.delete()
                return None
        elif resume_section.type == ResumeSection.ResumeSectionType.Project:
            try:
                return ProjectSerializer(resume_section.project).data
            except Project.DoesNotExist:
                resume_section.delete()
                return None
        elif resume_section.type == ResumeSection.ResumeSectionType.Certification:
            try:
                return CertificationSerializer(resume_section.certification).data
            except Certification.DoesNotExist:
                resume_section.delete()
                return None
        elif resume_section.type == ResumeSection.ResumeSectionType.Skill:
            if resume_section.proficiency_set.count() == 0:
                resume_section.delete()
                return None
            else:
                return ProficiencySerializer(resume_section.proficiency_set.all(), many=True).data
        else:
            return None


class ResumeSectionShortSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = ResumeSection
        fields = ('id', 'resume', 'index', 'type')
        read_only_fields = ['id']

    @staticmethod
    def get_type(resume_section: ResumeSection):
        return resume_section.get_type_display()


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


class ProficiencySerializer(serializers.ModelSerializer):
    skill = SkillSerializer()

    class Meta:
        model = Proficiency
        fields = ('id', 'skill', 'resume_section', 'level')


class ResumeSkillUpsertSerializer(serializers.Serializer):
    LEVEL_CHOICES = [
        ('OPERATIONAL', 'OPERATIONAL'),
        ('DEGRADED', 'DEGRADED')
    ]
    name = serializers.CharField(help_text='The name of the skill.')
    category = serializers.CharField(help_text='The category of the skill.')
    level = serializers.ChoiceField(Proficiency.Level.choices, help_text='The proficiency level of the skill.')


class ProjectSerializer(serializers.ModelSerializer):
    skills_used = SkillSerializer(many=True)
    resume_section = ResumeSectionShortSerializer()

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class SkillUpsertSerializer(serializers.Serializer):
    name = serializers.CharField(help_text='The name of the skill.')
    category = serializers.CharField(help_text='The category of the skill.')


class ProjectUpsertSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = '__all__'

class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = '__all__'


class CertificationUpsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = '__all__'


class SectionRearrangeSerializer(serializers.Serializer):
    """
    Serializer for rearranging resume sections.
    Accepts an array of section IDs representing the desired order.
    """
    section_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="Array of section IDs in the desired order"
    )

    def validate_section_ids(self, value):
        """
        Validate that there are no duplicate section IDs.
        """
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate section IDs are not allowed.")
        return value
