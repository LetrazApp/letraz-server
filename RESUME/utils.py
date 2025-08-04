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
        logger.debug(f'[source={source}] :: call_tailor_resume_util_service : Response: \n{res}')
        process.status = res.get('status')
        process.util_id = res.get('processId')
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
    in_progress_resumes_for_job = job.resume_set.all()
    for in_progress_resume in in_progress_resumes_for_job:
        logger.info(f'[Source={source}]Tailor Resume Process called for resume: {in_progress_resume.id}')
        call_tailor_resume_util_service(job=job, target_resume=in_progress_resume, source=source)


def should_generate_thumbnail(resume: Resume, change_type: str, change_details: dict = None) -> bool:
    """
    Determine if thumbnail generation is warranted based on change impact.
    
    Args:
        resume: The resume object that was changed
        change_type: Type of change that occurred
        change_details: Additional details about the change (optional)
    
    Returns:
        bool: True if thumbnail should be generated, False otherwise
    """
    # Base resumes always get priority - any change warrants thumbnail update
    if resume.base:
        logger.info(f'Thumbnail generation triggered for base resume {resume.id} due to {change_type}')
        return True
    
    # High impact changes - always trigger thumbnail generation
    high_impact_changes = ['section_added', 'section_removed', 'section_reordered', 'section_type_changed']
    if change_type in high_impact_changes:
        logger.info(f'Thumbnail generation triggered for resume {resume.id} due to high impact change: {change_type}')
        return True
    
    # Medium impact changes - trigger based on content analysis
    if change_type == 'content_change' and change_details:
        old_length = change_details.get('old_length', 0)
        new_length = change_details.get('new_length', 0)
        
        if old_length > 0:
            change_percentage = abs(new_length - old_length) / old_length
            threshold = getattr(settings, 'THUMBNAIL_IMPACT_THRESHOLD', 0.20)  # 20% default
            
            if change_percentage > threshold:
                logger.info(f'Thumbnail generation triggered for resume {resume.id} due to significant content change: {change_percentage:.2%}')
                return True
    
    # Profile changes for non-base resumes
    if change_type == 'profile_change':
        logger.info(f'Thumbnail generation triggered for resume {resume.id} due to profile change')
        return True
    
    # Low impact changes - typically don't trigger thumbnail generation
    logger.debug(f'Thumbnail generation skipped for resume {resume.id} due to low impact change: {change_type}')
    return False


def generate_resume_thumbnail(resume: Resume, change_type: str = None, change_details: dict = None, source: str = None):
    """
    Generate thumbnail for resume, replacing any existing thumbnail process.
    
    Args:
        resume: The resume object to generate thumbnail for
        change_type: Type of change that triggered the generation (optional)
        change_details: Additional details about the change (optional)
        source: Source of the generation request (optional)
    
    Returns:
        tuple: (resume, error_response) - resume object if successful, error_response if failed
    """
    # Check if thumbnail generation is enabled
    if not getattr(settings, 'THUMBNAIL_GENERATION_ENABLED', True):
        logger.debug(f'Thumbnail generation disabled, skipping for resume {resume.id}')
        return resume, None
    
    # Determine if thumbnail should be generated based on change impact
    if change_type and not should_generate_thumbnail(resume, change_type, change_details):
        logger.debug(f'Thumbnail generation skipped for resume {resume.id} due to low impact change')
        return resume, None
    
    logger.info(f'[source={source}] Starting thumbnail generation for resume {resume.id} (base: {resume.base})')
    
    # Step 1: Clean up existing thumbnail process
    if resume.thumbnail_process:
        old_process = resume.thumbnail_process
        resume.thumbnail_process = None
        resume.save()
        old_process.delete()
        logger.debug(f'[source={source}] Cleaned up existing thumbnail process for resume {resume.id}')
    
    # Step 2: Create new thumbnail process
    thumbnail_process = Process.objects.create(desc='Resume Thumbnail Generation')
    resume.thumbnail_process = thumbnail_process
    resume.save()
    
    # Step 3: Make gRPC call
    try:
        resume_service = letraz_utils_pb2_grpc.ResumeServiceStub(settings.UTIL_GRPC_CHANNEL)
        req = letraz_utils_pb2.ResumeScreenshotRequest(resume_id=resume.id)
        res = MessageToDict(resume_service.GenerateScreenshot(req))
        
        logger.debug(f'[source={source}] :: generate_resume_thumbnail : Response: \n{res}')
        
        # Step 4: Update process with response
        thumbnail_process.status = res.get('status')
        thumbnail_process.util_id = res.get('processId')
        thumbnail_process.status_details = res.get('message')
        thumbnail_process.save()
        
        logger.info(f'[source={source}] Thumbnail generation accepted for resume {resume.id}, process_id: {res.get("processId")}')
        return resume, None
        
    except Exception as e:
        error_response = ErrorResponse(code=ErrorCode.INTERNAL_SERVER_ERROR, message=e.__str__())
        logger.exception(f'Exception=> [Source={source}] | Thumbnail generation gRPC call error [UTIL]: {e.__str__()}')
        
        # Update process with failure status
        thumbnail_process.status = Process.ProcessStatus.Failed.value
        thumbnail_process.status_details = f'[Source={source}] - {e.__str__()}'
        thumbnail_process.save()
        
        return None, error_response