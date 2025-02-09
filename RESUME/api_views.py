import json
import logging
from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from CORE.serializers import ErrorSerializer
from PROFILE.models import User
from RESUME.models import Resume, Education, Experience, ResumeSection, Proficiency, Project
from RESUME.serializers import ResumeShortSerializer, ResumeFullSerializer, EducationFullSerializer, \
    ExperienceFullSerializer, EducationUpsertSerializer, ExperienceUpsertSerializer, ProficiencySerializer, \
    ProjectSerializer, ResumeSkillUpsertSerializer, ProjectUpsertSerializer
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from letraz_server.settings import PROJECT_NAME

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


# Education CRUD operations
@extend_schema(
    tags=['Education object'],
    parameters=[
        OpenApiParameter(
            name='resume_id',
            description='Resume ID of the resume the education belongs to. If you want to interact with the base educations, just put `base` in here',
            required=True,
            location=OpenApiParameter.PATH,
            type=OpenApiTypes.STR
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
            type=OpenApiTypes.STR,
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
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="Resume ID of the resume the education belongs to. If you want to interact with the base Skill, just put `base` in here",
            required=True,
        ),
    ]
)
class ResumeSkillViewSets(viewsets.GenericViewSet):
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
            type=OpenApiTypes.STR,
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
                return Response(ProjectSerializer(new_project).data)
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
