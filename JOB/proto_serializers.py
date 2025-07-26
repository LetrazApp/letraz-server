from django_grpc_framework import proto_serializers
from .models import Job
from letraz_server.conf.grpc_client.utils import letraz_utils_pb2, letraz_utils_pb2_grpc

class JobFullProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = Job
        proto_class = letraz_utils_pb2.Job
        fields = '__all__'