import logging
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, OpenApiTypes, inline_serializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from CORE.models import Waitlist, Skill
from CORE.serializers import WaitlistSerializer, HealthCheckSerializer, SkillSerializer, ErrorEnvelopeSerializer, ErrorListEnvelopeSerializer
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse, ErrorResponseList, letraz_restapi_exception_handled
from letraz_server import settings
from letraz_server.settings import PROJECT_NAME
from letraz_server.contrib.sdks.knock import KnockSDK

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)

ERROR_ENVELOPE = ErrorEnvelopeSerializer

# Health Check
@extend_schema(
    methods=['GET'],
    tags=['Core APIs'],
    auth=[],
    responses={200: HealthCheckSerializer, 503: HealthCheckSerializer},
    summary="Get server health status",
    description="Returns the server health status. The sentry status is also included in the response"
)
@api_view(['GET'])
@permission_classes([AllowAny])
@letraz_restapi_exception_handled
def health_check(request):
    response = {'instance_id':  settings.INSTANCE_ID,'status': 'OPERATIONAL', 'details': {
        'sentry': settings.SENTRY_STATUS, "clerk": settings.CLERK_STATUS, "db": settings.DB_STATUS, 'util_service': settings.UTIL_GRPC_CHANNEL_STATUS
    }}
    if not (settings.CLERK_STATUS == settings.DB_STATUS == settings.UTIL_GRPC_CHANNEL_STATUS == "OPERATIONAL"):
        response = {'instance_id':  settings.INSTANCE_ID,'status': 'DEGRADED', 'details': {
            'sentry': settings.SENTRY_STATUS, "clerk": settings.CLERK_STATUS, "db": settings.DB_STATUS, 'util_service': settings.UTIL_GRPC_CHANNEL_STATUS
        }}
        logger.error(
            f'status: OPERATIONAL, details: <sentry: {settings.SENTRY_STATUS}, "clerk": {settings.CLERK_STATUS}, "db": {settings.DB_STATUS}, "util_service": {settings.UTIL_GRPC_CHANNEL_STATUS}>')
        return Response(response, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response(response, status=status.HTTP_200_OK)


# Error Example
@extend_schema(
    methods=['GET'],
    tags=['Core APIs'],
    auth=[],
    responses={400: ERROR_ENVELOPE},
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
    responses={400: ErrorListEnvelopeSerializer},
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
    responses={200: WaitlistSerializer(many=True), 400: ERROR_ENVELOPE},
    summary="Get all waitlists",
    description="Returns all waitlist entries ordered by waiting number. The waiting number is the order in which the user joined the waitlist."
)
@extend_schema(
    methods=['POST'],
    tags=['Waitlist'],
    auth=[],
    summary="Add a new waitlist",
    description="Send a POST request with the email of the user and optionally a ref string to add a new waitlist entry. Returns the newly created waitlist entry with the waiting number and created_at timestamp. A corresponding Knock user will also be created with the same ID and email.",
    request=WaitlistSerializer,
    responses={
        201: WaitlistSerializer,
        400: ERROR_ENVELOPE
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
                
                # Create corresponding Knock user
                try:
                    knock_sdk = KnockSDK(api_key=settings.KNOCK_API_KEY)
                    if knock_sdk.is_available():
                        # Prepare user properties for Knock
                        user_properties = {
                            'email_address': waitlist.email,
                            'created_via': 'waitlist',
                            'waiting_number': waitlist.waiting_number
                        }
                        
                        # Create user in Knock with waitlist ID as user ID
                        success = knock_sdk.identify_user(
                            user_id=str(waitlist.id),
                            properties=user_properties
                        )
                        
                        if success:
                            logger.info(f"Successfully created Knock user for waitlist entry {waitlist.id}")
                        else:
                            logger.warning(f"Failed to create Knock user for waitlist entry {waitlist.id}")
                    else:
                        logger.warning("Knock SDK not available - skipping user creation")
                        
                except Exception as knock_error:
                    # Log the error but don't fail the waitlist creation
                    logger.error(f"Error creating Knock user for waitlist entry {waitlist.id}: {str(knock_error)}")
                
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
        400: ERROR_ENVELOPE
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

@extend_schema(
    methods=['GET'],
    tags=['Skill object'],
    auth=[],
    summary="Get all global skill categories",
    responses={
        200: {
            'type': 'array',
            'items': {'type': 'string'}
        },
        400: ERROR_ENVELOPE
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_skill_categories(request):
    """
    Get all skills available in the database across users and resumes
    """
    try:
        return Response(list({skill.category for skill in Skill.objects.all()}))
    except Exception as e:
        error_response = ErrorResponse(code=ErrorCode.INVALID_REQUEST, message=e.__str__(),
                                       extra={'data': request.data})
        logger.exception(f'UUID -> {error_response.uuid} | Unknown error encountered: {e.__str__()}')
        return error_response.response
