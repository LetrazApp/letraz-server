from django_socio_grpc import proto_serializers
from rest_framework import serializers
from .grpc import RESUME_pb2

# Skill serializers
class SkillProtoSerializer(proto_serializers.ProtoSerializer):
    name = serializers.CharField()
    category = serializers.CharField()
    alias = serializers.ListField(child=serializers.CharField(), required=False)
    preferred = serializers.BooleanField(default=False)

class SkillWithLevelProtoSerializer(proto_serializers.ProtoSerializer):
    skill = SkillProtoSerializer()
    level = serializers.CharField(allow_null=True, required=False)

class SkillSectionDataProtoSerializer(proto_serializers.ProtoSerializer):
    skills = serializers.ListField(child=SkillWithLevelProtoSerializer())

# Country serializer
class CountryProtoSerializer(proto_serializers.ProtoSerializer):
    code = serializers.CharField()
    name = serializers.CharField()

# Experience serializers
class ExperienceDataProtoSerializer(proto_serializers.ProtoSerializer):
    job_title = serializers.CharField()
    company_name = serializers.CharField()
    city = serializers.CharField()
    country = CountryProtoSerializer()
    employment_type = serializers.CharField()
    current = serializers.BooleanField()
    started_from_month = serializers.IntegerField(allow_null=True, required=False)
    started_from_year = serializers.IntegerField(allow_null=True, required=False)
    finished_at_month = serializers.IntegerField(allow_null=True, required=False)
    finished_at_year = serializers.IntegerField(allow_null=True, required=False)
    description = serializers.CharField()

# Project serializers
class ProjectDataProtoSerializer(proto_serializers.ProtoSerializer):
    name = serializers.CharField()
    role = serializers.CharField()
    category = serializers.CharField()
    current = serializers.BooleanField()
    started_from_month = serializers.IntegerField(allow_null=True, required=False)
    started_from_year = serializers.IntegerField(allow_null=True, required=False)
    finished_at_month = serializers.IntegerField(allow_null=True, required=False)
    finished_at_year = serializers.IntegerField(allow_null=True, required=False)
    description = serializers.CharField()
    github_url = serializers.URLField(allow_blank=True, required=False)
    live_url = serializers.URLField(allow_blank=True, required=False)
    skills_used = serializers.ListField(child=SkillProtoSerializer(), required=False)

# Education serializers
class EducationDataProtoSerializer(proto_serializers.ProtoSerializer):
    institution_name = serializers.CharField()
    degree = serializers.CharField()
    field_of_study = serializers.CharField()
    country = CountryProtoSerializer()
    current = serializers.BooleanField()
    started_from_month = serializers.IntegerField(allow_null=True, required=False)
    started_from_year = serializers.IntegerField(allow_null=True, required=False)
    finished_at_month = serializers.IntegerField(allow_null=True, required=False)
    finished_at_year = serializers.IntegerField(allow_null=True, required=False)
    description = serializers.CharField(allow_blank=True, required=False)

# Certification serializers
class CertificationDataProtoSerializer(proto_serializers.ProtoSerializer):
    name = serializers.CharField()
    issuing_organization = serializers.CharField()
    issue_date = serializers.DateField()
    credential_url = serializers.URLField(allow_blank=True, required=False)

# Section serializers
class SectionProtoSerializer(proto_serializers.ProtoSerializer):
    type = serializers.CharField()
    data = serializers.JSONField()  # Will be one of the above data types

# Resume serializers
class TailoredResumeProtoSerializer(proto_serializers.ProtoSerializer):
    id = serializers.CharField()
    sections = serializers.ListField(child=SectionProtoSerializer())

# Suggestion serializers
class SuggestionProtoSerializer(proto_serializers.ProtoSerializer):
    id = serializers.CharField()
    type = serializers.CharField()
    priority = serializers.CharField()
    impact = serializers.CharField()
    section = serializers.CharField()
    current = serializers.CharField()
    suggested = serializers.CharField()
    reasoning = serializers.CharField()

# Data container serializer
class DataProtoSerializer(proto_serializers.ProtoSerializer):
    tailored_resume = TailoredResumeProtoSerializer()
    suggestions = serializers.ListField(child=SuggestionProtoSerializer())
    thread_id = serializers.CharField()

# Metadata serializer
class MetadataProtoSerializer(proto_serializers.ProtoSerializer):
    company = serializers.CharField()
    job_title = serializers.CharField()
    resume_id = serializers.CharField()

# Main response serializer
class TailorResumeCallBackRequestProtoSerializer(proto_serializers.ProtoSerializer):
    processId = serializers.CharField()
    status = serializers.CharField()
    data = DataProtoSerializer()
    timestamp = serializers.DateTimeField()
    operation = serializers.CharField()
    processing_time = serializers.CharField()
    metadata = MetadataProtoSerializer()


class TailorResumeCallBackResponseSerializer(proto_serializers.ProtoSerializer):
    class Meta:
        proto_class = RESUME_pb2.TailorResumeCallBackResponse
    msg = serializers.CharField(required=False)