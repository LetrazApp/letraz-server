from rest_framework import serializers

from CORE.serializers import CountrySerializer
from .models import User


class UserSerializer(serializers.ModelSerializer):
    country = CountrySerializer()

    class Meta:
        model = User
        fields = (
            'id', 'title', 'first_name', 'last_name', 'email', 'phone', 'dob',
            'nationality', 'address', 'city', 'postal', 'country', 'website',
            'profile_text', 'created_at', 'updated_at'
        )
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserUpsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        read_only_fields = ['id', 'created_at', 'updated_at']
        exclude = ('groups', 'user_permissions')
