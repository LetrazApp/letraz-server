from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import UserInfo
from .serializers import UserInfoSerializer


@api_view(['GET'])
def profile_crud(request, user_id: str):
    if request.method == 'GET':
        user_info_by_user_id: UserInfo = UserInfo.objects.filter(id=user_id).first()
        return Response(UserInfoSerializer(user_info_by_user_id).data)
