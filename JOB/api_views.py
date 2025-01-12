from django.db.models import QuerySet
from rest_framework.decorators import api_view
from rest_framework.response import Response
from JOB.models import Job
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from .serializers import JobFullSerializer


@api_view(['GET'])
def job_crud(request, job_id: str):
    if request.method == 'GET':
        job_by_job_and_user_id_qs: QuerySet[Job] = Job.objects.filter(id=job_id)
        if job_by_job_and_user_id_qs.exists():
            return Response(JobFullSerializer(job_by_job_and_user_id_qs.first()).data)
        else:
            return ErrorResponse(code=ErrorCode.NOT_FOUND, message='Job not found!', details={'job': job_id}).response
