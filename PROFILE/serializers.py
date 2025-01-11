from rest_framework import serializers

from CORE.serializers import CountrySerializer
from .models import UserInfo


class UserInfoSerializer(serializers.ModelSerializer):
    country = CountrySerializer()

    class Meta:
        model = UserInfo
        fields = (
            'id', 'title', 'first_name', 'last_name', 'email', 'phone', 'dob',
            'nationality', 'address', 'city', 'postal', 'country', 'website',
            'profile_text', 'created_at', 'updated_at'
        )


class UserInfoUpsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = "__all__"
