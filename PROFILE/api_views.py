from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view
from rest_framework.response import Response

from CORE.serializers import ErrorSerializer
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from .models import UserInfo
from .serializers import UserInfoSerializer, UserInfoUpsertSerializer


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
    responses={200: UserInfoSerializer, 500: ErrorSerializer},
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
    request=UserInfoUpsertSerializer,
    responses={
        201: UserInfoSerializer,
        400: ErrorSerializer
    }
)
@api_view(['GET', 'POST'])
def user_info_crud(request, user_id: str | None = None):
    if request.method == 'GET':
        user_info_by_user_id_qs: QuerySet[UserInfo] = UserInfo.objects.filter(id=user_id)
        if user_info_by_user_id_qs.exists():
            return Response(UserInfoSerializer(user_info_by_user_id_qs.first()).data)
        else:
            return ErrorResponse(
                code=ErrorCode.NOT_FOUND, message='User Profile not found!', details={'user': user_id}
            ).response
    if request.method == 'POST':
        user_info_ser: UserInfoUpsertSerializer = UserInfoUpsertSerializer(data=request.data)
        if UserInfo.objects.filter(id=request.data.get('id')).exists():
            return ErrorResponse(
                code=ErrorCode.ALREADY_EXISTS, message=f'User info already exists!',
                details={'user': request.data.get('id')}
            ).response
        if user_info_ser.is_valid():
            user_info = user_info_ser.save()
            return Response(UserInfoSerializer(user_info).data)
        else:
            return ErrorResponse(
                code=ErrorCode.INVALID_REQUEST, message=f'Invalid Data provided!',
                details=user_info_ser.errors, extra={'data': request.data}
            ).response
