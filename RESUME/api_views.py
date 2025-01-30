import logging
from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status, viewsets
from rest_framework.response import Response
from CORE.serializers import ErrorSerializer
from PROFILE.models import User
from RESUME.models import Resume, Education, Experience, ResumeSection
from RESUME.serializers import ResumeShortSerializer, ResumeFullSerializer, EducationFullSerializer, \
    ExperienceFullSerializer, EducationUpsertSerializer, ExperienceUpsertSerializer
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
        Gives a resume for the user by produced id
        """
        self.__set_meta(request)
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
        self.error: Response | None = None
        super(EducationViewSets, self).__init__(*args, **kwargs)

    def __set_meta(self, request, resume_id: str):
        """
        Set up metadata for education or experience operations on a specific resume.
        
        This method authenticates the user and retrieves or creates a resume context for subsequent CRUD operations. It handles two scenarios:
        1. When 'base' resume is requested: Finds an existing base resume or creates a new one
        2. When a specific resume ID is provided: Retrieves the resume or sets an error response if not found
        
        Parameters:
            request (Request): The incoming HTTP request
            resume_id (str): The ID of the resume or 'base' to indicate a base resume
        
        Side Effects:
            - Sets `self.authenticated_user` to the current user
            - Sets `self.resume` to the retrieved or created resume
            - Sets `self.error` if the resume is not found for a non-base resume ID
        
        Returns:
            None: Returns early with an error response if resume is not found
        """
        # Ownership Check for all types of API
        self.authenticated_user: User = request.user
        if resume_id == 'base':
            if self.authenticated_user.resume_set.filter(base=True).exists():
                self.resume = self.authenticated_user.resume_set.filter(base=True).first()
            else:
                self.resume = self.authenticated_user.resume_set.create(base=True)
        else:
            if not self.authenticated_user.resume_set.filter(id=resume_id).exists():
                self.error = ErrorResponse(code=ErrorCode.NOT_FOUND, message='Resume not found!', status_code=404).response
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
            OpenApiParameter(name='id', description='Education ID of the education you want to retrieve', required=False,
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
        Set up metadata for the current resume operation, handling base and specific resumes.
        
        This method performs the following key tasks:
        - Authenticates the current user from the request
        - Handles resume retrieval or creation based on the resume_id
        - Supports 'base' resume creation if no base resume exists
        - Sets error response if a specific resume is not found
        
        Parameters:
            request (Request): The incoming HTTP request
            resume_id (str): Identifier for the resume, can be 'base' or a specific resume ID
        
        Side Effects:
            - Sets self.authenticated_user to the current user
            - Sets self.resume to the retrieved or created resume
            - Sets self.error if resume retrieval fails
        """
        # Ownership Check for all types of API
        self.authenticated_user: User = request.user
        if resume_id == 'base':
            if self.authenticated_user.resume_set.filter(base=True).exists():
                self.resume = self.authenticated_user.resume_set.filter(base=True).first()
            else:
                self.resume = self.authenticated_user.resume_set.create(base=True)
        else:
            if not self.authenticated_user.resume_set.filter(id=resume_id).exists():
                self.error = ErrorResponse(code=ErrorCode.NOT_FOUND, message='Resume not found!',
                                           status_code=404).response
                return
            self.resume = self.authenticated_user.resume_set.get(id=resume_id)

    @extend_schema(
        tags=['Experience object'],
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
        tags=['Experience object'],
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
        tags=['Experience object'],
        parameters=[
            OpenApiParameter(name='id', description='Experience ID of the experience you want to retrieve', required=True, type=str,
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
        tags=['Experience object'],
        parameters=[
            OpenApiParameter(name='id', description='Experience ID of the experience you want to delete', required=True, type=str,
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
