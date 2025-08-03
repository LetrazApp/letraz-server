from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from RESUME.models import Resume, Education, Experience, Proficiency, Project, Certification

# Only import algoliasearch if it's available
if getattr(settings, 'ALGOLIA_STATUS', 'DISABLED') == 'OPERATIONAL':
    try:
        import algoliasearch_django as algoliasearch
        ALGOLIA_AVAILABLE = True
    except ImportError:
        ALGOLIA_AVAILABLE = False
else:
    ALGOLIA_AVAILABLE = False


@receiver([post_save, post_delete], sender=Resume)
def update_resume_index_on_resume_change(sender, instance, **kwargs):
    """Handle Resume changes - update or delete from Algolia based on base status and processing status"""
    if not ALGOLIA_AVAILABLE:
        return
        
    try:
        if instance.base or instance.status != Resume.Status.Success:
            # Remove from Algolia if this is a base resume OR not successfully processed
            algoliasearch.delete_record(instance)
        else:
            # If this is not a base resume AND successfully processed, update it in Algolia
            algoliasearch.save_record(instance)
    except Exception as e:
        print(f"Error updating Algolia index for Resume {instance.id}: {e}")


@receiver([post_save, post_delete], sender=Education)
def update_resume_index_on_education_change(sender, instance, **kwargs):
    """Update Resume in Algolia when Education is modified (only for non-base resumes)"""
    try:
        resume = instance.resume_section.resume
        # Only update if this is not a base resume AND status is Success AND Algolia is available
        if ALGOLIA_AVAILABLE and not resume.base and resume.status == Resume.Status.Success:
            if kwargs.get('created', False) or kwargs.get('signal').__name__ == 'post_save':
                algoliasearch.save_record(resume)
            elif kwargs.get('signal').__name__ == 'post_delete':
                algoliasearch.save_record(resume)
    except Exception as e:
        # Log error but don't fail the operation
        print(f"Error updating Algolia index for Resume {instance.resume_section.resume.id} after Education change: {e}")


@receiver([post_save, post_delete], sender=Experience)
def update_resume_index_on_experience_change(sender, instance, **kwargs):
    """Update Resume in Algolia when Experience is modified (only for non-base resumes)"""
    try:
        resume = instance.resume_section.resume
        # Only update if this is not a base resume AND status is Success AND Algolia is available
        if ALGOLIA_AVAILABLE and not resume.base and resume.status == Resume.Status.Success:
            if kwargs.get('created', False) or kwargs.get('signal').__name__ == 'post_save':
                algoliasearch.save_record(resume)
            elif kwargs.get('signal').__name__ == 'post_delete':
                algoliasearch.save_record(resume)
    except Exception as e:
        print(f"Error updating Algolia index for Resume {instance.resume_section.resume.id} after Experience change: {e}")


@receiver([post_save, post_delete], sender=Proficiency)
def update_resume_index_on_proficiency_change(sender, instance, **kwargs):
    """Update Resume in Algolia when Proficiency (Skills) is modified (only for non-base resumes)"""
    try:
        resume = instance.resume_section.resume
        # Only update if this is not a base resume AND status is Success AND Algolia is available
        if ALGOLIA_AVAILABLE and not resume.base and resume.status == Resume.Status.Success:
            if kwargs.get('created', False) or kwargs.get('signal').__name__ == 'post_save':
                algoliasearch.save_record(resume)
            elif kwargs.get('signal').__name__ == 'post_delete':
                algoliasearch.save_record(resume)
    except Exception as e:
        print(f"Error updating Algolia index for Resume {instance.resume_section.resume.id} after Proficiency change: {e}")


@receiver([post_save, post_delete], sender=Project)
def update_resume_index_on_project_change(sender, instance, **kwargs):
    """Update Resume in Algolia when Project is modified (only for non-base resumes)"""
    try:
        resume = instance.resume_section.resume
        # Only update if this is not a base resume AND status is Success AND Algolia is available
        if ALGOLIA_AVAILABLE and not resume.base and resume.status == Resume.Status.Success:
            if kwargs.get('created', False) or kwargs.get('signal').__name__ == 'post_save':
                algoliasearch.save_record(resume)
            elif kwargs.get('signal').__name__ == 'post_delete':
                algoliasearch.save_record(resume)
    except Exception as e:
        print(f"Error updating Algolia index for Resume {instance.resume_section.resume.id} after Project change: {e}")


@receiver([post_save, post_delete], sender=Certification)
def update_resume_index_on_certification_change(sender, instance, **kwargs):
    """Update Resume in Algolia when Certification is modified (only for non-base resumes)"""
    try:
        resume = instance.resume_section.resume
        # Only update if this is not a base resume AND status is Success AND Algolia is available
        if ALGOLIA_AVAILABLE and not resume.base and resume.status == Resume.Status.Success:
            if kwargs.get('created', False) or kwargs.get('signal').__name__ == 'post_save':
                algoliasearch.save_record(resume)
            elif kwargs.get('signal').__name__ == 'post_delete':
                algoliasearch.save_record(resume)
    except Exception as e:
        print(f"Error updating Algolia index for Resume {instance.resume_section.resume.id} after Certification change: {e}")