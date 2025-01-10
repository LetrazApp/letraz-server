from rest_framework import serializers

from CORE.serializers import CountrySerializer
from .models import UserInfo


class UserInfoSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()

    class Meta:
        model = UserInfo
        fields = (
            'id', 'title', 'first_name', 'last_name', 'email', 'phone', 'dob',
            'nationality', 'address', 'city', 'postal', 'country', 'website',
            'profile_text', 'created_at', 'updated_at'
        )

    @staticmethod
    def get_country(user_info: UserInfo):
        return CountrySerializer(user_info.country).data if user_info.country else None
