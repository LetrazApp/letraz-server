from django.db.models import QuerySet
from rest_framework.decorators import api_view
from rest_framework.response import Response

from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from .models import UserInfo
from .serializers import UserInfoSerializer, UserInfoUpsertSerializer


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
