import logging
from rest_framework import serializers
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from RESUME.models import Resume
from RESUME.serializers import ResumeFullSerializer
from CORE.serializers import ErrorEnvelopeSerializer
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from letraz_server.contrib.admin_auth import admin_api_key_required
from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)

ERROR_ENVELOPE = ErrorEnvelopeSerializer

# Admin Resume Management
@extend_schema(
    methods=['GET'],
    tags=['Admin - Resume'],
    auth=[],
    responses={200: ResumeFullSerializer, 401: ERROR_ENVELOPE, 404: ERROR_ENVELOPE, 400: ERROR_ENVELOPE},
    summary="[ADMIN] Get resume data",
    description="Returns complete resume data including all associated sections (PersonalInfo, Education, Experience, Skills, Projects, Certifications). Requires admin API key authentication.",
    parameters=[
        OpenApiParameter(
            name='x-admin-api-key',
            location='header',
            required=True,
            type=OpenApiTypes.STR,
            description='Admin API key for authentication'
        ),
        OpenApiParameter(
            name='resume_id',
            location='path',
            required=True,
            type=OpenApiTypes.UUID,
            description='The unique identifier of the resume to retrieve'
        )
    ]
)
@api_view(['GET'])
@permission_classes([AllowAny])
@admin_api_key_required
def admin_resume_get(request, resume_id):
    """
    Admin endpoint to get complete resume data by ID
    """
    try:
        resume = Resume.objects.get(id=resume_id)
        logger.info(f"Admin accessed resume {resume_id} for user {resume.user.id}")
        return Response(ResumeFullSerializer(resume).data)
    except Resume.DoesNotExist:
        error_response = ErrorResponse(
            code=ErrorCode.NOT_FOUND,
            message='Resume not found!',
            details={'resume_id': resume_id},
            status_code=status.HTTP_404_NOT_FOUND
        )
        logger.warning(f'UUID -> {error_response.uuid} | Resume not found: {resume_id}')
        return error_response.response
    except Exception as e:
        error_response = ErrorResponse(
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=e.__str__(),
            details={'resume_id': resume_id},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        logger.exception(f'UUID -> {error_response.uuid} | Unknown error encountered: {e.__str__()}')
        return error_response.response 