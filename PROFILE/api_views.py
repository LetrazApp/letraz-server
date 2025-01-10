from django.db.models import QuerySet
from rest_framework.decorators import api_view
from rest_framework.response import Response

from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse
from .models import UserInfo
from .serializers import UserInfoSerializer


@api_view(['GET'])
def profile_crud(request, user_id: str):
    if request.method == 'GET':
        user_info_by_user_id_qs: QuerySet[UserInfo] = UserInfo.objects.filter(id=user_id)
        if user_info_by_user_id_qs.exists():
            return Response(UserInfoSerializer(user_info_by_user_id_qs.first()).data)
        else:
            return ErrorResponse(
                code=ErrorCode.NOT_FOUND, message='User Profile not found!', details={'user': user_id}
            ).response
