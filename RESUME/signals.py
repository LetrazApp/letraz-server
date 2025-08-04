"""
Django signals for automatic thumbnail generation when resume changes occur.
This file demonstrates how to integrate thumbnail generation with model changes.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from RESUME.models import Resume, ResumeSection, Education, Experience, Project, Certification
from PROFILE.models import User
from RESUME.utils import generate_resume_thumbnail
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ResumeSection)
def handle_resume_section_change(sender, instance, created, **kwargs):
    """
    Trigger thumbnail generation when resume sections change.
    """
    resume = instance.resume
    
    if created:
        change_type = 'section_added'
        logger.info(f'New section added to resume {resume.id}, triggering thumbnail generation')
    else:
        change_type = 'section_modified'
        logger.info(f'Section modified in resume {resume.id}, triggering thumbnail generation')
    
    # Generate thumbnail for the resume
    generate_resume_thumbnail(resume, change_type=change_type, source='resume_section_signal')


@receiver(post_delete, sender=ResumeSection)
def handle_resume_section_delete(sender, instance, **kwargs):
    """
    Trigger thumbnail generation when resume sections are deleted.
    """
    resume = instance.resume
    logger.info(f'Section deleted from resume {resume.id}, triggering thumbnail generation')
    
    # Generate thumbnail for the resume
    generate_resume_thumbnail(resume, change_type='section_removed', source='resume_section_delete_signal')


@receiver(post_save, sender=Education)
def handle_education_change(sender, instance, created, **kwargs):
    """
    Trigger thumbnail generation when education entries change.
    """
    resume = instance.resume_section.resume
    
    if created:
        change_type = 'content_change'
        logger.info(f'New education added to resume {resume.id}, triggering thumbnail generation')
    else:
        change_type = 'content_change'
        logger.info(f'Education modified in resume {resume.id}, triggering thumbnail generation')
    
    # Generate thumbnail for the resume
    generate_resume_thumbnail(resume, change_type=change_type, source='education_signal')


@receiver(post_save, sender=Experience)
def handle_experience_change(sender, instance, created, **kwargs):
    """
    Trigger thumbnail generation when experience entries change.
    """
    resume = instance.resume_section.resume
    
    if created:
        change_type = 'content_change'
        logger.info(f'New experience added to resume {resume.id}, triggering thumbnail generation')
    else:
        change_type = 'content_change'
        logger.info(f'Experience modified in resume {resume.id}, triggering thumbnail generation')
    
    # Generate thumbnail for the resume
    generate_resume_thumbnail(resume, change_type=change_type, source='experience_signal')


@receiver(post_save, sender=Project)
def handle_project_change(sender, instance, created, **kwargs):
    """
    Trigger thumbnail generation when project entries change.
    """
    resume = instance.resume_section.resume
    
    if created:
        change_type = 'content_change'
        logger.info(f'New project added to resume {resume.id}, triggering thumbnail generation')
    else:
        change_type = 'content_change'
        logger.info(f'Project modified in resume {resume.id}, triggering thumbnail generation')
    
    # Generate thumbnail for the resume
    generate_resume_thumbnail(resume, change_type=change_type, source='project_signal')


@receiver(post_save, sender=Certification)
def handle_certification_change(sender, instance, created, **kwargs):
    """
    Trigger thumbnail generation when certification entries change.
    """
    resume = instance.resume_section.resume
    
    if created:
        change_type = 'content_change'
        logger.info(f'New certification added to resume {resume.id}, triggering thumbnail generation')
    else:
        change_type = 'content_change'
        logger.info(f'Certification modified in resume {resume.id}, triggering thumbnail generation')
    
    # Generate thumbnail for the resume
    generate_resume_thumbnail(resume, change_type=change_type, source='certification_signal')


@receiver(post_save, sender=User)
def handle_user_profile_change(sender, instance, **kwargs):
    """
    Trigger thumbnail generation for user's base resume when profile changes.
    """
    try:
        # Find the user's base resume
        base_resume = instance.resume_set.get(base=True)
        logger.info(f'User profile changed, triggering thumbnail generation for base resume {base_resume.id}')
        
        # Generate thumbnail for the base resume
        generate_resume_thumbnail(base_resume, change_type='profile_change', source='user_profile_signal')
        
    except Resume.DoesNotExist:
        logger.debug(f'User {instance.id} does not have a base resume yet')
    except Exception as e:
        logger.exception(f'Error handling user profile change for user {instance.id}: {e}')


# Example of how to manually trigger thumbnail generation in API views
def manual_thumbnail_generation_example(resume_id):
    """
    Example of how to manually trigger thumbnail generation in API views.
    This can be used when you want explicit control over when thumbnails are generated.
    """
    from RESUME.models import Resume
    
    try:
        resume = Resume.objects.get(id=resume_id)
        
        # Manual thumbnail generation with specific change type
        updated_resume, error = generate_resume_thumbnail(
            resume=resume,
            change_type='manual_trigger',
            source='api_view'
        )
        
        if error:
            logger.error(f'Manual thumbnail generation failed for resume {resume_id}: {error}')
            return False
        else:
            logger.info(f'Manual thumbnail generation initiated for resume {resume_id}')
            return True
            
    except Resume.DoesNotExist:
        logger.error(f'Resume {resume_id} not found for manual thumbnail generation')
        return False
    except Exception as e:
        logger.exception(f'Unexpected error in manual thumbnail generation for resume {resume_id}: {e}')
        return False