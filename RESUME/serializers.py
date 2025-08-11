from rest_framework import serializers
from CORE.serializers import CountrySerializer, SkillSerializer
from JOB.serializers import JobShortSerializer, JobFullSerializer
from PROFILE.serializers import UserSerializer
from RESUME.models import Resume, ResumeSection, Education, Experience, Proficiency, Project, Certification


class ResumeShortSerializer(serializers.ModelSerializer):
    job = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = ('id', 'base', 'user', 'job', 'status', 'thumbnail')
        read_only_fields = ['id']

    @staticmethod
    def get_job(resume: Resume):
        return JobShortSerializer(resume.job).data

    @staticmethod
    def get_status(resume: Resume):
        return resume.get_status_display()

class BaseResumeFullSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = ('id', 'base', 'user', 'sections', 'thumbnail')
        read_only_fields = ['id']

    @staticmethod
    def get_user(resume: Resume):
        return UserSerializer(resume.user).data

    @staticmethod
    def get_sections(resume: Resume):
        # Optimize queryset to prevent N+1 queries by eagerly loading all related objects
        sections = resume.resumesection_set.select_related(
            'education', 
            'education__country',
            'experience',
            'experience__country', 
            'project',
            'certification'
        ).prefetch_related(
            'proficiency_set__skill__alias',  # For skills in proficiency sections
            'project__skills_used__alias'     # For skills used in projects
        ).order_by('index')
        
        return ResumeSectionFullSerializer(sections, many=True).data


class BaseResumeUtilSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = ('id', 'base', 'user', 'sections')
        read_only_fields = ['id']

    @staticmethod
    def get_user(resume: Resume):
        return UserSerializer(resume.user).data

    @staticmethod
    def get_sections(resume: Resume):
        # Optimize queryset to prevent N+1 queries by eagerly loading all related objects
        sections = resume.resumesection_set.select_related(
            'education', 
            'education__country',
            'experience',
            'experience__country', 
            'project',
            'certification'
        ).prefetch_related(
            'proficiency_set__skill__alias',  # For skills in proficiency sections
            'project__skills_used__alias'     # For skills used in projects
        ).order_by('index')
        
        return ResumeSectionFullSerializer(sections, many=True).data


class ResumeFullSerializer(BaseResumeFullSerializer):
    job = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = ('id', 'base', 'user', 'job', 'status', 'sections', 'thumbnail')
        read_only_fields = ['id']

    @staticmethod
    def get_job(resume: Resume):
        return JobFullSerializer(resume.job).data

    @staticmethod
    def get_status(resume: Resume):
        return resume.get_status_display()

class ResumeSectionFullSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    class Meta:
        model = ResumeSection
        fields = ('id', 'resume', 'index', 'type', 'data')
        read_only_fields = ['id']

    @staticmethod
    def get_id(resume_section: ResumeSection):
        return str(resume_section.id)

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
                return {'skills': []}
            else:
                return {'skills': ProficiencySerializer(resume_section.proficiency_set.all(), many=True).data}
        else:
            return None


class ResumeSectionShortSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = ResumeSection
        fields = ('id', 'resume', 'index', 'type')
        read_only_fields = ['id']

    @staticmethod
    def get_id(resume_section: ResumeSection):
        return str(resume_section.id)

    @staticmethod
    def get_type(resume_section: ResumeSection):
        return resume_section.get_type_display()


class EducationFullSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    resume_section = serializers.SerializerMethodField()
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
    def get_resume_section(resume_section: ResumeSection):
        return str(resume_section.id)

    @staticmethod
    def get_id(resume_section: ResumeSection):
        return str(resume_section.id)

    @staticmethod
    def get_country(education: Education):
        return CountrySerializer(education.country).data if education.country else None


class EducationUpsertSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    class Meta:
        model = Education
        fields = "__all__"

    @staticmethod
    def get_id(resume_section: ResumeSection):
        return str(resume_section.id)


class ExperienceFullSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    resume_section = serializers.SerializerMethodField()
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
    def get_id(resume_section: ResumeSection):
        return str(resume_section.id)

    @staticmethod
    def get_resume_section(resume_section: ResumeSection):
        return str(resume_section.id)

    @staticmethod
    def get_country(experience: Experience):
        return CountrySerializer(experience.country).data if experience.country else None

    @staticmethod
    def get_employment_type(experience: Experience):
        return experience.get_employment_type_display() if experience.employment_type else None


class ExperienceUpsertSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    class Meta:
        model = Experience
        fields = '__all__'

    @staticmethod
    def get_id(resume_section: ResumeSection):
        return str(resume_section.id)


class ProficiencySerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    resume_section = serializers.SerializerMethodField()
    skill = SkillSerializer()

    class Meta:
        model = Proficiency
        fields = ('id', 'skill', 'resume_section', 'level')

    @staticmethod
    def get_id(resume_section: ResumeSection):
        return str(resume_section.id)

    @staticmethod
    def get_resume_section(resume_section: ResumeSection):
        return str(resume_section.id)


class ResumeSkillUpsertSerializer(serializers.Serializer):
    LEVEL_CHOICES = [
        ('OPERATIONAL', 'OPERATIONAL'),
        ('DEGRADED', 'DEGRADED')
    ]
    name = serializers.CharField(help_text='The name of the skill.')
    category = serializers.CharField(help_text='The category of the skill.')
    level = serializers.ChoiceField(Proficiency.Level.choices, help_text='The proficiency level of the skill.')


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    skills_used = SkillSerializer(many=True)
    resume_section = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    @staticmethod
    def get_id(resume_section: ResumeSection):
        return str(resume_section.id)

    @staticmethod
    def get_resume_section(resume_section: ResumeSection):
        return str(resume_section.id)


class SkillUpsertSerializer(serializers.Serializer):
    name = serializers.CharField(help_text='The name of the skill.')
    category = serializers.CharField(help_text='The category of the skill.')


class ProjectUpsertSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'

    @staticmethod
    def get_id(resume_section: ResumeSection):
        return str(resume_section.id)


class CertificationSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    resume_section = serializers.SerializerMethodField()

    class Meta:
        model = Certification
        fields = '__all__'

    @staticmethod
    def get_id(resume_section: ResumeSection):
        return str(resume_section.id)

    @staticmethod
    def get_resume_section(resume_section: ResumeSection):
        return str(resume_section.id)


class CertificationUpsertSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    class Meta:
        model = Certification
        fields = '__all__'

    @staticmethod
    def get_id(resume_section: ResumeSection):
        return str(resume_section.id)


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
