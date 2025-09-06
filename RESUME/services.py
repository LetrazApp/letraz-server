import asyncio
import logging
from PROFILE.models import User
from django_socio_grpc import generics
from django_socio_grpc.exceptions import NotFound, InvalidArgument, GRPCException
from unicodedata import category

from CORE.models import Process, Country, Skill
from RESUME.models import Resume, ResumeSection, Experience, Education, Project, Certification, Proficiency
from JOB.proto_serialzers import ScrapeJobCallbackRequestSerializer, ScrapeJobResponseSerializer
from RESUME.proto_serializers import TailorResumeCallBackRequestProtoSerializer, TailorResumeCallBackResponseSerializer, \
    GenerateScreenshotCallBackResponseSerializer, GenerateScreenshotCallBackRequestProtoSerializer
from RESUME.utils import bulk_call_tailor_resume_for_the_job, generate_resume_thumbnail_async, index_resume_by_id_async
from letraz_server.settings import PROJECT_NAME
from django_socio_grpc.decorators import grpc_action
from google.protobuf.json_format import MessageToDict, MessageToJson
from letraz_server.contrib.sdks.knock import KnockSDK
from letraz_server import settings
__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)



class TailorResumeCallBackService(generics.GenericService):

    @grpc_action(
        request=TailorResumeCallBackRequestProtoSerializer,
        response=TailorResumeCallBackResponseSerializer,  # Empty response
    )
    async def TailorResumeCallBack(self, request, context):
        util_process_id = str(request.processId)
        logger.debug(f"[util id - {util_process_id}] [method: TailorResumeJobCallBack] --->Request: \n{MessageToJson(request)}")

        # Your implementation here
        process_qs = Process.objects.filter(util_id=request.processId)
        if not await process_qs.aexists():
            raise NotFound(f"No process found with that util process id: {request.processId}")
        process = await process_qs.afirst()
        in_progress_resume_qs = Resume.objects.filter(process=process)
        if not await in_progress_resume_qs.aexists():
            process.status = Process.ProcessStatus.Failed.value
            process.status_details = f"No resume found for the process: {process.id}"
            await process.asave()
            raise NotFound(f"No resume found for the process: {process.id}")
        if not request.data or not request.data.tailored_resume or not request.data.tailored_resume.sections:
            process.status = Process.ProcessStatus.Failed.value
            process.status_details = f"Must return a resume object with sections"
            await process.asave()
            raise InvalidArgument(f"Must return a resume object with sections")
        try:
            in_progress_resume: Resume = await in_progress_resume_qs.afirst()
            
            # Set a flag to skip thumbnail generation during bulk tailoring
            # This approach doesn't affect other users' resumes
            setattr(in_progress_resume, '_skip_thumbnail_generation', True)
            logger.debug(f"[util id - {util_process_id}] Set thumbnail generation skip flag for resume {in_progress_resume.id}")
            
            # Deleting all existing Resume section
            await in_progress_resume.resumesection_set.all().adelete()
            user = await User.objects.aget(id=in_progress_resume.user_id)
            resume_sections_data = MessageToDict(request.data.tailored_resume).get("sections")
            logger.debug(f"[util id - {util_process_id}] [method: TailorResumeJobCallBack] Resume sections data: {resume_sections_data}")
            for position, section in enumerate(resume_sections_data):
                if section.get('data'):
                    section_data = section.get('data')
                    if section.get('type') == 'Skill':
                        if section_data.get('skills'):
                            new_res_sec: ResumeSection = await in_progress_resume.resumesection_set.acreate(index=position, type=ResumeSection.ResumeSectionType.Skill.value)
                            for skill in section_data.get('skills'):
                                target_skill, created = await Skill.objects.aget_or_create(name=skill.get('skill').get('name'), category=skill.get('skill').get('category'))
                                target_proficiency, created = await new_res_sec.proficiency_set.aget_or_create(skill=target_skill)
                                skill_proficiency = skill.get('level')
                                if skill_proficiency:
                                    if str(skill_proficiency) in Proficiency.Level.values:
                                        target_proficiency.level = skill_proficiency
                                await target_proficiency.asave()
                    elif section.get('type') == 'Experience':
                        new_res_sec: ResumeSection = await in_progress_resume.resumesection_set.acreate(index=position, type=ResumeSection.ResumeSectionType.Experience.value)
                        experience = await Experience.objects.acreate(
                            resume_section=new_res_sec, user=user, company_name=section_data.get('company_name'),
                            job_title=section_data.get('job_title'), employment_type=Experience.EmploymentType.get_value_by_display(section_data.get('employment_type'))
                        )
                        experience.city = section_data.get('city')
                        if section_data.get('country'):
                            country, created = await Country.objects.aget_or_create(code=section_data.get('country').get('code'), name=section_data.get('country').get('name'))
                            experience.country = country
                        experience.started_from_month = section_data.get('started_from_month')
                        experience.started_from_year = section_data.get('started_from_year')
                        experience.finished_at_month = section_data.get('finished_at_month')
                        experience.finished_at_year = section_data.get('finished_at_year')
                        experience.current = section_data.get('current')
                        experience.description = section_data.get('description')
                        await experience.asave()
                    elif section.get('type') == 'Education':
                        new_res_sec: ResumeSection = await in_progress_resume.resumesection_set.acreate(index=position, type=ResumeSection.ResumeSectionType.Education.value)
                        education = await Education.objects.acreate(
                            resume_section=new_res_sec, user=user, institution_name=section_data.get('institution_name'),
                            field_of_study=section_data.get('field_of_study')
                        )
                        education.degree = section_data.get('degree')
                        if section_data.get('country'):
                            country, created = await Country.objects.aget_or_create(code=section_data.get('country').get('code'), name=section_data.get('country').get('name'))
                            education.country = country
                        education.started_from_month = section_data.get('started_from_month')
                        education.started_from_year = section_data.get('started_from_year')
                        education.finished_at_month = section_data.get('finished_at_month')
                        education.finished_at_year = section_data.get('finished_at_year')
                        education.current = section_data.get('current')
                        education.description = section_data.get('description')
                        await education.asave()
                    elif section.get('type') == 'Project':
                        new_res_sec: ResumeSection = await in_progress_resume.resumesection_set.acreate(index=position, type=ResumeSection.ResumeSectionType.Project.value)
                        project = await Project.objects.acreate(
                            resume_section=new_res_sec, user=user,
                            name=section_data.get('name')
                        )
                        project.category = section_data.get('category')
                        project.description = section_data.get('description')
                        project.role = section_data.get('role')
                        project.github_url = section_data.get('github_url')
                        project.live_url = section_data.get('live_url')
                        if section_data.get('skills_used'):
                            skills = section_data.get('skills_used')
                            for skill in skills:
                                await asyncio.create_task(project.add_skill_only_to_project(skill_name=skill.get('name'), skill_category=skill.get('category')))
                        project.started_from_month = section_data.get('started_from_month')
                        project.started_from_year = section_data.get('started_from_year')
                        project.finished_at_month = section_data.get('finished_at_month')
                        project.finished_at_year = section_data.get('finished_at_year')
                        project.current = section_data.get('current')
                        await project.asave()
                    elif section.get('type') == 'Certification':
                        new_res_sec: ResumeSection = await in_progress_resume.resumesection_set.acreate(index=position, type=ResumeSection.ResumeSectionType.Certification.value)
                        certification = await Certification.objects.acreate(
                            resume_section=new_res_sec, user=user,
                            name=section_data.get('name')
                        )
                        certification.issuing_organization = section_data.get('issuing_organization')
                        certification.issue_date = section_data.get('issue_date')
                        certification.credential_url = section_data.get('credential_url')
                        await certification.asave()
                    else:
                        pass
                        
            in_progress_resume.status = Resume.Status.Success.value
            
            # Clear the skip flag before saving to ensure normal signal behavior for future updates
            if hasattr(in_progress_resume, '_skip_thumbnail_generation'):
                delattr(in_progress_resume, '_skip_thumbnail_generation')
            
            await in_progress_resume.asave()
            index_resume_by_id_async(in_progress_resume.id)

            # Trigger thumbnail generation ONCE after successful resume tailoring
            try:
                # Use proper async pattern with background threading and connection management
                generate_resume_thumbnail_async(in_progress_resume)
                logger.info(f"[util id - {util_process_id}] Thumbnail generation triggered for tailored resume {in_progress_resume.id}")
            except Exception as thumb_e:
                # Don't fail the main process if thumbnail generation fails
                logger.warning(f"[util id - {util_process_id}] Thumbnail generation failed for resume {in_progress_resume.id}: {thumb_e}")

            # Notify user that resume tailoring succeeded
            try:
                knock = KnockSDK(api_key=settings.KNOCK_API_KEY)
                if knock.is_available() and in_progress_resume.user_id:
                    knock.trigger_workflow(
                        workflow_key="resume-tailored",
                        user_id=str(in_progress_resume.user_id),
                        data={
                            "resume_id": in_progress_resume.id,
                            "job_id": in_progress_resume.job_id,
                            "cta_url": f"{settings.CLIENT_URL}/app/craft/resumes/{in_progress_resume.id}",
                            "job_title": in_progress_resume.job.title if in_progress_resume.job else None,
                            "company_name": in_progress_resume.job.company_name if in_progress_resume.job else None,
                        }
                    )
                elif not knock.is_available():
                    logger.warning(f"Knock not available; skipping resume-tailored notification for resume {in_progress_resume.id}")
            except Exception:
                logger.exception(f"Failed to send resume-tailored notification for resume {in_progress_resume.id}")

        except Exception as e:
            process.status = Process.ProcessStatus.Failed.value
            error_msg = f'[util id - {util_process_id}] [method: ScrapeJobCallBack] {str(e)}'
            logger.exception(error_msg)
            process.status_details = error_msg[:249]
            await process.asave()
            # Notify user that resume tailoring failed
            try:
                knock = KnockSDK(api_key=settings.KNOCK_API_KEY)
                if knock.is_available() and in_progress_resume_qs:
                    in_progress_resume = await in_progress_resume_qs.afirst()
                    if in_progress_resume and in_progress_resume.user_id:
                        knock.trigger_workflow(
                            workflow_key="resume-tailor-failed",
                            user_id=str(in_progress_resume.user_id),
                            data={
                                "resume_id": in_progress_resume.id if in_progress_resume else None,
                                "job_id": in_progress_resume.job_id if in_progress_resume else None,
                                "reason": str(e),
                                # Placeholder report URL until provided
                                "report_url": f"{settings.CLIENT_URL}/app/support?resumeId={in_progress_resume.id}" if settings.CLIENT_URL else None,
                                "job_title": in_progress_resume.job.title if in_progress_resume.job else None,
                                "company_name": in_progress_resume.job.company_name if in_progress_resume.job else None,
                            }
                        )
                elif not knock.is_available():
                    logger.warning("Knock not available; skipping resume-tailor-failed notification")
            except Exception:
                logger.exception("Failed to send resume-tailor-failed notification")
            raise GRPCException(str(e))
        return ScrapeJobResponseSerializer("OK").message



class GenerateScreenshotCallBackService(generics.GenericService):

    @grpc_action(
        request=GenerateScreenshotCallBackRequestProtoSerializer,
        response=GenerateScreenshotCallBackResponseSerializer,  # Empty response
    )
    async def GenerateScreenshotCallBack(self, request, context):
        util_process_id = str(request.processId)
        logger.debug(f"[util id - {util_process_id}] [method: GenerateScreenshotCallBack] --->Request: \n{MessageToJson(request)}")

        # Your implementation here
        process_qs = Process.objects.filter(util_id=request.processId)
        if not await process_qs.aexists():
            raise NotFound(f"No process found with that util process id: {request.processId}")
        process = await process_qs.afirst()
        thumbnail_in_progress_resume_qs = Resume.objects.filter(thumbnail_process=process)
        if not await thumbnail_in_progress_resume_qs.aexists():
            process.status = Process.ProcessStatus.Failed.value
            process.status_details = f"No resume found for the process: {process.id}"
            await process.asave()
            raise NotFound(f"No resume found for the process: {process.id}")
        if not request.data or not request.data.screenshot_url :
            process.status = Process.ProcessStatus.Failed.value
            process.status_details = f"Must return a data object with screenshot_url in the response"
            await process.asave()
            raise InvalidArgument(f"Must return a data object with screenshot_url in the response")
        try:
            thumbnail_in_progress_resume: Resume = await thumbnail_in_progress_resume_qs.afirst()
            request_data = MessageToDict(request).get("data")
            thumbnail_in_progress_resume.thumbnail = request_data.get("screenshotUrl")
            await thumbnail_in_progress_resume.asave()
            process.status = Process.ProcessStatus.Success.value
            process.status_details = f"Screenshot URL generated"[:249]
            await process.asave()
            index_resume_by_id_async(thumbnail_in_progress_resume.id)
        except Exception as e:
            process.status = Process.ProcessStatus.Failed.value
            error_msg = f'[util id - {util_process_id}] [method: ScrapeJobCallBack] {str(e)}'
            logger.exception(error_msg)
            process.status_details = error_msg[:249]
            await process.asave()
            raise GRPCException(str(e))
        return ScrapeJobResponseSerializer("OK").message
