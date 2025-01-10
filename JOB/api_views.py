from rest_framework.decorators import api_view
from rest_framework.response import Response
from JOB.models import Job
from .serializers import JobFullSerializer


@api_view(['GET'])
def job_crud(request, job_id: str):
    if request.method == 'GET':
        job_by_job_and_user_id: Job = Job.objects.filter(id=job_id).first()
        return Response(JobFullSerializer(job_by_job_and_user_id).data)
