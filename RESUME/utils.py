import logging
import threading
from contextlib import contextmanager
from django.conf import settings
from django.core.cache import cache

from CORE.models import Process
from JOB.models import Job
from JOB.serializers import JobSerializer
from RESUME.algolia_serializer import AlgoliaIndexResumeSerializer
from RESUME.models import Resume
from django.contrib.auth.models import User as AuthUser

from RESUME.serializers import BaseResumeFullSerializer, BaseResumeUtilSerializer
from letraz_server.conf.grpc_client.utils import letraz_utils_pb2_grpc, letraz_utils_pb2
from google.protobuf.json_format import MessageToDict

from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from letraz_server.settings import PROJECT_NAME, ALGOLIA_CLIENT

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)

# Thread-local storage for deletion context
_local = threading.local()


@contextmanager
def disable_thumbnail_generation():
    """Context manager to temporarily disable thumbnail generation"""
    _local.disable_thumbnails = True
    try:
        yield
    finally:
        _local.disable_thumbnails = False


def is_thumbnail_generation_disabled():
    """Check if thumbnail generation is currently disabled"""
    return getattr(_local, 'disable_thumbnails', False)


def call_tailor_resume_util_service(job:Job, target_resume: Resume, source=None):
    # GRPC: Call Tailor-Resume RPC method to Util service
    process = Process.objects.create(desc='Tailor Resume Process')
    try:
        base_resume = target_resume.user.resume_set.get(base=True)
        resume_service = letraz_utils_pb2_grpc.ResumeServiceStub(settings.UTIL_GRPC_CHANNEL)
        req = letraz_utils_pb2.TailorResumeRequest(base_resume=BaseResumeUtilSerializer(base_resume, many=False).data,
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


def should_generate_thumbnail(resume, change_type, change_details=None):
    """
    Determine if thumbnail generation is warranted based on change impact.
    
    Args:
        resume: Resume instance
        change_type: Type of change ('section_added', 'section_removed', 'section_reordered', 'content_change', 'profile_change')
        change_details: Additional details about the change (optional)
    
    Returns:
        bool: True if thumbnail should be generated
    """
    # Check if thumbnail generation is globally disabled
    if is_thumbnail_generation_disabled():
        logger.debug(f'Thumbnail generation globally disabled, skipping resume {resume.id}')
        return False
    
    # Check if thumbnail generation is temporarily disabled for this resume instance
    if hasattr(resume, '_skip_thumbnail_generation') and resume._skip_thumbnail_generation:
        logger.debug(f'Thumbnail generation skipped for resume {resume.id} due to bulk operation flag')
        return False
    
    # Base resumes always get priority - all changes warrant thumbnail updates
    if resume.base:
        logger.info(f'Base resume {resume.id} always gets thumbnail generation priority')
        return True
    
    # High impact changes always trigger thumbnail generation
    high_impact_changes = ['section_added', 'section_removed', 'section_reordered']
    if change_type in high_impact_changes:
        logger.info(f'High impact change "{change_type}" detected for resume {resume.id}')
        return True
    
    # Medium impact changes with threshold
    if change_type == 'content_change' and change_details:
        old_length = change_details.get('old_length', 0)
        new_length = change_details.get('new_length', 0)
        if old_length > 0:
            change_percentage = abs(new_length - old_length) / old_length
            threshold_exceeded = change_percentage > getattr(settings, 'THUMBNAIL_IMPACT_THRESHOLD', 0.20)
            if threshold_exceeded:
                logger.info(f'Content change threshold exceeded ({change_percentage:.2%}) for resume {resume.id}')
            return threshold_exceeded
    
    # Profile changes for base resumes are already handled above
    if change_type == 'profile_change':
        logger.info(f'Profile change detected for non-base resume {resume.id}')
        return True
    
    logger.debug(f'No thumbnail generation needed for change "{change_type}" on resume {resume.id}')
    return False


def generate_resume_thumbnail(resume):
    """
    Generate thumbnail for resume, replacing any existing process.
    
    Args:
        resume: Resume instance to generate thumbnail for
        
    Returns:
        bool: True if generation was initiated successfully, False otherwise
    """
    # Additional safety check: Ensure the resume still exists in database
    # This prevents issues during cascade deletions
    try:
        Resume.objects.get(id=resume.id)
    except Resume.DoesNotExist:
        logger.debug(f'Resume {resume.id} no longer exists, skipping thumbnail generation')
        return False
    
    # Check if thumbnail generation is disabled globally
    if is_thumbnail_generation_disabled():
        logger.debug(f'Thumbnail generation globally disabled, skipping resume {resume.id}')
        return False
    
    # Check if thumbnail generation is enabled
    if not getattr(settings, 'THUMBNAIL_GENERATION_ENABLED', True):
        logger.info(f'Thumbnail generation disabled, skipping resume {resume.id}')
        return False
    
    # Check if gRPC channel is available
    if not hasattr(settings, 'UTIL_GRPC_CHANNEL') or not settings.UTIL_GRPC_CHANNEL:
        logger.error(f'gRPC channel not available for thumbnail generation of resume {resume.id}')
        return False
    
    # Prevent duplicate thumbnail generation within short time window (10 seconds)
    cache_key = f'thumbnail_generation_{resume.id}'
    if cache.get(cache_key):
        logger.debug(f'Thumbnail generation already in progress for resume {resume.id}, skipping duplicate')
        return False
    
    # Set cache to prevent duplicates for 10 seconds
    cache.set(cache_key, True, 10)
    
    logger.info(f'Triggering thumbnail generation for resume {resume.id} (base: {resume.base})')
    
    # Step 1: Clean up existing thumbnail process
    if resume.thumbnail_process:
        old_process = resume.thumbnail_process
        resume.thumbnail_process = None
        resume.save()
        old_process.delete()
        logger.debug(f'Cleaned up existing thumbnail process for resume {resume.id}')
    
    # Step 2: Create new process
    thumbnail_process = Process.objects.create(desc='Resume Thumbnail Generation')
    resume.thumbnail_process = thumbnail_process
    resume.save()
    
    # Step 3: Make gRPC call
    try:
        resume_service = letraz_utils_pb2_grpc.ResumeServiceStub(settings.UTIL_GRPC_CHANNEL)
        req = letraz_utils_pb2.ResumeScreenshotRequest(resume_id=resume.id)
        res = MessageToDict(resume_service.GenerateScreenshot(req))
        
        logger.debug(f'Thumbnail generation response for resume {resume.id}: {res}')
        
        # Step 4: Update process with response
        thumbnail_process.status = res.get('status')
        thumbnail_process.util_id = res.get('processId')  # gRPC response uses camelCase 'processId'
        thumbnail_process.status_details = res.get('message')
        thumbnail_process.save()
        
        logger.info(f'Thumbnail generation accepted for resume {resume.id}, process_id: {thumbnail_process.util_id}')
        return True
        
    except Exception as e:
        # Handle gRPC errors
        thumbnail_process.status = Process.ProcessStatus.Failed.value
        # Truncate error message to fit database field (max 250 chars)
        error_msg = f'gRPC Error: {str(e)}'
        thumbnail_process.status_details = error_msg[:247] + '...' if len(error_msg) > 250 else error_msg
        thumbnail_process.save()
        logger.exception(f'Thumbnail generation failed for resume {resume.id}: {e}')
        return False
    finally:
        # Always clear the cache after completion (success or failure)
        cache.delete(cache_key)

def index_resume_by_id(resume_id: str):
    resume_qs = Resume.objects.filter(pk=resume_id)
    if not resume_qs.exists():
        logger.warning(f'Resume {resume_id} no longer exists, skipping indexing')
    else:
        resume = resume_qs.first()
        data = AlgoliaIndexResumeSerializer(resume).data
        ALGOLIA_CLIENT.add_resume(data)