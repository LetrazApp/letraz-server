import json
import logging
import sys
from datetime import datetime

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from PROFILE.models import User
from .algolia_serializer import AlgoliaIndexResumeSerializer
from .models import Resume, ResumeSection, Education, Experience, Project, Certification
from .serializers import ResumeFullSerializer
from .utils import should_generate_thumbnail, generate_resume_thumbnail_async
from letraz_server.settings import PROJECT_NAME, ALGOLIA_CLIENT
import sentry_sdk

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


@receiver(post_save, sender=ResumeSection)
def handle_resume_section_change(sender, instance, created, **kwargs):
    """Trigger thumbnail generation when resume sections change"""
    resume = instance.resume
    
    if created:
        change_type = 'section_added'
        logger.debug(f'New resume section {instance.type} added to resume {resume.id}')
    else:
        change_type = 'section_modified'
        logger.debug(f'Resume section {instance.id} modified in resume {resume.id}')
    
    if should_generate_thumbnail(resume, change_type):
        transaction.on_commit(lambda: generate_resume_thumbnail_async(resume))


@receiver(post_delete, sender=ResumeSection) 
def handle_resume_section_delete(sender, instance, **kwargs):
    """Trigger thumbnail generation when resume sections are deleted"""
    # Check if the resume still exists before attempting thumbnail generation
    # This prevents thumbnail generation during cascade deletion of the resume itself
    try:
        resume = Resume.objects.get(id=instance.resume.id)
        logger.debug(f'Resume section {instance.id} deleted from resume {resume.id}')
        
        if should_generate_thumbnail(resume, 'section_removed'):
            transaction.on_commit(lambda: generate_resume_thumbnail_async(resume))
    except Resume.DoesNotExist:
        logger.debug(f'Resume {instance.resume.id} no longer exists, skipping thumbnail generation for deleted section {instance.id}')


@receiver(post_save, sender=User)
def handle_user_profile_change(sender, instance, **kwargs):
    """Trigger thumbnail generation for user's base resume when profile changes"""
    try:
        base_resume = instance.resume_set.get(base=True)
        logger.debug(f'User profile change detected for user {instance.id}, checking base resume {base_resume.id}')
        
        if should_generate_thumbnail(base_resume, 'profile_change'):
            transaction.on_commit(lambda: generate_resume_thumbnail_async(base_resume))
    except Resume.DoesNotExist:
        logger.debug(f'User {instance.id} does not have a base resume yet')
    except Resume.MultipleObjectsReturned:
        logger.warning(f'User {instance.id} has multiple base resumes - this should not happen')


@receiver(post_save, sender=Education)
def handle_education_change(sender, instance, created, **kwargs):
    """Trigger thumbnail generation when education entries change"""
    if not hasattr(instance, 'resume_section') or not instance.resume_section:
        return
        
    resume = instance.resume_section.resume
    
    if created:
        change_type = 'section_added'
        logger.debug(f'New education entry added to resume {resume.id}')
    else:
        change_type = 'content_change'
        logger.debug(f'Education entry {instance.id} modified in resume {resume.id}')
    
    if should_generate_thumbnail(resume, change_type):
        transaction.on_commit(lambda: generate_resume_thumbnail_async(resume))


@receiver(post_delete, sender=Education)
def handle_education_delete(sender, instance, **kwargs):
    """Trigger thumbnail generation when education entries are deleted"""
    if not hasattr(instance, 'resume_section') or not instance.resume_section:
        return
    
    # Check if the resume still exists before attempting thumbnail generation
    # This prevents thumbnail generation during cascade deletion of the resume itself
    try:
        resume = Resume.objects.get(id=instance.resume_section.resume.id)
        logger.debug(f'Education entry deleted from resume {resume.id}')
        
        if should_generate_thumbnail(resume, 'section_removed'):
            transaction.on_commit(lambda: generate_resume_thumbnail_async(resume))
    except Resume.DoesNotExist:
        logger.debug(f'Resume no longer exists, skipping thumbnail generation for deleted education {instance.id}')


@receiver(post_save, sender=Experience)
def handle_experience_change(sender, instance, created, **kwargs):
    """Trigger thumbnail generation when experience entries change"""
    if not hasattr(instance, 'resume_section') or not instance.resume_section:
        return
        
    resume = instance.resume_section.resume
    
    if created:
        change_type = 'section_added'
        logger.debug(f'New experience entry added to resume {resume.id}')
    else:
        change_type = 'content_change'
        logger.debug(f'Experience entry {instance.id} modified in resume {resume.id}')
    
    if should_generate_thumbnail(resume, change_type):
        transaction.on_commit(lambda: generate_resume_thumbnail_async(resume))


@receiver(post_delete, sender=Experience)
def handle_experience_delete(sender, instance, **kwargs):
    """Trigger thumbnail generation when experience entries are deleted"""
    if not hasattr(instance, 'resume_section') or not instance.resume_section:
        return
    
    # Check if the resume still exists before attempting thumbnail generation
    # This prevents thumbnail generation during cascade deletion of the resume itself
    try:
        resume = Resume.objects.get(id=instance.resume_section.resume.id)
        logger.debug(f'Experience entry deleted from resume {resume.id}')
        
        if should_generate_thumbnail(resume, 'section_removed'):
            transaction.on_commit(lambda: generate_resume_thumbnail_async(resume))
    except Resume.DoesNotExist:
        logger.debug(f'Resume no longer exists, skipping thumbnail generation for deleted experience {instance.id}')


@receiver(post_save, sender=Project)
def handle_project_change(sender, instance, created, **kwargs):
    """Trigger thumbnail generation when project entries change"""
    if not hasattr(instance, 'resume_section') or not instance.resume_section:
        return
        
    resume = instance.resume_section.resume
    
    if created:
        change_type = 'section_added'
        logger.debug(f'New project entry added to resume {resume.id}')
    else:
        change_type = 'content_change'
        logger.debug(f'Project entry {instance.id} modified in resume {resume.id}')
    
    if should_generate_thumbnail(resume, change_type):
        transaction.on_commit(lambda: generate_resume_thumbnail_async(resume))


@receiver(post_delete, sender=Project)
def handle_project_delete(sender, instance, **kwargs):
    """Trigger thumbnail generation when project entries are deleted"""
    if not hasattr(instance, 'resume_section') or not instance.resume_section:
        return
    
    # Check if the resume still exists before attempting thumbnail generation
    # This prevents thumbnail generation during cascade deletion of the resume itself
    try:
        resume = Resume.objects.get(id=instance.resume_section.resume.id)
        logger.debug(f'Project entry deleted from resume {resume.id}')
        
        if should_generate_thumbnail(resume, 'section_removed'):
            transaction.on_commit(lambda: generate_resume_thumbnail_async(resume))
    except Resume.DoesNotExist:
        logger.debug(f'Resume no longer exists, skipping thumbnail generation for deleted project {instance.id}')


@receiver(post_save, sender=Certification)
def handle_certification_change(sender, instance, created, **kwargs):
    """Trigger thumbnail generation when certification entries change"""
    if not hasattr(instance, 'resume_section') or not instance.resume_section:
        return
        
    resume = instance.resume_section.resume
    
    if created:
        change_type = 'section_added'
        logger.debug(f'New certification entry added to resume {resume.id}')
    else:
        change_type = 'content_change'
        logger.debug(f'Certification entry {instance.id} modified in resume {resume.id}')
    
    if should_generate_thumbnail(resume, change_type):
        transaction.on_commit(lambda: generate_resume_thumbnail_async(resume))


@receiver(post_delete, sender=Certification)
def handle_certification_delete(sender, instance, **kwargs):
    """Trigger thumbnail generation when certification entries are deleted"""
    if not hasattr(instance, 'resume_section') or not instance.resume_section:
        return
    
    # Check if the resume still exists before attempting thumbnail generation
    # This prevents thumbnail generation during cascade deletion of the resume itself
    try:
        resume = Resume.objects.get(id=instance.resume_section.resume.id)
        logger.debug(f'Certification entry deleted from resume {resume.id}')
        
        if should_generate_thumbnail(resume, 'section_removed'):
            generate_resume_thumbnail_async(resume)
    except Resume.DoesNotExist:
        logger.debug(f'Resume no longer exists, skipping thumbnail generation for deleted certification {instance.id}')


@receiver(post_save, sender=Resume)
def handle_resume_change(sender, instance: Resume, created, **kwargs):
    """Trigger thumbnail generation when resume is created or significantly modified"""
    if created and instance.base:
        # New base resume created- generate thumbnail immediately
        logger.info(f'New base resume {instance.id} created for user {instance.user.id}')
        if should_generate_thumbnail(instance, 'section_added'):
            transaction.on_commit(lambda: generate_resume_thumbnail_async(instance))

@receiver(post_delete, sender=Resume, dispatch_uid="resume_post_delete_algolia_sync")
def handle_resume_delete(sender, instance: Resume, **kwargs):
    """
    Remove a resume from Algolia after the DB transaction commits.
    """
    resume_id = str(instance.id)
    user_id = str(instance.user.id)

    def _deindex():
        try:
            client = getattr(ALGOLIA_CLIENT, "client", None)
            if client is None:
                logger.warning("Algolia client is not initialized, skipping deindex.")
                return

            index_name = "resume"
            client.delete_object(index_name=index_name, object_id=resume_id)
            logger.info(f"Deleted resume {resume_id} from Algolia index '{index_name}'.")

        except Exception as e:
            # Log locally
            logger.error(
                "Failed to delete resume %s (user %s) from Algolia index: %s",
                resume_id,
                user_id,
                str(e),
                exc_info=True,
            )

    transaction.on_commit(_deindex)
