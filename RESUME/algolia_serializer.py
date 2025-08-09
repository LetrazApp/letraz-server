import datetime
from rest_framework import serializers
from JOB.serializers import JobShortSerializer
from RESUME.models import Resume, ResumeSection, Education, Experience, Project, Certification, Proficiency


class AlgoliaIndexResumeSerializer(serializers.ModelSerializer):
    objectID = serializers.SerializerMethodField()
    job = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    indexed_at = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = ('objectID', 'id', 'user', 'job', 'status', 'sections', 'thumbnail', 'indexed_at')

    @staticmethod
    def get_objectID(resume: Resume):
        return resume.id

    @staticmethod
    def get_job(resume: Resume):
        return JobShortSerializer(resume.job).data

    @staticmethod
    def get_status(resume: Resume):
        return resume.get_status_display()

    @staticmethod
    def get_user(resume: Resume):
        return resume.user.id

    @staticmethod
    def get_sections(resume: Resume):
        return AlgoliaIndexResumeSectionSerializer(resume.resumesection_set.order_by('index'), many=True).data

    @staticmethod
    def get_indexed_at(resume: Resume):
        return datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')


class AlgoliaIndexResumeSectionSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    class Meta:
        model = ResumeSection
        fields = ('type', 'data')

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
                return AlgoliaIndexResumeEducationSerializer(resume_section.education).data
            except Education.DoesNotExist:
                resume_section.delete()
                return None
        elif resume_section.type == ResumeSection.ResumeSectionType.Experience:
            try:
                return AlgoliaIndexResumeExperienceSerializer(resume_section.experience).data
            except Experience.DoesNotExist:
                resume_section.delete()
                return None
        elif resume_section.type == ResumeSection.ResumeSectionType.Project:
            try:
                return AlgoliaIndexResumeProjectSerializer(resume_section.project).data
            except Project.DoesNotExist:
                resume_section.delete()
                return None
        elif resume_section.type == ResumeSection.ResumeSectionType.Certification:
            try:
                return AlgoliaIndexResumeCertificationSerializer(resume_section.certification).data
            except Certification.DoesNotExist:
                resume_section.delete()
                return None
        elif resume_section.type == ResumeSection.ResumeSectionType.Skill:
            if resume_section.proficiency_set.count() == 0:
                resume_section.delete()
                return {'skills': []}
            else:
                return {'skills': AlgoliaIndexResumeProficiencySerializer(resume_section.proficiency_set.all(), many=True).data}
        else:
            return None


class AlgoliaIndexResumeEducationSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()

    class Meta:
        model = Education
        fields = (
            'institution_name', 'field_of_study', 'degree', 'country', 'current', 'description'
        )


    @staticmethod
    def get_country(education: Education):
        return education.country.name if education.country else None


class AlgoliaIndexResumeExperienceSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()
    employment_type = serializers.SerializerMethodField()

    class Meta:
        model = Experience
        fields = (
            'company_name', 'job_title', 'employment_type', 'city', 'country',
            'current', 'description'
        )

    @staticmethod
    def get_country(experience: Experience):
        return experience.country.name if experience.country else None

    @staticmethod
    def get_employment_type(experience: Experience):
        return experience.get_employment_type_display() if experience.employment_type else None


class AlgoliaIndexResumeProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'category', 'name', 'description', 'role', 'github_url', 'live_url', 'current'
        )


class AlgoliaIndexResumeCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = (
            'name', 'issuing_organization', 'issue_date', 'credential_url'
        )


class AlgoliaIndexResumeProficiencySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Proficiency
        fields = ('name', 'category', 'level')

    @staticmethod
    def get_name(proficiency: Proficiency):
        return proficiency.skill.name if proficiency.skill else None

    @staticmethod
    def get_category(proficiency: Proficiency):
        return proficiency.skill.category if proficiency.skill else None
