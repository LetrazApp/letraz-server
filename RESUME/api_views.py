import logging
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import api_view
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


# Resume CRUD operations
@extend_schema(
    methods=['GET'],
    tags=['Resume object'],
    parameters=[
        OpenApiParameter(
            name='user_id',
            location=OpenApiParameter.PATH,
            description='User ID',
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='resume_id',
            description='Resume ID',
            required=False,
            type=str
        )
    ],
    auth=[],
    responses={
        200: ResumeFullSerializer or ResumeFullSerializer(many=True),
        500: ErrorSerializer
    },
    summary="Get one or all resume",
    description="Returns a user's resume by the resume's id. If no resume id is not specified then returns all resumes. If the resume is not found, a 404 error is returned."
)
@api_view(['GET'])
def resume_crud(request, resume_id: str | None = None):
    if request.method == 'GET':
        authenticated_user: User = request.user
        # If resume id is not provided send all resumes for the user
        if request.query_params.get('base') and request.query_params.get('base') == 'true':
            base_resume_qs: QuerySet[Resume] = authenticated_user.resume_set.filter(base=True)
            if base_resume_qs.exists():
                return Response(ResumeFullSerializer(base_resume_qs.first()).data)
            else:
                return ErrorResponse(code=ErrorCode.NOT_FOUND, message='Base Resume not found!').response
        elif resume_id:
            resume_by_user_and_resume_id_qs: QuerySet[Resume] = authenticated_user.resume_set.filter(id=resume_id)
            if resume_by_user_and_resume_id_qs.exists():
                return Response(ResumeFullSerializer(resume_by_user_and_resume_id_qs.first()).data)
            else:
                return ErrorResponse(
                    code=ErrorCode.NOT_FOUND, message='Resume not found!', details={'resume': resume_id}
                ).response
        else:
            return Response(
                ResumeShortSerializer(authenticated_user.resume_set.all(), many=True).data
            )


# Education CRUD operations
@extend_schema(
    methods=['GET'],
    tags=['Education object'],
    parameters=[
        OpenApiParameter(
            name='user_id',
            location=OpenApiParameter.PATH,
            description='User ID',
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='resume_id',
            description='Resume ID',
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='education_id',
            description='Education ID',
            required=False,
            type=str
        )
    ],
    auth=[],
    responses={
        200: EducationFullSerializer or EducationFullSerializer(many=True),
        500: ErrorSerializer
    },
    summary="Get one or all educations",
    description="Returns a user's education by the education's id. If no education id is not specified then returns all educations for the resume as specified in the resume id. Send the id of the base resume to get the user's all base educations. If the education is not found, a 404 error is returned."
)
@extend_schema(
    methods=['POST'],
    tags=['Education object'],
    parameters=[
        OpenApiParameter(
            name='user_id',
            location=OpenApiParameter.PATH,
            description='User ID',
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='resume_id',
            description='Resume ID',
            required=True,
            type=str
        )
    ],
    auth=[],
    responses={
        200: EducationFullSerializer,
        500: ErrorSerializer
    },
    summary="Add a new education",
    description="Adds a new education to the user's resume as specified in the resume id. If a base resume id is provided, the education is added to the base resume."
)
@extend_schema(
    methods=['DELETE'],
    tags=['Education object'],
    parameters=[
        OpenApiParameter(
            name='user_id',
            location=OpenApiParameter.PATH,
            description='User ID',
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='resume_id',
            description='Resume ID',
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='education_id',
            description='Education ID',
            required=True,
            type=str
        )
    ],
    auth=[],
    responses={
        204: None,
        500: ErrorSerializer
    },
    summary="Delete an education",
    description="Deletes an education from the user's resume as specified in the resume id."
)
@api_view(['GET', 'POST', 'DELETE'])
def education_crud(request, resume_id: str, education_id: str | None = None):
    try:
        # Ownership Check for all types of API
        authenticated_user: User = request.user
        if not authenticated_user.resume_set.filter(id=resume_id).exists():
            return ErrorResponse(code=ErrorCode.NOT_FOUND, message='Resume not found!', status_code=404).response
        resume: Resume = authenticated_user.resume_set.get(id=resume_id)

        # Main APIs Logic
        if request.method == 'GET':
            if education_id:
                education_sq: QuerySet[Education] = authenticated_user.education_set.filter(
                    resume_section__resume=resume, id=education_id
                )
                if education_sq.exists():
                    return Response(EducationFullSerializer(education_sq.first()).data)
                else:
                    return ErrorResponse(
                        code=ErrorCode.NOT_FOUND, message='Education not found!', details={'education': education_id}
                    ).response
            else:  # If resume id is not provided send all resumes for the user
                return Response(
                    EducationFullSerializer(authenticated_user.education_set.filter(
                        resume_section__resume=resume
                    ), many=True).data
                )
        if request.method == 'POST':
            if education_id:
                return ErrorResponse(code=ErrorCode.INVALID_REQUEST,
                                     message='Education Id i not allowed in create request!').response
            new_resume_section = resume.create_section(section_type=ResumeSection.ResumeSectionType.Education)
            payload = request.data
            payload['user'] = authenticated_user.id
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
        if request.method == 'DELETE':
            try:
                education: Education = authenticated_user.education_set.get(
                    id=str(education_id).strip(), resume_section__resume=resume
                )
                resume_sec = education.resume_section
                education.delete()
                resume_sec.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Education.DoesNotExist:
                return ErrorResponse(code=ErrorCode.NOT_FOUND, message=f'Education not found!',
                                     extra={'education': education_id}).response
    except Exception as e:
        error_response = ErrorResponse(code=ErrorCode.INVALID_REQUEST, message=e.__str__(),
                                       extra={'education': education_id})
        logger.exception(f'UUID -> {error_response.uuid} | Unknown error encountered: {e.__str__()}')
        return error_response.response


# Experience CRUD operations
@extend_schema(
    methods=['GET'],
    tags=['Experience object'],
    parameters=[
        OpenApiParameter(
            name='user_id',
            location=OpenApiParameter.PATH,
            description='User ID',
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='resume_id',
            description='Resume ID',
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='experience_id',
            description='Experience ID',
            required=False,
            type=str
        )
    ],
    auth=[],
    responses={
        200: ExperienceFullSerializer or ExperienceFullSerializer(many=True),
        500: ErrorSerializer
    },
    summary="Get one or all experiences",
    description="Returns a user's experience by the experience's id. If no experience id is not specified then returns all experience for the resume as specified in the resume id. Send the id of the base resume to get the user's all base experience. If the experience is not found, a 404 error is returned."
)
@extend_schema(
    methods=['POST'],
    tags=['Experience object'],
    parameters=[
        OpenApiParameter(
            name='user_id',
            location=OpenApiParameter.PATH,
            description='User ID',
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='resume_id',
            description='Resume ID',
            required=True,
            type=str
        )
    ],
    auth=[],
    responses={
        200: ExperienceFullSerializer,
        500: ErrorSerializer
    },
    summary="Add a new experience",
    description="Adds a new experience to the user's resume as specified in the resume id. If a base resume id is provided, the experience is added to the base resume."
)
@extend_schema(
    methods=['DELETE'],
    tags=['Experience object'],
    parameters=[
        OpenApiParameter(
            name='user_id',
            location=OpenApiParameter.PATH,
            description='User ID',
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='resume_id',
            description='Resume ID',
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='experience_id',
            description='Experience ID',
            required=True,
            type=str
        )
    ],
    auth=[],
    responses={
        204: None,
        500: ErrorSerializer
    },
    summary="Delete an experience",
    description="Deletes an experience from the user's resume as specified in the resume id."
)
@api_view(['GET', 'POST', 'DELETE'])
def experience_crud(request, resume_id: str, experience_id: str | None = None):
    try:
        # Ownership Check for all types of API
        authenticated_user: User = request.user
        if not authenticated_user.resume_set.filter(id=resume_id).exists():
            return ErrorResponse(code=ErrorCode.NOT_FOUND, message='Resume not found!', status_code=404).response
        resume: Resume = authenticated_user.resume_set.get(id=resume_id)

        # Main APIs Logic
        if request.method == 'GET':
            if experience_id:
                experience_qs: QuerySet[Experience] = authenticated_user.experience_set.filter(
                    resume_section__resume=resume
                )
                if experience_qs.exists():
                    return Response(ExperienceFullSerializer(experience_qs.first()).data)
                else:
                    return ErrorResponse(
                        code=ErrorCode.NOT_FOUND, message='Experience not found!', details={'experience': experience_id}
                    ).response
            else:  # If resume id is not provided send all resumes for the user
                return Response(
                    ExperienceFullSerializer(
                        authenticated_user.experience_set.filter(resume_section__resume=resume), many=True).data
                    )
        if request.method == 'POST':
            if experience_id:
                return ErrorResponse(code=ErrorCode.INVALID_REQUEST,
                                     message='Experience Id i not allowed in create request!').response
            new_resume_section = resume.create_section(section_type=ResumeSection.ResumeSectionType.Education)
            payload = request.data
            payload['user'] = authenticated_user.id
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
        if request.method == 'DELETE':
            try:
                experience: Experience = authenticated_user.experience_set.get(
                    id=str(experience_id).strip(), resume_section__resume=resume
                )
                resume_sec = experience.resume_section
                experience.delete()
                resume_sec.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)
            except Education.DoesNotExist:
                return ErrorResponse(code=ErrorCode.NOT_FOUND, message=f'Experience not found!',
                                     extra={'experience': experience_id}).response
    except Exception as e:
        error_response = ErrorResponse(code=ErrorCode.INVALID_REQUEST, message=e.__str__(),
                                       extra={'education': experience_id})
        logger.exception(f'UUID -> {error_response.uuid} | Unknown error encountered: {e.__str__()}')
        return error_response.response
