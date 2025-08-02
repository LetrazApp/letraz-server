from django_socio_grpc.proto_serializers import ProtoSerializer
from rest_framework import serializers
from .grpc import JOB_pb2

class JobSalarySerializer(ProtoSerializer):
    currency = serializers.CharField(required=False)
    max = serializers.IntegerField(required=False)
    min = serializers.IntegerField(required=False)


class JobDetailSerializer(ProtoSerializer):
    title = serializers.CharField()
    job_url = serializers.CharField()
    company_name = serializers.CharField()
    location = serializers.CharField()
    salary = JobSalarySerializer(required=False)
    requirements = serializers.ListField(child=serializers.CharField(), required=False)
    description = serializers.CharField()
    responsibilities = serializers.ListField(child=serializers.CharField(), required=False)
    benefits = serializers.ListField(child=serializers.CharField(), required=False)


class CallbackMetadataSerializer(ProtoSerializer):
    engine = serializers.CharField(required=False)
    url = serializers.CharField(required=False)


class ScrapeJobDataSerializer(ProtoSerializer):
    job = JobDetailSerializer(required=False)
    engine = serializers.CharField(required=False)
    used_llm = serializers.BooleanField(required=False)


class ScrapeJobCallbackRequestSerializer(ProtoSerializer):
    processId = serializers.CharField()
    status = serializers.CharField()
    data = ScrapeJobDataSerializer(required=False)
    timestamp = serializers.CharField()
    operation = serializers.CharField()
    processing_time = serializers.CharField()
    metadata = CallbackMetadataSerializer(required=False)


class ScrapeJobResponseSerializer(ProtoSerializer):
    class Meta:
        proto_class = JOB_pb2.ScrapeJobResponse
    msg = serializers.CharField(required=False)