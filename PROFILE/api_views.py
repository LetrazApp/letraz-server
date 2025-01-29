import logging
from json import JSONDecodeError

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from CORE.serializers import ErrorSerializer
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from letraz_server.settings import PROJECT_NAME
from .models import User
from .serializers import UserSerializer, UserUpsertSerializer

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)

@extend_schema(
    methods=['GET'],
    tags=['User'],
    responses={200: UserSerializer, 500: ErrorSerializer},
    summary="Get user info",
)
@extend_schema(
    methods=['PATCH'],
    tags=['User'],
    summary="Add a new user info",
    request=UserUpsertSerializer,
    responses={201: UserSerializer, 400: ErrorSerializer}
)
class UserCRUD(APIView):
    """
    API reference for all available endpoints for the User Profile Info object.
    Contains endpoints for getting user profile info for a user or update their details.
    """
    def __init__(self):
        self.authenticated_user: User | None = None
        self.error: ErrorResponse | None = None
        super(UserCRUD, self).__init__()

    def __set_meta(self, request):
        """
        Retrieve check and set authenticated user
        """
        # Ownership Check for all types of API
        self.authenticated_user: User = request.user

    def get(self, request):
        """
        Returns a user's user info by the user's id. If the user info is not found, a 404 error is returned.
        """
        self.__set_meta(request)
        try:
            return Response(UserSerializer(self.authenticated_user).data)
        except Exception as ex:
            error_response = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message='An unknown error occurred while fetching your information!',
                details=ex.__str__(), status_code=500
            )
            logger.exception(f'{error_response.uuid} An unknown error occurred while fetching your information {ex}')
            return error_response.response

    def patch(self, request):
        """
        Send a PATCH request with the user's data to add or upsert a user info entry.
        If the user info already exists, it will be updated. If the user info does not exist, it will be created.
        """
        self.__set_meta(request)
        try:
            user_ser: UserUpsertSerializer = UserUpsertSerializer(self.authenticated_user, data=request.data, partial=True)
            if user_ser.is_valid():
                user_info = user_ser.save()
                return Response(UserSerializer(user_info).data)
            else:
                return ErrorResponse(
                    code=ErrorCode.INVALID_REQUEST, message=f'Invalid Data provided!',
                    details=user_ser.errors, extra={'data': request.data}
                ).response
        except Exception as ex:
            error_response = ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message='An unknown error occurred while fetching your information!',
                details=ex.__str__(), status_code=500
            )
            logger.exception(f'{error_response.uuid} An unknown error occurred while fetching your information {ex}')
            return error_response.response
