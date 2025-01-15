from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from CORE.serializers import ErrorSerializer
from JOB.models import Job
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from .serializers import JobFullSerializer

@extend_schema(
    methods=['GET'],
    tags=['Job object'],
    auth=[],
    responses={200: JobFullSerializer, 500: ErrorSerializer},
    summary="Get job by job ID",
    description="Returns the full job object as saved in the database by the job ID. If the job is not found, an error response is returned."
)
@api_view(['GET'])
def job_crud(request, job_id: str):
    if request.method == 'GET':
        job_by_job_and_user_id_qs: QuerySet[Job] = Job.objects.filter(id=job_id)
        if job_by_job_and_user_id_qs.exists():
            return Response(JobFullSerializer(job_by_job_and_user_id_qs.first()).data)
        else:
            return ErrorResponse(code=ErrorCode.NOT_FOUND, message='Job not found!', details={'job': job_id}).response
