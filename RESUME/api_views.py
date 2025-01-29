import logging
from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from CORE.serializers import ErrorSerializer
from PROFILE.models import User
from RESUME.models import Resume, Education, Experience, ResumeSection, generate_resume_id
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
        Gives a list of all resumes for the user
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
        OpenApiParameter(name='resume_id', description='Resume ID', required=True, location=OpenApiParameter.PATH,
                         type=str)]
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
        Retrieve check and set authenticated user for Education CRUD
        """
        # Ownership Check for all types of API
        self.authenticated_user: User = request.user
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
            OpenApiParameter(name='id', description='Education ID', required=False,
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
        If a base resume id is provided, the education is added to the base resume.
        """
        self.__set_meta(request, resume_id)
        if self.error:
            return self.error
        new_resume_section = self.resume.create_section(section_type=ResumeSection.ResumeSectionType.Education)
        payload = request.data
        payload['user'] = self.authenticated_user.id
        payload['resume_section'] = new_resume_section.id
        education_ser: EducationUpsertSerializer = EducationUpsertSerializer(data=payload)
        if education_ser.is_valid():
            new_education = education_ser.save()
            return Response(EducationFullSerializer(new_education).data, status=status.HTTP_201_CREATED)
        else:
            if new_resume_section:
                new_resume_section.delete()
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST, message=f'Invalid Data provided!',
                details=education_ser.errors, extra={'data': request.data}
            ).response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='id', description='Education ID', required=False,
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
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="Unique identifier of the Resume",
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
        if not self.authenticated_user.resume_set.filter(id=resume_id).exists():
            self.error = ErrorResponse(code=ErrorCode.NOT_FOUND, message='Resume not found!', status_code=404).response
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
        if experience_ser.is_valid():
            new_experience = experience_ser.save()
            return Response(ExperienceFullSerializer(new_experience).data, status=status.HTTP_201_CREATED)
        else:
            if new_resume_section:
                new_resume_section.delete()
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST, message=f'Invalid Data provided!',
                details=experience_ser.errors, extra={'data': request.data}
            ).response

    @extend_schema(
        tags=['Experience object'],
        parameters=[
            OpenApiParameter(name='id', description='Experience ID', required=True, type=str,
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
            OpenApiParameter(name='id', description='Experience ID', required=True, type=str,
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
                                 extra={'experience': experience_id}).response
