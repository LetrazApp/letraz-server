import logging
import threading

from django_socio_grpc import generics
from django_socio_grpc.exceptions import NotFound, InvalidArgument, GRPCException
from CORE.models import Process
from JOB.models import Job
from JOB.proto_serialzers import ScrapeJobCallbackRequestSerializer, ScrapeJobResponseSerializer
from RESUME.utils import bulk_call_tailor_resume_for_the_job
from letraz_server.settings import PROJECT_NAME
from django_socio_grpc.decorators import grpc_action
from google.protobuf.json_format import MessageToDict

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


class ScrapeJobCallbackService(generics.GenericService):

    @grpc_action(
        request=ScrapeJobCallbackRequestSerializer,
        response=ScrapeJobResponseSerializer,  # Empty response
    )
    async def ScrapeJobCallBack(self, request, context):
        util_process_id = str(request.processId)
        # Your implementation here
        process_qs = Process.objects.filter(util_id=request.processId)
        if not await process_qs.aexists():
            raise NotFound(f"No process found with that util process id: {request.processId}")
        process = await process_qs.afirst()
        in_progress_job_qs = Job.objects.filter(process=process)
        if not await in_progress_job_qs.aexists():
            process.status = Process.ProcessStatus.Failed.value
            process.status_details=f"No job found for the process: {process.id}"
            await process.asave()
            raise NotFound(f"No job found for the process: {process.id}")
        if not request.data or not request.data.job:
            process.status = Process.ProcessStatus.Failed.value
            process.status_details = f"Must return a job object"
            await process.asave()
            raise InvalidArgument(f"Must return a job object")
        try:
            in_progress_job: Job = await in_progress_job_qs.afirst()
            job_data = MessageToDict(request.data.job)
            logger.debug(f"[util id - {util_process_id}] [method: ScrapeJobCallBack] Job data: {job_data}")
            in_progress_job.title = job_data.get('title')
            in_progress_job.company_name = job_data.get('companyName')
            in_progress_job.location = job_data.get('location')
            if job_data.get('salary'):
                in_progress_job.currency = job_data.get('salary').get('currency')
                in_progress_job.salary_max = job_data.get('salary').get('max')
                in_progress_job.salary_min = job_data.get('salary').get('min')
            in_progress_job.requirements = job_data.get('requirements')
            in_progress_job.description = job_data.get('description')
            in_progress_job.responsibilities = job_data.get('responsibilities')
            in_progress_job.benefits = job_data.get('benefits')

            in_progress_job.status = Job.Status.Success.value

            await in_progress_job.asave()
            process.status = Process.ProcessStatus.Success.value
            process.status_details = f"Successfully updated the job: {in_progress_job.id}"
            await process.asave()
            batch = threading.Thread(target=bulk_call_tailor_resume_for_the_job, args=(in_progress_job, f'ScrapeJobCallBack :: util Process id: {util_process_id}'))
            batch.start()
            # bulk_call_tailor_resume_for_the_job(job=in_progress_job, source=f'ScrapeJobCallBack :: util Process id: {util_process_id}')
        except Exception as e:
            process.status = Process.ProcessStatus.Failed.value
            error_msg = f'[util id - {util_process_id}] [method: ScrapeJobCallBack] {str(e)}'
            logger.exception(error_msg)
            process.status_details=error_msg[:249]
            await process.asave()
            raise GRPCException(str(e))

        return ScrapeJobResponseSerializer("OK").message