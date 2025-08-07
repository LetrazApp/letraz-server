import logging
import algoliasearch_django as algoliasearch
from algoliasearch_django import AlgoliaIndex
from RESUME.models import Resume, ResumeSection
from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


class ResumeIndex(AlgoliaIndex):
    fields = [
        'id',
        'base', 
        'version',
        'status'
    ]
    
    def get_raw_record(self, instance, **kwargs):
        """Override to include all computed fields"""
        # Get the basic record
        record = super().get_raw_record(instance, **kwargs)
        
        # Add all computed fields manually
        record.update({
            'user_id': self.get_user_id(instance),
            'user_full_name': self.get_user_full_name(instance),
            'user_email': self.get_user_email(instance),
            'job_id': self.get_job_id(instance),
            'job_title': self.get_job_title(instance),
            'job_company': self.get_job_company(instance),
            'education_data': self.get_education_data(instance),
            'experience_data': self.get_experience_data(instance),
            'skills_data': self.get_skills_data(instance),
            'projects_data': self.get_projects_data(instance),
            'certifications_data': self.get_certifications_data(instance),
            'created_at': self.get_created_at(instance),
            'updated_at': self.get_updated_at(instance)
        })
        
        return record
    
    settings = {
        'searchableAttributes': [
            'user_full_name',
            'user_email', 
            'job_title',
            'job_company',
            'education_data.institution_name',
            'education_data.field_of_study',
            'education_data.degree',
            'experience_data.company_name',
            'experience_data.job_title',
            'experience_data.description',
            'skills_data.skill_name',
            'skills_data.skill_category',
            'projects_data.name',
            'projects_data.description',
            'projects_data.category',
            'certifications_data.name',
            'certifications_data.issuing_organization'
        ],
        'attributesForFaceting': [
            'user_id',
            'job_id',
            'base',
            'status',
            'skills_data.skill_category',
            'education_data.country',
            'experience_data.employment_type',
            'experience_data.country'
        ]
    }
    
    def get_queryset(self):
        """
        Optimize queryset with proper prefetch to avoid N+1 queries.
        Only index non-base resumes (base=False) that are successfully processed (status=Success).
        """
        return Resume.objects.filter(
            base=False,  # Exclude base resumes from indexing
            status=Resume.Status.Success  # Only include successfully processed resumes
        ).select_related(
            'user', 'job', 'process'
        ).prefetch_related(
            'resumesection_set__education',
            'resumesection_set__experience', 
            'resumesection_set__proficiency_set__skill',
            'resumesection_set__project',
            'resumesection_set__certification'
        )
    
    def get_user_id(self, instance):
        try:
            return instance.user.id if instance.user else None
        except Exception as e:
            logger.exception(f"Error getting user_id: {e}")
            return None
    
    def get_user_full_name(self, instance):
        try:
            return instance.user.get_full_name() if instance.user else ""
        except Exception as e:
            logger.exception(f"Error getting user_full_name: {e}")
            return ""
    
    def get_user_email(self, instance):
        try:
            return instance.user.email if instance.user else ""
        except Exception as e:
            logger.exception(f"Error getting user_email: {e}")
            return ""
    
    def get_job_id(self, instance):
        return instance.job.id if instance.job else None
    
    def get_job_title(self, instance):
        return instance.job.title if instance.job else ""
    
    def get_job_company(self, instance):
        return instance.job.company_name if instance.job else ""
    
    def get_education_data(self, instance):
        """Extract all education data from resume sections"""
        try:
            education_list = []
            for section in instance.resumesection_set.filter(type=ResumeSection.ResumeSectionType.Education):
                if hasattr(section, 'education'):
                    edu = section.education
                    education_list.append({
                        'id': str(edu.id),
                        'institution_name': edu.institution_name,
                        'field_of_study': edu.field_of_study,
                        'degree': edu.degree or "",
                        'country': edu.country.name if edu.country else "",
                        'started_from': f"{edu.started_from_month}/{edu.started_from_year}" if edu.started_from_month and edu.started_from_year else "",
                        'finished_at': f"{edu.finished_at_month}/{edu.finished_at_year}" if edu.finished_at_month and edu.finished_at_year else "",
                        'current': edu.current,
                        'description': edu.description or ""
                    })
            logger.debug(f"Education data for {instance.id}: {education_list}")
            return education_list
        except Exception as e:
            logger.exception(f"Error getting education_data for {instance.id}: {e}")
            return []
    
    def get_experience_data(self, instance):
        """Extract all experience data from resume sections"""
        try:
            experience_list = []
            for section in instance.resumesection_set.filter(type=ResumeSection.ResumeSectionType.Experience):
                if hasattr(section, 'experience'):
                    exp = section.experience
                    experience_list.append({
                        'id': str(exp.id),
                        'company_name': exp.company_name,
                        'job_title': exp.job_title,
                        'employment_type': exp.get_employment_type_display(),
                        'city': exp.city or "",
                        'country': exp.country.name if exp.country else "",
                        'started_from': f"{exp.started_from_month}/{exp.started_from_year}" if exp.started_from_month and exp.started_from_year else "",
                        'finished_at': f"{exp.finished_at_month}/{exp.finished_at_year}" if exp.finished_at_month and exp.finished_at_year else "",
                        'current': exp.current,
                        'description': exp.description or ""
                    })
            logger.debug(f"Experience data for {instance.id}: {experience_list}")
            return experience_list
        except Exception as e:
            logger.exception(f"Error getting experience_data for {instance.id}: {e}")
            return []
    
    def get_skills_data(self, instance):
        """Extract all skills data from resume sections"""
        skills_list = []
        for section in instance.resumesection_set.filter(type=ResumeSection.ResumeSectionType.Skill):
            for proficiency in section.proficiency_set.all():
                skills_list.append({
                    'id': str(proficiency.id),
                    'skill_name': proficiency.skill.name,
                    'skill_category': proficiency.skill.category or "",
                    'level': proficiency.get_level_display() if proficiency.level else ""
                })
        return skills_list
    
    def get_projects_data(self, instance):
        """Extract all projects data from resume sections"""
        projects_list = []
        for section in instance.resumesection_set.filter(type=ResumeSection.ResumeSectionType.Project):
            if hasattr(section, 'project'):
                proj = section.project
                projects_list.append({
                    'id': str(proj.id),
                    'name': proj.name,
                    'category': proj.category or "",
                    'description': proj.description or "",
                    'role': proj.role or "",
                    'github_url': proj.github_url or "",
                    'live_url': proj.live_url or "",
                    'started_from': f"{proj.started_from_month}/{proj.started_from_year}" if proj.started_from_month and proj.started_from_year else "",
                    'finished_at': f"{proj.finished_at_month}/{proj.finished_at_year}" if proj.finished_at_month and proj.finished_at_year else "",
                    'current': proj.current,
                    'skills_used': [skill.name for skill in proj.skills_used.all()]
                })
        return projects_list
    
    def get_certifications_data(self, instance):
        """Extract all certifications data from resume sections"""
        certifications_list = []
        for section in instance.resumesection_set.filter(type=ResumeSection.ResumeSectionType.Certification):
            if hasattr(section, 'certification'):
                cert = section.certification
                certifications_list.append({
                    'id': str(cert.id),
                    'name': cert.name,
                    'issuing_organization': cert.issuing_organization or "",
                    'issue_date': cert.issue_date.isoformat() if cert.issue_date else "",
                    'credential_url': cert.credential_url or ""
                })
        return certifications_list
    
    def get_created_at(self, instance):
        # Resume model doesn't have created_at, but we can use user's date_joined or similar
        return instance.user.date_joined.isoformat() if instance.user and hasattr(instance.user, 'date_joined') else ""
    
    def get_updated_at(self, instance):
        # Resume model doesn't have updated_at, but we can use user's last_login or similar
        return instance.user.last_login.isoformat() if instance.user and instance.user.last_login else ""


algoliasearch.register(Resume, ResumeIndex)
