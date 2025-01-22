import logging

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from CORE.serializers import ErrorSerializer
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from letraz_server.settings import PROJECT_NAME
from .serializers import UserSerializer, UserUpsertSerializer

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


@extend_schema(
    methods=['GET'],
    tags=['User info'],
    parameters=[
        OpenApiParameter(
            name='user_id',
            location=OpenApiParameter.PATH,
            description='User ID',
            required=True,
            type=str
        )
    ],
    auth=[],
    responses={200: UserSerializer, 500: ErrorSerializer},
    summary="Get user info",
    description="Returns a user's user info by the user's id. If the user info is not found, a 404 error is returned."
)
@extend_schema(
    methods=['POST'],
    tags=['User info'],
    auth=[],
    parameters=[],
    summary="Add a new user info",
    description="Send a POST request with the user's data to add a upsert a new user info entry. If the user info already exists, it will be updated. If the user info does not exist, it will be created.",
    request=UserUpsertSerializer,
    responses={
        201: UserSerializer,
        400: ErrorSerializer
    }
)
@api_view(['GET'])
def user_info_crud(request):
    if request.method == 'GET':
        try:
            return Response(UserSerializer(request.user).data)
        except Exception as ex:
            error_response = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message='An unknown error occurred while fetching your information!',
                details=ex.__str__(),
                status_code=500
            )
            logger.exception(f'{error_response.uuid} An unknown error occurred while fetching your information {ex}')
            return error_response.response
