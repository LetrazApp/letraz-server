import logging

from CORE.models import Process
from JOB.models import Job
from JOB.serializers import JobSerializer
from RESUME.models import Resume
from django.contrib.auth.models import User as AuthUser

from RESUME.serializers import BaseResumeFullSerializer
from letraz_server import settings
from letraz_server.conf.grpc_client.utils import letraz_utils_pb2_grpc, letraz_utils_pb2
from google.protobuf.json_format import MessageToDict

from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


def call_tailor_resume_util_service(job:Job, target_resume: Resume, source=None):
    # GRPC: Call Tailor-Resume RPC method to Util service
    process = Process.objects.create(desc='Tailor Resume Process')
    try:
        base_resume = target_resume.user.resume_set.get(base=True)
        resume_service = letraz_utils_pb2_grpc.ResumeServiceStub(settings.UTIL_GRPC_CHANNEL)
        req = letraz_utils_pb2.TailorResumeRequest(base_resume=BaseResumeFullSerializer(base_resume, many=False).data,
                                                   job=JobSerializer(job, many=False).data,
                                                   resume_id=target_resume.id)
        res = MessageToDict(resume_service.TailorResume(req))
        logger.debug(f'Tailor Resume Process: \n{res}')
        process.status = res.get('status')
        process.util_id = res.get('util_id')
        process.status_details = res.get('message')
        process.save()
        target_resume.process = process
        target_resume.save()
        return target_resume, None
    except Exception as e:
        error_response = ErrorResponse(code=ErrorCode.INTERNAL_SERVER_ERROR, message=e.__str__())
        logger.exception(f'Exception=> [Source={source}] | GRPC call error [UTIL]: {e.__str__()}')
        process.status = Process.ProcessStatus.Failed.value
        process.status_details = f'[Source={source}] - {e.__str__()}'
        process.save()
        return None, error_response

def bulk_call_tailor_resume_for_the_job(job:Job, source=None):
    in_progress_resumes_for_job = job.resume_set.filter(status=Resume.Status.Processing.value)
    print(in_progress_resumes_for_job)
    for in_progress_resume in in_progress_resumes_for_job:
        logger.info(f'[Source={source}]Tailor Resume Process called for resume: {in_progress_resume.id}')
        call_tailor_resume_util_service(job=job, target_resume=in_progress_resume)