from django_grpc_framework import proto_serializers
from rest_framework import serializers
from PROFILE.models import User
from .models import Resume, ResumeSection, Education, Project, Certification, Experience, Proficiency
from letraz_server.conf.grpc_client.utils import letraz_utils_pb2
from .serializers import EducationFullSerializer, ExperienceFullSerializer, ProjectSerializer, CertificationSerializer, \
    ProficiencySerializer


class ResumeFullProtoSerializer(proto_serializers.ModelProtoSerializer):
    user = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        proto_class = letraz_utils_pb2.BaseResume
        fields = '__all__'


    @staticmethod
    def get_user(resume: Resume):
        return UserProtoSerializer(resume.user).data

    @staticmethod
    def get_sections(resume: Resume):
        return ResumeSectionFullProtoSerializer(resume.resumesection_set.order_by('index'), many=True).data


class UserProtoSerializer(proto_serializers.ModelProtoSerializer):
    country = serializers.SerializerMethodField()

    class Meta:
        model = User
        proto_class = letraz_utils_pb2.User
        fields = (
            'id', 'title', 'first_name', 'last_name', 'email', 'phone', 'dob',
            'nationality', 'address', 'city', 'postal', 'country', 'website',
            'profile_text', 'created_at', 'updated_at'
        )

    @staticmethod
    def get_country(user: User):
        if user.country:
            return user.country.name.__str__()
        else:
            return ''


class ResumeSectionFullProtoSerializer(proto_serializers.ModelProtoSerializer):
    type = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    class Meta:
        model = ResumeSection
        proto_class = letraz_utils_pb2.ResumeSection
        fields = ('id', 'resume', 'index', 'type', 'data')

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

