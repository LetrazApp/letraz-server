import json
import logging
import re
import uuid
from http import HTTPStatus
from django.db.models import QuerySet
from django.db.models import Q
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from google.protobuf.json_format import MessageToDict
from CORE.models import Process, Country, Skill
from CORE.serializers import ErrorSerializer
from JOB.models import Job
from JOB.serializers import JobFullSerializer, JobSerializer
from PROFILE.models import User
from RESUME.models import Resume, Education, Experience, ResumeSection, Proficiency, Project, Certification
from RESUME.serializers import ResumeShortSerializer, ResumeFullSerializer, EducationFullSerializer, \
    ExperienceFullSerializer, EducationUpsertSerializer, ExperienceUpsertSerializer, ProficiencySerializer, \
    ProjectSerializer, ResumeSkillUpsertSerializer, ProjectUpsertSerializer, CertificationSerializer, \
    CertificationUpsertSerializer, SectionRearrangeSerializer, BaseResumeFullSerializer, BaseResumeUtilSerializer, \
    ResumeReplaceSerializer
from RESUME.utils import (
    call_tailor_resume_util_service,
    index_resume_by_id_async,
    disable_thumbnail_generation,
    generate_resume_thumbnail_async,
)
from letraz_server import settings
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from letraz_server.settings import PROJECT_NAME
from letraz_server.conf.grpc_client.utils import letraz_utils_pb2_grpc
from letraz_server.conf.grpc_client.utils import letraz_utils_pb2
from google.protobuf.json_format import ParseDict
from RESUME.serializers import ResumeSectionFullSerializer

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


# Resume CRUD ViewSets
@extend_schema(tags=['Resume object'])
class ResumeViewSets(viewsets.GenericViewSet):
    def __init__(self, *args, **kwargs):
        self.authenticated_user: User | None = None
        self.error: ErrorResponse | None = None
        super(ResumeViewSets, self).__init__(*args, **kwargs)

    def __set_meta(self, request):
        """
        Retrieve check and set authenticated user for Resume CRUD
        """
        # Ownership Check for all types of API
        self.authenticated_user: User = request.user

    @extend_schema(
        responses={200: ResumeShortSerializer(many=True), 500: ErrorSerializer},
        summary="Get all resume"
    )
    def list(self, request):
        """
        Gives a list of all resumes for the user. If no resumes are found, an empty list is returned.
        """
        self.__set_meta(request)
        return Response(ResumeShortSerializer(self.authenticated_user.resume_set.all(), many=True).data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='Resume ID', required=True, location=OpenApiParameter.PATH,
                             type=str)
        ],
        responses={200: ResumeFullSerializer, 500: ErrorSerializer},
        summary="Get resume by id"
    )
    def retrieve(self, request, pk):
        """
        Gives a resume for the user by produced id or gives base resume of the user if id is provided as `base`.
        """
        self.__set_meta(request)
        if pk == 'base':
            base_resume, created = self.authenticated_user.resume_set.get_or_create(base=True)
            resume_id = base_resume.id
        else:
            resume_id = pk
        resume_by_user_and_resume_id_qs: QuerySet[Resume] = self.authenticated_user.resume_set.filter(id=resume_id)
        if resume_by_user_and_resume_id_qs.exists():
            return Response(ResumeFullSerializer(resume_by_user_and_resume_id_qs.first()).data)
        else:
            return ErrorResponse(
                code=ErrorCode.NOT_FOUND, message='Resume not found!', details={'resume': resume_id}
            ).response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='Resume ID', required=True, location=OpenApiParameter.PATH,
                             type=str)
        ],
        request=ResumeReplaceSerializer,
        responses={200: ResumeFullSerializer, 400: ErrorSerializer, 404: ErrorSerializer, 500: ErrorSerializer},
        summary="Replace resume sections",
        description="Replace all sections of a resume with the provided ordered list of sections."
    )
    def update(self, request, pk=None):
        self.__set_meta(request)
        # Resolve resume
        if pk == 'base':
            resume, _ = self.authenticated_user.resume_set.get_or_create(base=True)
        else:
            resume_qs = self.authenticated_user.resume_set.filter(id=pk)
            if not resume_qs.exists():
                return ErrorResponse(
                    code=ErrorCode.NOT_FOUND, message='Resume not found!', details={'resume': pk}
                ).response
            resume = resume_qs.first()

        # Validate payload
        serializer = ResumeReplaceSerializer(data=request.data)
        if not serializer.is_valid():
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST, message='Invalid request data.',
                details=serializer.errors, extra={'data': request.data}
            ).response

        sections_payload = serializer.validated_data['sections']

        try:
            with transaction.atomic():
                # Avoid spamming thumbnail generation while bulk editing
                with disable_thumbnail_generation():
                    # Mark resume to skip any signal-based thumbnail generation
                    setattr(resume, '_skip_thumbnail_generation', True)

                    # Remove all existing sections and cascades
                    resume.resumesection_set.all().delete()

                    # Prepare bulk creation containers
                    new_sections: list[ResumeSection] = []
                    # Keep mapping of enumerated index -> created section id for each type as we preserve original indices
                    experience_payloads: list[dict] = []
                    education_payloads: list[dict] = []
                    project_payloads: list[dict] = []
                    project_skills_used_map: dict[str, list[dict]] = {}
                    certification_payloads: list[dict] = []

                    # Skills handling
                    explicit_skill_sections: dict[str, list[dict]] = {}  # section_id -> list of skill items
                    first_skill_section_id: str | None = None
                    project_skill_items: list[dict] = []  # list of {'name','category'} from projects

                    # 1) Build all sections (pre-generate UUIDs) and organize payloads
                    for index, section in enumerate(sections_payload):
                        section_type = section.get('type')
                        section_data = section.get('data') or {}

                        if section_type == 'Skill':
                            skills_list = section_data.get('skills') or []
                            if not skills_list:
                                # Skip creating empty Skill sections (matches previous behavior)
                                continue
                            sec_id = uuid.uuid4()
                            sec = ResumeSection(id=sec_id, resume=resume, index=index,
                                                type=ResumeSection.ResumeSectionType.Skill.value)
                            new_sections.append(sec)
                            explicit_skill_sections[str(sec_id)] = skills_list
                            if not first_skill_section_id:
                                first_skill_section_id = str(sec_id)
                            continue

                        if section_type == 'Experience':
                            sec_id = uuid.uuid4()
                            new_sections.append(ResumeSection(
                                id=sec_id, resume=resume, index=index,
                                type=ResumeSection.ResumeSectionType.Experience.value
                            ))
                            payload = dict(section_data)
                            payload['user'] = self.authenticated_user.id
                            payload['resume_section'] = sec_id
                            experience_payloads.append(payload)
                            continue

                        if section_type == 'Education':
                            sec_id = uuid.uuid4()
                            new_sections.append(ResumeSection(
                                id=sec_id, resume=resume, index=index,
                                type=ResumeSection.ResumeSectionType.Education.value
                            ))
                            payload = dict(section_data)
                            payload['user'] = self.authenticated_user.id
                            payload['resume_section'] = sec_id
                            education_payloads.append(payload)
                            continue

                        if section_type == 'Project':
                            sec_id = uuid.uuid4()
                            new_sections.append(ResumeSection(
                                id=sec_id, resume=resume, index=index,
                                type=ResumeSection.ResumeSectionType.Project.value
                            ))
                            payload = dict(section_data)
                            skills_used = payload.pop('skills_used', None)
                            payload['user'] = self.authenticated_user.id
                            payload['resume_section'] = sec_id
                            project_payloads.append(payload)
                            if isinstance(skills_used, list):
                                project_skills_used_map[str(sec_id)] = skills_used
                                # Collect skills for global resolution
                                for sk in skills_used:
                                    if sk:
                                        project_skill_items.append({'name': sk.get('name'), 'category': sk.get('category')})
                            continue

                        if section_type == 'Certification':
                            sec_id = uuid.uuid4()
                            new_sections.append(ResumeSection(
                                id=sec_id, resume=resume, index=index,
                                type=ResumeSection.ResumeSectionType.Certification.value
                            ))
                            payload = dict(section_data)
                            payload['user'] = self.authenticated_user.id
                            payload['resume_section'] = sec_id
                            certification_payloads.append(payload)
                            continue

                        # Unknown types: ignore

                    # If there are project skills but no explicit Skill section, create one at the end
                    if project_skill_items and not first_skill_section_id:
                        sec_id = uuid.uuid4()
                        next_index = (max([s.index for s in new_sections], default=-1) + 1)
                        new_sections.append(ResumeSection(
                            id=sec_id, resume=resume, index=next_index,
                            type=ResumeSection.ResumeSectionType.Skill.value
                        ))
                        first_skill_section_id = str(sec_id)

                    # 2) Bulk create all sections
                    if new_sections:
                        ResumeSection.objects.bulk_create(new_sections, batch_size=500)

                    # 3) Validate and bulk create children
                    # Experience
                    if experience_payloads:
                        exp_ser = ExperienceUpsertSerializer(data=experience_payloads, many=True)
                        if not exp_ser.is_valid():
                            return ErrorResponse(
                                code=ErrorCode.INVALID_REQUEST,
                                message='Invalid Experience data provided.',
                                details=exp_ser.errors,
                                extra={'data': experience_payloads}
                            ).response
                        exp_instances = [
                            Experience(**item) for item in exp_ser.validated_data
                        ]
                        if exp_instances:
                            Experience.objects.bulk_create(exp_instances, batch_size=500)

                    # Education
                    if education_payloads:
                        edu_ser = EducationUpsertSerializer(data=education_payloads, many=True)
                        if not edu_ser.is_valid():
                            return ErrorResponse(
                                code=ErrorCode.INVALID_REQUEST,
                                message='Invalid Education data provided.',
                                details=edu_ser.errors,
                                extra={'data': education_payloads}
                            ).response
                        edu_instances = [
                            Education(**item) for item in edu_ser.validated_data
                        ]
                        if edu_instances:
                            Education.objects.bulk_create(edu_instances, batch_size=500)

                    # Project
                    created_projects_by_section: dict[str, Project] = {}
                    if project_payloads:
                        prj_ser = ProjectUpsertSerializer(data=project_payloads, many=True)
                        if not prj_ser.is_valid():
                            return ErrorResponse(
                                code=ErrorCode.INVALID_REQUEST,
                                message='Invalid Project data provided.',
                                details=prj_ser.errors,
                                extra={'data': project_payloads}
                            ).response
                        prj_instances: list[Project] = []
                        for item in prj_ser.validated_data:
                            # Pre-assign UUID so we can reference for M2M
                            prj_id = uuid.uuid4()
                            inst = Project(id=prj_id, **item)
                            prj_instances.append(inst)
                        if prj_instances:
                            Project.objects.bulk_create(prj_instances, batch_size=500)
                            for inst in prj_instances:
                                created_projects_by_section[str(inst.resume_section_id)] = inst

                    # Certification
                    if certification_payloads:
                        cert_ser = CertificationUpsertSerializer(data=certification_payloads, many=True)
                        if not cert_ser.is_valid():
                            return ErrorResponse(
                                code=ErrorCode.INVALID_REQUEST,
                                message='Invalid Certification data provided.',
                                details=cert_ser.errors,
                                extra={'data': certification_payloads}
                            ).response
                        cert_instances = [
                            Certification(**item) for item in cert_ser.validated_data
                        ]
                        if cert_instances:
                            Certification.objects.bulk_create(cert_instances, batch_size=500)

                    # 4) Resolve Skills once
                    # Gather unique skills from explicit skill sections and project skills
                    unique_skill_keys: set[tuple[str | None, str | None]] = set()
                    # explicit skills
                    for sec_id, skills_list in explicit_skill_sections.items():
                        for skill_item in skills_list:
                            if not skill_item:
                                continue
                            sk_info = (skill_item or {}).get('skill') or {}
                            sk_name = sk_info.get('name')
                            if not sk_name:
                                continue
                            unique_skill_keys.add((sk_name, sk_info.get('category')))
                    # project skills
                    for sk in project_skill_items:
                        if not sk or not sk.get('name'):
                            continue
                        unique_skill_keys.add((sk.get('name'), sk.get('category')))

                    skill_lookup: dict[tuple[str | None, str | None], Skill] = {}
                    if unique_skill_keys:
                        names = list({n for (n, _c) in unique_skill_keys if n})
                        cats = list({c for (_n, c) in unique_skill_keys})
                        non_null_cats = [c for c in cats if c is not None]
                        has_null_cat = any(c is None for c in cats)

                        name_q = Q(name__in=names)
                        cat_q = Q()
                        if non_null_cats:
                            cat_q |= Q(category__in=non_null_cats)
                        if has_null_cat:
                            cat_q |= Q(category__isnull=True)

                        existing_skills = Skill.objects.filter(name_q & cat_q) if (names and (non_null_cats or has_null_cat)) else Skill.objects.none()
                        for s in existing_skills:
                            skill_lookup[(s.name, s.category)] = s
                        missing = [
                            Skill(name=name, category=cat)
                            for (name, cat) in unique_skill_keys
                            if (name, cat) not in skill_lookup
                        ]
                        if missing:
                            Skill.objects.bulk_create(missing, batch_size=500)
                            for s in missing:
                                skill_lookup[(s.name, s.category)] = s

                    # 5) Bulk create Proficiencies for explicit Skill sections
                    prof_instances: list[Proficiency] = []
                    for sec_id, skills_list in explicit_skill_sections.items():
                        for skill_item in skills_list:
                            if not skill_item:
                                continue
                            sk_info = (skill_item or {}).get('skill') or {}
                            sk_name = sk_info.get('name')
                            if not sk_name:
                                continue
                            sk_cat = sk_info.get('category')
                            level = (skill_item or {}).get('level')
                            level_val = level if level and str(level) in Proficiency.Level.values else None
                            skill_obj = skill_lookup.get((sk_name, sk_cat))
                            if not skill_obj:
                                continue
                            prof_instances.append(
                                Proficiency(resume_section_id=sec_id, skill_id=skill_obj.id, level=level_val)
                            )

                    # Add project skills to the first skill section (or the implicit one we created)
                    if first_skill_section_id and project_skill_items:
                        # Avoid duplicates that may already be added via explicit sections
                        existing_pairs = set()
                        for p in prof_instances:
                            if str(p.resume_section_id) == str(first_skill_section_id):
                                # For safety capture against duplicates by skill id
                                existing_pairs.add(p.skill_id)
                        for sk in project_skill_items:
                            name = sk.get('name')
                            if not name:
                                continue
                            cat = sk.get('category')
                            skill_obj = skill_lookup.get((name, cat))
                            if not skill_obj:
                                continue
                            if skill_obj.id in existing_pairs:
                                continue
                            prof_instances.append(
                                Proficiency(resume_section_id=first_skill_section_id, skill_id=skill_obj.id, level=None)
                            )

                    if prof_instances:
                        Proficiency.objects.bulk_create(prof_instances, batch_size=500, ignore_conflicts=True)

                    # 6) Bulk create Project.skills_used M2M through rows
                    if created_projects_by_section and project_skills_used_map:
                        through_model = Project.skills_used.through
                        m2m_instances = []
                        for sec_id, skills_used in project_skills_used_map.items():
                            prj = created_projects_by_section.get(str(sec_id))
                            if not prj:
                                continue
                            for sk in skills_used:
                                if not sk or not sk.get('name'):
                                    continue
                                skill_obj = skill_lookup.get((sk.get('name'), sk.get('category')))
                                if not skill_obj:
                                    continue
                                m2m_instances.append(through_model(project_id=prj.id, skill_id=skill_obj.id))
                        if m2m_instances:
                            through_model.objects.bulk_create(m2m_instances, batch_size=500, ignore_conflicts=True)

                    # Clean skip flag before leaving transaction
                    if hasattr(resume, '_skip_thumbnail_generation'):
                        delattr(resume, '_skip_thumbnail_generation')

            # Kick off background jobs after successful commit
            index_resume_by_id_async(resume.id)
            generate_resume_thumbnail_async(resume)

            return Response(ResumeFullSerializer(resume).data)

        except ValueError as ve:
            error_response = ErrorResponse(
                code=ErrorCode.INVALID_REQUEST,
                message=str(ve),
                status_code=status.HTTP_400_BAD_REQUEST,
                details={'data': request.data}
            )
            logger.exception(f"{error_response.uuid} -> Invalid request while replacing resume: {ve}")
            return error_response.response
        except Exception as e:
            error_response = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message='Unexpected error occurred while replacing resume.',
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f"{error_response.uuid} -> Exception while replacing resume: {e}")
            return error_response.response

    @extend_schema(
        request=SectionRearrangeSerializer,
        responses={200: ResumeFullSerializer, 400: ErrorSerializer, 404: ErrorSerializer, 500: ErrorSerializer},
        summary="Rearrange resume sections",
        description="Rearrange the order of sections in a resume by providing an array of section IDs in the desired order."
    )
    @action(detail=True, methods=['put'], url_path='sections/rearrange')
    def rearrange_sections(self, request, pk=None):
        """
        Rearrange the order of sections in a resume.
        Accepts an array of section IDs and updates the order of sections in the resume.
        """
        self.__set_meta(request)
        
        # Get the resume
        if pk == 'base':
            resume, created = self.authenticated_user.resume_set.get_or_create(base=True)
        else:
            resume_qs = self.authenticated_user.resume_set.filter(id=pk)
            if not resume_qs.exists():
                return ErrorResponse(
                    code=ErrorCode.NOT_FOUND, message='Resume not found!', details={'resume': pk}
                ).response
            resume = resume_qs.first()
        
        # Validate request data
        serializer = SectionRearrangeSerializer(data=request.data)
        if not serializer.is_valid():
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST, message='Invalid request data.',
                details=serializer.errors, extra={'data': request.data}
            ).response
        
        section_ids = serializer.validated_data['section_ids']
        
        try:
            # Get all existing sections for the resume
            existing_sections = resume.resumesection_set.all()
            existing_section_ids = set(str(section.id) for section in existing_sections)
            provided_section_ids = set(str(section_id) for section_id in section_ids)
            
            # Validate that all provided section IDs belong to the resume
            invalid_section_ids = provided_section_ids - existing_section_ids
            if invalid_section_ids:
                return ErrorResponse(
                    code=ErrorCode.INVALID_REQUEST, 
                    message='Some section IDs do not belong to this resume.',
                    details={'invalid_section_ids': list(invalid_section_ids)}
                ).response
            
            # Check if all existing sections are included in the request
            missing_section_ids = existing_section_ids - provided_section_ids
            if missing_section_ids:
                return ErrorResponse(
                    code=ErrorCode.INVALID_REQUEST,
                    message='Some existing sections are missing from the request.',
                    details={'missing_section_ids': list(missing_section_ids)}
                ).response
            
            # Update the section order
            with transaction.atomic():
                # Create a mapping of section ID to section object
                section_map = {str(section.id): section for section in existing_sections}

                # Temporarily disable thumbnail generation signals during bulk updates
                with disable_thumbnail_generation():
                    # Two-step process to avoid unique constraint violation:
                    # Step 1: Set all sections to temporary negative indices to avoid conflicts
                    for temp_index, section_id in enumerate(section_ids):
                        section = section_map[str(section_id)]
                        section.index = -(temp_index + 1)  # Use negative values to avoid conflicts
                        section.save()

                    # Step 2: Set all sections to their final indices
                    for new_index, section_id in enumerate(section_ids):
                        section = section_map[str(section_id)]
                        section.index = new_index
                        section.save()

            # Trigger a single thumbnail generation after reordering completes (non-blocking)
            generate_resume_thumbnail_async(resume)

            # Return the updated resume
            return Response(ResumeFullSerializer(resume).data)
            
        except Exception as e:
            error_response = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message='Unexpected error occurred while rearranging sections.',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f'{error_response.uuid} -> Exception while rearranging sections: {e}')
            return error_response.response


# Education CRUD operations
@extend_schema(
    tags=['Education object'],
    parameters=[
        OpenApiParameter(
            name='resume_id',
            description='Resume ID of the resume the education belongs to. If you want to interact with the base educations, just put `base` in here',
            required=True,
            location=OpenApiParameter.PATH,
            type=str
        )
    ]
)
class EducationViewSets(viewsets.GenericViewSet):
    """
    API reference of all available endpoints for the Education object.
    Contains endpoints for getting all educations for a user, get specific education by its ID as well as create, update
    and delete individual educations by their ID.
    """

    def __init__(self, *args, **kwargs):
        self.authenticated_user: User | None = None
        self.resume: Resume | None = None
        self.error: Response | None = None
        super(EducationViewSets, self).__init__(*args, **kwargs)

    def __set_meta(self, request, resume_id: str):
        """
        Retrieve check and set authenticated user for Education CRUD
        """
        # Ownership Check for all types of API
        self.authenticated_user: User = request.user
        if resume_id == 'base':
            base_resume, created = self.authenticated_user.resume_set.get_or_create(base=True)
            self.resume = base_resume
        else:
            if not self.authenticated_user.resume_set.filter(id=resume_id).exists():
                self.error = ErrorResponse(code=ErrorCode.NOT_FOUND, message='Resume not found!',
                                           status_code=404).response
                return
            self.resume = self.authenticated_user.resume_set.get(id=resume_id)

    @extend_schema(
        responses={200: EducationFullSerializer(many=True), 500: ErrorSerializer},
        summary="Get all educations",
    )
    def list(self, request, resume_id: str) -> Response:
        """
        Returns all education for the resume id of the user
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        return Response(EducationFullSerializer(self.authenticated_user.education_set.filter(
            resume_section__resume=self.resume
        ), many=True).data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='Education ID of the education you want to retrieve',
                             required=False,
                             location=OpenApiParameter.PATH, type=str)
        ],
        responses={200: EducationFullSerializer, 500: ErrorSerializer},
        summary="Get education by id",
    )
    def retrieve(self, request, resume_id: str, pk: str) -> Response:
        """
        Returns a user's education by the education's id.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        education_id: str = pk
        education_sq: QuerySet[Education] = self.authenticated_user.education_set.filter(
            resume_section__resume=self.resume, id=education_id
        )
        if education_sq.exists():
            return Response(EducationFullSerializer(education_sq.first()).data)
        else:
            return ErrorResponse(
                code=ErrorCode.NOT_FOUND, message='Education not found!', details={'education': education_id}
            ).response

    @extend_schema(
        request=EducationUpsertSerializer,
        responses={200: EducationFullSerializer, 500: ErrorSerializer},
        summary="Add a new education"
    )
    def create(self, request, resume_id: str) -> Response:
        """
        Adds a new education to the user's resume as specified in the resume id.
        If a base is provided as the resume_id, the education is added to the base resume.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        new_resume_section = self.resume.create_section(section_type=ResumeSection.ResumeSectionType.Education)
        payload = request.data
        payload['user'] = self.authenticated_user.id
        payload['resume_section'] = new_resume_section.id
        education_ser: EducationUpsertSerializer = EducationUpsertSerializer(data=payload)
        try:
            if education_ser.is_valid():
                new_education = education_ser.save()
                index_resume_by_id_async(self.resume.id)
                return Response(EducationFullSerializer(new_education).data, status=status.HTTP_201_CREATED)
            else:
                if new_resume_section:
                    new_resume_section.delete()
                return ErrorResponse(
                    code=ErrorCode.INVALID_REQUEST, message='Invalid Data provided.',
                    details=education_ser.errors, extra={'data': request.data}
                ).response
        except Exception as e:
            if new_resume_section:
                new_resume_section.delete()
            error_response: ErrorResponse = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR, message='Unexpected error occurred.',
                details=education_ser.errors, extra={'data': request.data},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f'{error_response.uuid} -> Exception while adding education: {e}')
            return error_response.response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='Education ID of the education you want to update', required=False,
                             location=OpenApiParameter.PATH, type=str)
        ],
        request=EducationUpsertSerializer,
        responses={200: EducationFullSerializer, 500: ErrorSerializer},
        summary="Update an education"
    )
    def partial_update(self, request, resume_id: str, pk: str) -> Response:
        """
        Updates an existing education entry from the user's resume as specified in the resume id.
        If a base is provided as the resume_id, the education is updated in the base resume.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        try:
            if not self.authenticated_user.education_set.filter(
                id=pk, resume_section__resume=self.resume
            ).exists():
                return ErrorResponse(
                    code=ErrorCode.NOT_FOUND, message='Education not found!', details={'education': pk}
                ).response
            
            existing_education: Education = self.authenticated_user.education_set.get(
                id=pk, resume_section__resume=self.resume
            )
            payload = request.data.copy()
            payload['user'] = self.authenticated_user.id
            payload['resume_section'] = existing_education.resume_section.id
            
            education_ser = EducationUpsertSerializer(existing_education, data=payload, partial=True)
            
            if education_ser.is_valid():
                updated_education = education_ser.save()
                index_resume_by_id_async(self.resume.id)
                return Response(EducationFullSerializer(updated_education).data)
            else:
                return ErrorResponse(
                    code=ErrorCode.INVALID_REQUEST, message='Invalid Data provided.',
                    details=education_ser.errors, extra={'data': request.data}
                ).response
        except Exception as e:
            error_response: ErrorResponse = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR, message='Unexpected error occurred.',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f'{error_response.uuid} -> Exception while updating education: {e}')
            return error_response.response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='Education ID of the education you want to delete', required=False,
                             location=OpenApiParameter.PATH, type=str)
        ],
        responses={204: None, 500: ErrorSerializer},
        summary="Delete an education"
    )
    def destroy(self, request, resume_id: str, pk: str) -> Response:
        """
        Deletes an education from the user's resume as specified in the resume id.
        """
        education_id = pk
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        try:
            education: Education = self.authenticated_user.education_set.get(
                id=str(education_id).strip(), resume_section__resume=self.resume
            )
            resume_sec = education.resume_section
            education.delete()
            resume_sec.delete()
            index_resume_by_id_async(self.resume.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Education.DoesNotExist:
            return ErrorResponse(
                code=ErrorCode.NOT_FOUND, message=f'Education not found!', extra={'education': education_id}).response


# Experience CRUD ViewSets
@extend_schema(
    tags=['Experience object'],
    parameters=[
        OpenApiParameter(
            name="resume_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="Resume ID of the resume the education belongs to. If you want to interact with the base educations, just put `base` in here",
            required=True,
        ),
    ]
)
class ExperienceViewSets(viewsets.GenericViewSet):
    """
    API reference of all available endpoints for the Experience.
    Contains endpoints for getting all experience for a user, get specific experience by its ID as well as create,
    update and delete individual experience by their ID.
    """

    def __init__(self, *args, **kwargs):
        self.authenticated_user: User | None = None
        self.resume: Resume | None = None
        self.error: Response | None = None
        super(ExperienceViewSets, self).__init__(*args, **kwargs)

    def __set_meta(self, request, resume_id: str):
        """
        Retrieve check and set authenticated user & resume
        """
        # Ownership Check for all types of API
        self.authenticated_user: User = request.user
        if resume_id == 'base':
            base_resume, created = self.authenticated_user.resume_set.get_or_create(base=True)
            self.resume = base_resume
        else:
            if not self.authenticated_user.resume_set.filter(id=resume_id).exists():
                self.error = ErrorResponse(code=ErrorCode.NOT_FOUND, message='Resume not found!',
                                           status_code=404).response
                return
            self.resume = self.authenticated_user.resume_set.get(id=resume_id)

    @extend_schema(
        responses={200: ExperienceFullSerializer or ExperienceFullSerializer(many=True), 500: ErrorSerializer},
        summary="Get all experiences",
    )
    def list(self, request, resume_id: str) -> Response:
        """
        Gives all experiences for the Resume id
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        return Response(ExperienceFullSerializer(
            self.authenticated_user.experience_set.filter(resume_section__resume=self.resume), many=True).data,
                        status=status.HTTP_200_OK)

    @extend_schema(
        request=ExperienceUpsertSerializer,
        responses={201: ExperienceFullSerializer or ExperienceFullSerializer(many=True), 500: ErrorSerializer},
        summary="Create a new experience",
    )
    def create(self, request, resume_id: str) -> Response:
        """
        Adds a new experience to the user's resume as specified in the resume id.
        If a base resume id is provided, the experience is added to the base resume.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        new_resume_section = self.resume.create_section(section_type=ResumeSection.ResumeSectionType.Experience)
        payload = request.data
        payload['user'] = self.authenticated_user.id
        payload['resume_section'] = new_resume_section.id
        experience_ser: ExperienceUpsertSerializer = ExperienceUpsertSerializer(data=request.data)
        try:
            if experience_ser.is_valid():
                new_experience = experience_ser.save()
                index_resume_by_id_async(self.resume.id)
                return Response(ExperienceFullSerializer(new_experience).data, status=status.HTTP_201_CREATED)
            else:
                if new_resume_section:
                    new_resume_section.delete()
                return ErrorResponse(
                    code=ErrorCode.INVALID_REQUEST, message='Invalid Data provided!',
                    details=experience_ser.errors, extra={'data': request.data}
                ).response
        except Exception as e:
            if new_resume_section:
                new_resume_section.delete()
            error_response: ErrorResponse = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR, message='Unexpected error occurred.',
                details=experience_ser.errors, extra={'data': request.data},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f'{error_response.uuid} -> Exception while adding experience: {e}')
            return error_response.response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='Experience ID of the experience you want to retrieve',
                             required=True, type=str,
                             location=OpenApiParameter.PATH)
        ],
        responses={200: ExperienceFullSerializer or ExperienceFullSerializer(many=True), 500: ErrorSerializer},
        summary="Get experience by id",
    )
    def retrieve(self, request, resume_id: str, pk: str) -> Response:
        """
        Gives experience by id and resume id
        """
        experience_id = pk
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        experience_qs: QuerySet[Experience] = self.authenticated_user.experience_set.filter(
            resume_section__resume=self.resume, id=experience_id
        )
        if experience_qs.exists():
            return Response(ExperienceFullSerializer(experience_qs.first()).data)
        else:
            return ErrorResponse(
                code=ErrorCode.NOT_FOUND, message='Experience not found!', details={'experience': experience_id}
            ).response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='Experience ID of the experience you want to update', required=True,
                             type=str, location=OpenApiParameter.PATH)
        ],
        request=ExperienceUpsertSerializer,
        responses={200: ExperienceFullSerializer, 500: ErrorSerializer},
        summary="Update an experience"
    )
    def partial_update(self, request, resume_id: str, pk: str) -> Response:
        """
        Updates an existing experience in the user's resume as specified in the resume id.
        If a base is provided as the resume_id, the experience is updated in the base resume.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        try:
            if not self.authenticated_user.experience_set.filter(
                id=pk, resume_section__resume=self.resume
            ).exists():
                return ErrorResponse(
                    code=ErrorCode.NOT_FOUND, message='Experience not found!', details={'experience': pk}
                ).response
            
            existing_experience: Experience = self.authenticated_user.experience_set.get(
                id=pk, resume_section__resume=self.resume
            )
            payload = request.data.copy()
            payload['user'] = self.authenticated_user.id
            payload['resume_section'] = existing_experience.resume_section.id
            
            experience_ser = ExperienceUpsertSerializer(existing_experience, data=payload, partial=True)
            
            if experience_ser.is_valid():
                updated_experience = experience_ser.save()
                index_resume_by_id_async(self.resume.id)
                return Response(ExperienceFullSerializer(updated_experience).data)
            else:
                return ErrorResponse(
                    code=ErrorCode.INVALID_REQUEST, message='Invalid Data provided!',
                    details=experience_ser.errors, extra={'data': request.data}
                ).response
        except Exception as e:
            error_response: ErrorResponse = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR, message='Unexpected error occurred.',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f'{error_response.uuid} -> Exception while updating experience: {e}')
            return error_response.response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='Experience ID of the experience you want to delete', required=True,
                             type=str,
                             location=OpenApiParameter.PATH)
        ],
        responses={204: None, 500: ErrorSerializer}, summary="Delete an experience"
    )
    def destroy(self, request, resume_id: str, pk: str) -> Response:
        """
        Deletes an experience from the user's resume as specified in the resume id.
        """
        experience_id = pk
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        try:
            experience: Experience = self.authenticated_user.experience_set.get(
                id=experience_id, resume_section__resume=self.resume
            )
            resume_sec = experience.resume_section
            experience.delete()
            resume_sec.delete()
            index_resume_by_id_async(self.resume.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Experience.DoesNotExist:
            return ErrorResponse(code=ErrorCode.NOT_FOUND, message='Experience not found!',
                                 extra={'experience': experience_id}).response


# Skill CRUD ViewSets for a Resume
@extend_schema(
    tags=['Skill object'],
    parameters=[
        OpenApiParameter(
            name="resume_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="Resume ID of the resume the education belongs to. If you want to interact with the base Skill, just put `base` in here",
            required=True,
        ),
    ]
)
class ResumeSkillViewSets(viewsets.GenericViewSet):
    serializer_class = ProficiencySerializer
    """
    API reference of all available endpoints for the Skill object in an individual resume.
    Contains endpoints for getting all skills for a resume, create, update and delete specific skill by its ID as well.
    """

    def __init__(self, *args, **kwargs):
        self.authenticated_user: User | None = None
        self.resume: Resume | None = None
        self.error: Response | None = None
        super(ResumeSkillViewSets, self).__init__(*args, **kwargs)

    def __set_meta(self, request, resume_id: str):
        """
        Retrieve check and set authenticated user & resume
        """
        # Ownership Check for all types of API
        self.authenticated_user: User = request.user
        if resume_id == 'base':
            base_resume, created = self.authenticated_user.resume_set.get_or_create(base=True)
            self.resume = base_resume
        else:
            if not self.authenticated_user.resume_set.filter(id=resume_id).exists():
                self.error = ErrorResponse(code=ErrorCode.NOT_FOUND, message='Resume not found!',
                                           status_code=404).response
                return
            self.resume = self.authenticated_user.resume_set.get(id=resume_id)

    @extend_schema(
        responses={200: ProficiencySerializer(many=True), 500: ErrorSerializer},
        summary="Get all skills of resume",
    )
    def list(self, request, resume_id: str) -> Response:
        """
        Gives all skill for the Resume id or base if `base`  is provided as resume id
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        return Response(ProficiencySerializer(
            Proficiency.objects.filter(resume_section__resume=self.resume), many=True).data,
                        status=status.HTTP_200_OK)

    @extend_schema(
        request=ResumeSkillUpsertSerializer,
        responses={201: ProficiencySerializer, 500: ErrorSerializer},
        summary="Add a new skill",
    )
    def create(self, request, resume_id: str) -> Response:
        """
        Adds a new Skill to the user's resume as specified in the resume id.
        If a `base` is provided as resume id, the Skill is added to the base resume.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        try:
            index_resume_by_id_async(self.resume.id)
            return Response(ProficiencySerializer(self.resume.add_skill(
                skill_name=request.data.get('name'),
                skill_category=request.data.get('category'),
                skill_proficiency=request.data.get('level'),
            )).data)
        except ValueError as ve:
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST, message=ve.__str__(),
                extra={'data': request.data}, status_code=status.HTTP_400_BAD_REQUEST
            ).response
        except Exception as e:
            error_response: ErrorResponse = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR, message='Unexpected error occurred.',
                details=e.__str__(), extra={'data': request.data},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f'{error_response.uuid} -> Exception while adding experience: {e}')
            return error_response.response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='ID of the Skill-proficiency you want to delete for the resume',
                             required=True,
                             type=str, location=OpenApiParameter.PATH)
        ],
        responses={200: ProficiencySerializer, 500: ErrorSerializer},
        summary="Update an existing skill",
    )
    def partial_update(self, request, resume_id: str, pk) -> Response:
        """
        Update an existing Skill-proficiency to the user's resume as specified in the resume id.
        If a base resume id is provided, the Skill is updated for the base resume.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        try:
            skill_proficiency: Proficiency = Proficiency.objects.filter(
                resume_section__resume=self.resume, id=pk
            ).first()
            name = request.data.get('name', '---')
            if not name:
                raise ValueError('Name can not be empty.')
            category = request.data.get('category', '---')
            level = request.data.get('level', '---')
            edited_skill_proficiency = self.resume.edit_skill(
                proficiency_id=pk,
                skill_name=skill_proficiency.skill.name if name == '---' else name,
                skill_category=skill_proficiency.skill.category if category == '---' else category,
                skill_proficiency=skill_proficiency.level if level == '---' else level,
            )
            index_resume_by_id_async(self.resume.id)
            return Response(ProficiencySerializer(edited_skill_proficiency).data)
        except ValueError as ve:
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST, message=ve.__str__(),
                extra={'data': request.data}, status_code=status.HTTP_400_BAD_REQUEST
            ).response
        except Exception as e:
            error_response: ErrorResponse = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR, message='Unexpected error occurred.',
                details=e.__str__(), extra={'data': request.data},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f'{error_response.uuid} -> Exception while adding experience: {e}')
            return error_response.response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='ID of the Skill-proficiency you want to delete for the resume',
                             required=True,
                             type=str, location=OpenApiParameter.PATH)
        ],
        responses={204: None, 500: ErrorSerializer}, summary="Remove skill from resume"
    )
    def destroy(self, request, resume_id: str, pk: str) -> Response:
        """
        Deletes a skill-proficiency from the user's resume as specified in the resume id or base resume if `base ids provided as resume id`.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        try:
            self.resume.remove_skill(pk)
            index_resume_by_id_async(self.resume.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Experience.DoesNotExist:
            return ErrorResponse(code=ErrorCode.NOT_FOUND, message='Experience not found!',
                                 extra={'proficiency': pk}).response
        except ValueError as ve:
            return ErrorResponse(code=ErrorCode.INVALID_REQUEST, message='Invalid proficiency id.',
                                 extra={'proficiency': pk}).response
        except Exception as ex:
            error_response = ErrorResponse(code=ErrorCode.INTERNAL_SERVER_ERROR, message='Unexpected error occurred.',
                                           details=ex.__str__(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            logger.exception(f'{error_response.uuid} -> Unexpected exception occurred: {ex.__str__()}')
            return error_response.response

    @extend_schema(
        responses={200: serializers.ListSerializer(child=serializers.CharField()), 500: ErrorSerializer},
        summary="Get all skill category for the resume"
    )
    @action(detail=False, methods=['get'], url_path='categories')
    def get_featured_resumes(self, request, resume_id: str) -> Response:
        """
        Get all skill category for the resume
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        all_skill_proficiencies_for_resume: QuerySet[Proficiency] = Proficiency.objects.filter(
            resume_section__resume=self.resume
        )
        all_skill_categories_for_resume: set[str] = set()
        proficiency: Proficiency
        for proficiency in all_skill_proficiencies_for_resume:
            if not proficiency.skill.category:
                continue
            all_skill_categories_for_resume.add(proficiency.skill.category)
        return Response(all_skill_categories_for_resume)


# Project CRUD ViewSets for a Resume
@extend_schema(
    tags=['Project object'],
    parameters=[
        OpenApiParameter(
            name="resume_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="Resume ID of the resume the education belongs to. If you want to interact with the base project, just put `base` in here",
            required=True,
        ),
    ]
)
class ResumeProjectViewSets(viewsets.GenericViewSet):
    """
    API reference of all available endpoints for the Projects object in an individual resume.
    Contains endpoints for getting all projects for a resume, create, update and delete specific skill by its ID as well.
    """

    def __init__(self, *args, **kwargs):
        self.authenticated_user: User | None = None
        self.resume: Resume | None = None
        self.error: Response | None = None
        super(ResumeProjectViewSets, self).__init__(*args, **kwargs)

    def __set_meta(self, request, resume_id: str):
        """
        Retrieve check and set authenticated user & resume
        """
        # Ownership Check for all types of API
        self.authenticated_user: User = request.user
        if resume_id == 'base':
            base_resume, created = self.authenticated_user.resume_set.get_or_create(base=True)
            self.resume = base_resume
        else:
            if not self.authenticated_user.resume_set.filter(id=resume_id).exists():
                self.error = ErrorResponse(code=ErrorCode.NOT_FOUND, message='Resume not found!',
                                           status_code=404).response
                return
            self.resume = self.authenticated_user.resume_set.get(id=resume_id)

    @extend_schema(
        responses={200: ProjectSerializer(many=True), 500: ErrorSerializer},
        summary="Get all projects",
    )
    def list(self, request, resume_id: str) -> Response:
        """
        Gives all projects for the Resume id or base if `base`  is provided as resume id
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        return Response(ProjectSerializer(
            Project.objects.filter(resume_section__resume=self.resume), many=True).data,
                        status=status.HTTP_200_OK)

    @extend_schema(
        request=ProjectUpsertSerializer,
        responses={201: ProjectSerializer, 500: ErrorSerializer},
        summary="Create a new project",
    )
    def create(self, request, resume_id: str) -> Response:
        """
        Adds a new project to the user's resume as specified in the resume id.
        If a `base` is provided as resume id, the Project is added to the base resume.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        try:
            payload: dict = request.data
            skill_used: list[dict] = payload.get('skills_used')
            if payload.get('skills_used'):
                del payload['skills_used']
            new_resume_section = self.resume.create_section(section_type=ResumeSection.ResumeSectionType.Project)
            payload['resume_section'] = new_resume_section.id
            payload['user'] = self.authenticated_user.id
            project_ser: ProjectUpsertSerializer = ProjectUpsertSerializer(data=payload)
            if project_ser.is_valid():
                new_project: Project = project_ser.save()
                if type(skill_used) is type(list()):
                    for skill_dict in skill_used:
                        new_project.add_skill(skill_name=skill_dict.get('name'),
                                              skill_category=skill_dict.get('category'))

                index_resume_by_id_async(self.resume.id)
                return Response(ProjectSerializer(new_project).data, status=HTTPStatus.CREATED)
            else:
                if new_resume_section:
                    new_resume_section.delete()
                return ErrorResponse(
                    code=ErrorCode.INVALID_REQUEST, message='Invalid Data provided.',
                    details=project_ser.errors, extra={'data': request.data}
                ).response
        except ValueError as ve:
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST, message=ve.__str__(),
                extra={'data': request.data}, status_code=status.HTTP_400_BAD_REQUEST
            ).response
        except Exception as e:
            error_response: ErrorResponse = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR, message='Unexpected error occurred.',
                details=e.__str__(), extra={'data': request.data},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f'{error_response.uuid} -> Exception while adding project: {e}')
            return error_response.response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='ID of the project that you want to update',
                             required=True,
                             type=str, location=OpenApiParameter.PATH)
        ],
        request=ProjectUpsertSerializer,
        responses={200: ProjectSerializer, 500: ErrorSerializer},
        summary="Update a project",
    )
    def partial_update(self, request, resume_id: str, pk: str) -> Response:
        """
        Updates an existing project of the user's resume as specified in the resume id.
        If a `base` is provided as resume id, the Project is added to the base resume.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        try:
            if not Project.objects.filter(id=pk).exists():
                return ErrorResponse(
                    code=ErrorCode.NOT_FOUND, message='Project not found!', details={'project': pk}
                ).response
            existing_project: Project = Project.objects.get(id=pk)
            payload: dict = request.data.copy()
            skill_used: list[dict] = payload.get('skills_used')
            if payload.get('skills_used'):
                del payload['skills_used']
            payload['user'] = self.authenticated_user.id
            project_ser: ProjectUpsertSerializer = ProjectUpsertSerializer(existing_project, data=payload, partial=True)
            if project_ser.is_valid():
                updated_project: Project = project_ser.save()
                if not request.data.get('skills_used', '---') == '---':
                    updated_project.skills_used.clear()
                    updated_project.save()
                if type(skill_used) is type(list()):
                    for skill_dict in skill_used:
                        if not skill_dict.get('name'):
                            continue
                        updated_project.add_skill(skill_name=skill_dict.get('name'),
                                                  skill_category=skill_dict.get('category'))

                index_resume_by_id_async(self.resume.id)
                return Response(ProjectSerializer(updated_project).data)
            else:
                return ErrorResponse(
                    code=ErrorCode.INVALID_REQUEST, message='Invalid Data provided.',
                    details=project_ser.errors, extra={'data': request.data}
                ).response
        except ValueError as ve:
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST, message=ve.__str__(),
                extra={'data': request.data}, status_code=status.HTTP_400_BAD_REQUEST
            ).response
        except Exception as e:
            error_response: ErrorResponse = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR, message='Unexpected error occurred.',
                details=e.__str__(), extra={'data': request.data},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f'{error_response.uuid} -> Exception while adding project: {e}')
            return error_response.response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='ID of the project that you want to delete',
                             required=True,
                             type=str, location=OpenApiParameter.PATH)
        ],
        request=ProjectUpsertSerializer,
        responses={200: None, 500: ErrorSerializer},
        summary="Delete a project",
    )
    def destroy(self, request, resume_id: str, pk: str) -> Response:
        """
        Delete an existing project of the user's resume as specified in the resume id.
        If a `base` is provided as resume id, the Project is added to the base resume.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        try:
            if not Project.objects.filter(id=pk).exists():
                return ErrorResponse(
                    code=ErrorCode.NOT_FOUND, message='Project not found!', details={'project': pk}
                ).response
            existing_project: Project = Project.objects.get(id=pk)
            parent_resume_section: ResumeSection = existing_project.resume_section
            existing_project.delete()
            parent_resume_section.delete()
            index_resume_by_id_async(self.resume.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as ve:
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST, message=ve.__str__(),
                extra={'data': request.data}, status_code=status.HTTP_400_BAD_REQUEST
            ).response
        except Exception as e:
            error_response: ErrorResponse = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR, message='Unexpected error occurred.',
                details=e.__str__(), extra={'data': request.data},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f'{error_response.uuid} -> Exception while adding project: {e}')
            return error_response.response

# Certification CRUD ViewSets for a Resume
@extend_schema(
    tags=['Certification object'],
    parameters=[
        OpenApiParameter(
            name="resume_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="Resume ID of the resume the certification belongs to. If you want to interact with the base resume certification, just put `base` in here",
            required=True,
        ),
    ]
)
class ResumeCertificationViewSets(viewsets.GenericViewSet):
    """
    API reference of all available endpoints for the Certifications object in an individual resume.
    Contains endpoints for getting all Certifications for a resume, create, update and delete specific Certification by its ID as well.
    """

    def __init__(self, *args, **kwargs):
        self.authenticated_user: User | None = None
        self.resume: Resume | None = None
        self.error: Response | None = None
        super(ResumeCertificationViewSets, self).__init__(*args, **kwargs)

    def __set_meta(self, request, resume_id: str):
        """
        Retrieve check and set authenticated user & resume
        """
        # Ownership Check for all types of API
        self.authenticated_user: User = request.user
        if resume_id == 'base':
            base_resume, created = self.authenticated_user.resume_set.get_or_create(base=True)
            self.resume = base_resume
        else:
            if not self.authenticated_user.resume_set.filter(id=resume_id).exists():
                self.error = ErrorResponse(code=ErrorCode.NOT_FOUND, message='Resume not found!',
                                           status_code=404).response
                return
            self.resume = self.authenticated_user.resume_set.get(id=resume_id)

    @extend_schema(
        responses={200: CertificationSerializer(many=True), 500: ErrorSerializer},
        summary="Get all certifications",
    )
    def list(self, request, resume_id: str) -> Response:
        """
        Gives all certifications for the Resume id or base if `base` is provided as resume id
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        return Response(CertificationSerializer(
            Certification.objects.filter(resume_section__resume=self.resume), many=True).data,
                        status=status.HTTP_200_OK)



    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='Resume ID', required=True, location=OpenApiParameter.PATH,
                             type=str)
        ],
        responses={200: CertificationSerializer, 500: ErrorSerializer},
        summary="Get certification by id"
    )
    def retrieve(self, request, pk, resume_id: str) -> Response:
        """
        Gives the certification of the resume for the user by produced id or gives base resume certification of the user if id is provided as `base`.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        if Certification.objects.filter(resume_section__resume=self.resume, id=pk).exists():
            return Response(CertificationSerializer(Certification.objects.get(resume_section__resume=self.resume, id=pk)).data)
        else:
            return ErrorResponse(code=ErrorCode.NOT_FOUND, message='Certification not found!', status_code=404).response


    @extend_schema(
        request=CertificationUpsertSerializer,
        responses={201: CertificationSerializer, 500: ErrorSerializer},
        summary="Create a new certification",
    )
    def create(self, request, resume_id: str) -> Response:
        """
        Adds a new certification to the user's resume as specified in the resume id.
        If a `base` is provided as resume id, the certification is added to the base resume.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        try:
            payload: dict = request.data
            new_resume_section = self.resume.create_section(section_type=ResumeSection.ResumeSectionType.Certification)
            payload['resume_section'] = new_resume_section.id
            payload['user'] = self.authenticated_user.id
            certification_ser: CertificationUpsertSerializer = CertificationUpsertSerializer(data=payload)
            if certification_ser.is_valid():
                new_certification: Certification = certification_ser.save()
                index_resume_by_id_async(self.resume.id)
                return Response(CertificationSerializer(new_certification).data, status=HTTPStatus.CREATED)
            else:
                if new_resume_section:
                    new_resume_section.delete()
                return ErrorResponse(
                    code=ErrorCode.INVALID_REQUEST, message='Invalid Data provided.',
                    details=certification_ser.errors, extra={'data': request.data}
                ).response
        except ValueError as ve:
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST, message=ve.__str__(),
                extra={'data': request.data}, status_code=status.HTTP_400_BAD_REQUEST
            ).response
        except Exception as e:
            error_response: ErrorResponse = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR, message='Unexpected error occurred.',
                details=e.__str__(), extra={'data': request.data},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f'{error_response.uuid} -> Exception while adding certification: {e}')
            return error_response.response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='ID of the certification that you want to update',
                             required=True,
                             type=str, location=OpenApiParameter.PATH)
        ],
        request=CertificationUpsertSerializer,
        responses={200: CertificationSerializer, 500: ErrorSerializer},
        summary="Update a certification",
    )
    def partial_update(self, request, resume_id: str, pk: str) -> Response:
        """
        Updates an existing certification of the user's resume as specified in the resume id.
        If a `base` is provided as resume id, the certification is added to the base resume.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        try:
            if not Certification.objects.filter(id=pk).exists():
                return ErrorResponse(
                    code=ErrorCode.NOT_FOUND, message='Certification not found!', details={'certification': pk}
                ).response
            existing_certification: Certification = Certification.objects.get(id=pk)
            payload: dict = request.data.copy()
            payload['user'] = self.authenticated_user.id
            certification_ser: CertificationUpsertSerializer = CertificationUpsertSerializer(existing_certification, data=payload, partial=True)
            if certification_ser.is_valid():
                updated_certification: Certification = certification_ser.save()
                index_resume_by_id_async(self.resume.id)
                return Response(CertificationSerializer(updated_certification).data)
            else:
                return ErrorResponse(
                    code=ErrorCode.INVALID_REQUEST, message='Invalid Data provided.',
                    details=certification_ser.errors, extra={'data': request.data}
                ).response
        except ValueError as ve:
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST, message=ve.__str__(),
                extra={'data': request.data}, status_code=status.HTTP_400_BAD_REQUEST
            ).response
        except Exception as e:
            error_response: ErrorResponse = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR, message='Unexpected error occurred.',
                details=e.__str__(), extra={'data': request.data},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f'{error_response.uuid} -> Exception while adding project: {e}')
            return error_response.response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='ID of the certification that you want to delete',
                             required=True,
                             type=str, location=OpenApiParameter.PATH)
        ],
        request=CertificationUpsertSerializer,
        responses={200: None, 500: ErrorSerializer},
        summary="Delete a certification",
    )
    def destroy(self, request, resume_id: str, pk: str) -> Response:
        """
        Delete an existing certification of the user's resume as specified in the resume id.
        If a `base` is provided as resume id, the certification will be  deleted from to the base resume.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        try:
            if not Certification.objects.filter(id=pk).exists():
                return ErrorResponse(
                    code=ErrorCode.NOT_FOUND, message='Certification not found!', details={'certification': pk}
                ).response
            existing_certification: Certification = Certification.objects.get(id=pk)
            parent_resume_section: ResumeSection = existing_certification.resume_section
            existing_certification.delete()
            parent_resume_section.delete()
            index_resume_by_id_async(self.resume.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as ve:
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST, message=ve.__str__(),
                extra={'data': request.data}, status_code=status.HTTP_400_BAD_REQUEST
            ).response
        except Exception as e:
            error_response: ErrorResponse = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR, message='Unexpected error occurred.',
                details=e.__str__(), extra={'data': request.data},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            logger.exception(f'{error_response.uuid} -> Exception while adding project: {e}')
            return error_response.response

@extend_schema(
    methods=['POST'],
    tags=['Resume object'],
    summary="Start resume tailoring process",
    responses={
        200: ResumeFullSerializer,
        400: ErrorSerializer
    }
)
@api_view(['POST'])
def tailor_resume(request):
    """
    Start resume tailoring process
    """
    try:
        url_pattern = r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)'
        target:str = request.data.get('target')
        if not target:
            return ErrorResponse(code=ErrorCode.INVALID_REQUEST, message='"target" is required in body!').response
        if re.match(url_pattern, target):
            sanitized_url = str(target).strip().rstrip('/')

            sanitized_url_job_qs = Job.objects.filter(job_url=sanitized_url)
            if sanitized_url_job_qs.exists():
                job = sanitized_url_job_qs.first()
                # Only unavailable if the job scraping is not completed successfully
                if job.status != Job.Status.Success:
                    return ErrorResponse(code=ErrorCode.UNAVAILABLE, message='This service is temporarily unavailable please try after some time', status_code=503).response
                # If a resume exists for THIS user and this job, return it; otherwise create a new one for this user
                job_resume_qs = Resume.objects.filter(job=job, user=request.user)
                if job_resume_qs.exists():
                    return Response(ResumeFullSerializer(job_resume_qs.first(), many=False).data)
                else:
                    new_resume_for_job = Resume.objects.create(job=job, user=request.user, status=Resume.Status.Processing.value)
                    # GRPC: Call Tailor-Resume RPC method to Util service
                    base_resume = request.user.resume_set.get(base=True)
                    process = Process.objects.create(desc='Tailor Resume Process')
                    try:
                        resume_service = letraz_utils_pb2_grpc.ResumeServiceStub(settings.UTIL_GRPC_CHANNEL)
                        req = letraz_utils_pb2.TailorResumeRequest(base_resume=BaseResumeUtilSerializer(base_resume, many=False).data, job=JobSerializer(job, many=False).data, resume_id=new_resume_for_job.id)
                        res = MessageToDict(resume_service.TailorResume(req))
                        logger.debug(f'Tailor Resume Process: \n{res}')
                        process.status = res.get('status')
                        process.util_id = res.get('processId')
                        process.status_details = res.get('message')
                        process.save()
                        new_resume_for_job.process = process
                        new_resume_for_job.save()
                    except Exception as e:
                        error_response = ErrorResponse(code=ErrorCode.INTERNAL_SERVER_ERROR, message=e.__str__())
                        logger.exception(f'UUID -> {error_response.uuid} | GRPC call error [UTIL]: {e.__str__()}')
                        process.status = Process.ProcessStatus.Failed.value
                        process.status_details = f'[UUID- {error_response.uuid}] - {e.__str__()}'
                        process.save()
                        if new_resume_for_job:
                            new_resume_for_job.delete()
                        return error_response.response
                    return Response(ResumeFullSerializer(new_resume_for_job, many=False).data)
            else:
                new_job_obj = Job.objects.create(job_url=sanitized_url, title='<UNDER_EXTRACTION>', company_name='<UNDER_EXTRACTION>', status=Job.Status.Processing.value)
                new_resume_for_job = Resume.objects.create(job=new_job_obj, user=request.user, status=Resume.Status.Processing.value)
                # GRPC: Call Scrape-Job RPC method with URL to Util service
                process = Process.objects.create(desc='Scrape Job Process')
                try:
                    scrapper = letraz_utils_pb2_grpc.ScraperServiceStub(settings.UTIL_GRPC_CHANNEL)
                    req = letraz_utils_pb2.ScrapeJobRequest(url=sanitized_url)
                    res = MessageToDict(scrapper.ScrapeJob(req))
                    logger.debug(f'Scrapper Response: \n{res}')
                    process.status = res.get('status')
                    process.util_id = res.get('processId')
                    process.status_details = res.get('message')
                    process.save()
                    new_job_obj.process = process
                    new_job_obj.save()
                except Exception as e:
                    error_response = ErrorResponse(code=ErrorCode.INTERNAL_SERVER_ERROR, message=e.__str__())
                    logger.exception(f'UUID -> {error_response.uuid} | GRPC call error [UTIL]: {e.__str__()}')
                    process.status = Process.ProcessStatus.Failed.value
                    process.status_details = f'[UUID- {error_response.uuid}] - {e.__str__()}'
                    process.save()
                    if new_job_obj:
                        new_job_obj.delete()
                    if new_resume_for_job:
                        new_resume_for_job.delete()
                    return error_response.response
                return Response(ResumeFullSerializer(new_resume_for_job, many=False).data)
        elif len(str(target.strip())) > 300:
            new_job_obj = Job.objects.create(title='<UNDER_EXTRACTION>', company_name='<UNDER_EXTRACTION>', status=Job.Status.Processing.value)
            new_resume_for_job = Resume.objects.create(job=new_job_obj, user=request.user, status=Resume.Status.Processing.value)
            # GRPC: Call Scrape-Job RPC method with Description to Util service
            process = Process.objects.create(desc='Scrape Job Process')
            try:
                scrapper = letraz_utils_pb2_grpc.ScraperServiceStub(settings.UTIL_GRPC_CHANNEL)
                req = letraz_utils_pb2.ScrapeJobRequest(description=target.strip())
                res = MessageToDict(scrapper.ScrapeJob(req))
                logger.debug(f'Scrapper Response: {res}')
                process.status = res.get('status')
                process.util_id = res.get('processId')
                process.status_details = res.get('message')
                process.save()
                new_job_obj.process = process
                new_job_obj.save()
            except Exception as e:
                error_response = ErrorResponse(code=ErrorCode.INTERNAL_SERVER_ERROR, message=e.__str__())
                logger.exception(f'UUID -> {error_response.uuid} | GRPC call error [UTIL]: {e.__str__()}')
                process.status = Process.ProcessStatus.Failed.value
                process.status_details = f'[UUID- {error_response.uuid}] - {e.__str__()}'[:249]
                process.save()
                if new_job_obj:
                    new_job_obj.delete()
                if new_resume_for_job:
                    new_resume_for_job.delete()
                return error_response.response
            return Response(ResumeFullSerializer(new_resume_for_job, many=False).data)
        else:
            return ErrorResponse(code=ErrorCode.INVALID_REQUEST, message='Description is too short.').response
    except Exception as e:
        error_response = ErrorResponse(code=ErrorCode.INVALID_REQUEST, message=e.__str__(), extra={'data': request.data})
        logger.exception(f'UUID -> {error_response.uuid} | Unknown error encountered: {e.__str__()}')
        return error_response.response

