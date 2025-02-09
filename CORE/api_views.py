import logging
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from CORE.models import Waitlist, Skill
from CORE.serializers import WaitlistSerializer, ErrorSerializer, ErrorListSerializer, HealthCheckSerializer, SkillSerializer
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse, ErrorResponseList
from letraz_server import settings
from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


# Health Check
@extend_schema(
    methods=['GET'],
    tags=['Core APIs'],
    auth=[],
    responses={200: HealthCheckSerializer, 500: ErrorSerializer},
    summary="Get server health status",
    description="Returns the server health status. The sentry status is also included in the response"
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    response = {'status': 'OPERATIONAL', 'details': {
        'sentry': settings.SENTRY_STATUS, "clerk": settings.CLERK_STATUS, "DB": settings.DB_STATUS
    }}
    if (not settings.CLERK_STATUS == 'OPERATIONAL') or (not settings.DB_STATUS == 'OPERATIONAL'):
        response = {'status': 'DEGRADED', 'details': {
            'sentry': settings.SENTRY_STATUS, "clerk": settings.CLERK_STATUS, "DB": settings.DB_STATUS
        }}
        logger.error(
            f'status: OPERATIONAL, details: <sentry: {settings.SENTRY_STATUS}, "clerk": {settings.CLERK_STATUS}, "DB": {settings.DB_STATUS}>')
        return Response(response, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response(response, status=status.HTTP_200_OK)


# Error Example
@extend_schema(
    methods=['GET'],
    tags=['Core APIs'],
    auth=[],
    responses={500: ErrorSerializer},
    summary="Get sample error",
    description="Returns a sample error response that might occur if an operation fails. Note that the HTTP status would raise an error and that's a normal behavior."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def error_example(request):
    error_response: ErrorResponse = ErrorResponse(
        code=ErrorCode.INVALID, message='Example error!',
        details='Example error details!', extra='Example extra data!'
    )
    logger.error(f'UUID -> {error_response.uuid} | Error example was called!')
    return error_response.response


# Error List Example
@extend_schema(
    methods=['GET'],
    tags=['Core APIs'],
    auth=[],
    responses={500: ErrorListSerializer},
    summary="Get sample error (bulk operations)",
    description="Returns a sample error response that might occur if one or more operations fails from a bulk operation request. Note that the HTTP status would raise an error and that's a normal behavior."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def error_list_example(request):
    error_list: ErrorResponseList = ErrorResponseList('Multiple error found!')
    for i in range(1, 5):
        error_response: ErrorResponse = ErrorResponse(
            code=ErrorCode.INVALID, message=f'Example error - {i + 1}!',
            details='Example error details!', extra='Example extra data!'
        )
        logger.error(f'UUID -> {error_response.uuid} | Error Response List example was called!')
        error_list.add_error_obj(error_response)
    return error_list.get_error_list_response()


# Waitlist CRUD
@extend_schema(
    methods=['GET'],
    tags=['Waitlist'],
    auth=[],
    responses={200: WaitlistSerializer(many=True), 500: ErrorSerializer},
    summary="Get all waitlists",
    description="Returns all waitlist entries ordered by waiting number. The waiting number is the order in which the user joined the waitlist."
)
@extend_schema(
    methods=['POST'],
    tags=['Waitlist'],
    auth=[],
    summary="Add a new waitlist",
    description="Send a POST request with the email of the user and optionally a ref string to add a new waitlist entry. Returns the newly created waitlist entry with the waiting number and created_at timestamp.",
    request=WaitlistSerializer,
    responses={
        201: WaitlistSerializer,
        400: ErrorSerializer
    }
)
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def waitlist_crud(request):
    try:
        if request.method == 'GET':
            waitlist_qs: QuerySet[Waitlist] = Waitlist.objects.all().order_by('waiting_number')
            return Response(WaitlistSerializer(waitlist_qs, many=True).data)
        if request.method == 'POST':
            waitlist_serializer: WaitlistSerializer = WaitlistSerializer(data=request.data)
            if waitlist_serializer.is_valid():
                waitlist: Waitlist = waitlist_serializer.save()
                return Response(WaitlistSerializer(waitlist).data, status=status.HTTP_201_CREATED)
            else:
                return ErrorResponse(
                    code=ErrorCode.INVALID_REQUEST, message=f'Invalid Data provided!',
                    details=waitlist_serializer.errors, extra={'data': request.data}
                ).response
    except Exception as e:
        error_response = ErrorResponse(code=ErrorCode.INVALID_REQUEST, message=e.__str__(),
                                       extra={'data': request.data})
        logger.exception(f'UUID -> {error_response.uuid} | Unknown error encountered: {e.__str__()}')
        return error_response.response


@extend_schema(
    methods=['GET'],
    tags=['Skill object'],
    auth=[],
    summary="Get all global skills",
    responses={
        200: SkillSerializer(many=True),
        400: ErrorSerializer
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_skill(request):
    """
    Get all skills available in the database across users and resumes
    """
    try:
        return Response(SkillSerializer(Skill.objects.all(), many=True).data)
    except Exception as e:
        error_response = ErrorResponse(code=ErrorCode.INVALID_REQUEST, message=e.__str__(),
                                       extra={'data': request.data})
        logger.exception(f'UUID -> {error_response.uuid} | Unknown error encountered: {e.__str__()}')
        return error_response.response
