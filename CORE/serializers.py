from random import choices

from rest_framework import serializers
from .models import Country, Waitlist, Skill


class HealthDetailsSerializer(serializers.Serializer):
    SENTRY_STATUS_CHOICES = [
        ('OPERATIONAL', 'OPERATIONAL'),
        ('UNINITIALIZED', 'UNINITIALIZED'),
        ('FAILED', 'FAILED')
    ]
    CLERK_STATUS_CHOICES = [
        ('OPERATIONAL', 'OPERATIONAL'),
        ('DOWN', 'DOWN')
    ]
    DB_STATUS_CHOICES = [
        ('OPERATIONAL', 'OPERATIONAL'),
        ('DEGRADED', 'DEGRADED'),
        ('FATAL', 'FATAL')
    ]
    sentry = serializers.ChoiceField(
        SENTRY_STATUS_CHOICES,
        help_text='The status of the sentry integration. If False, the sentry is not initialized, possibly due to absense of environment variables, which is expected or misconfigured initialization.'
    )
    clerk = serializers.ChoiceField(
        CLERK_STATUS_CHOICES,
        help_text='The health status of Clerk integration. The status can be OPERATIONAL or DOWN.')
    DB = serializers.ChoiceField(
        DB_STATUS_CHOICES,
        help_text='The health status of  Clerk connection. The status can be OPERATIONAL, DEGRADED or FATAL.')


class HealthCheckSerializer(serializers.Serializer):
    STATUS_CHOICES = [
        ('OPERATIONAL', 'OPERATIONAL'),
        ('DEGRADED', 'DEGRADED')
    ]

    status = serializers.ChoiceField(
        help_text='The health status of the server. The status can be ok, degraded or failing.', choices=STATUS_CHOICES)
    details = HealthDetailsSerializer()


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class ErrorSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(
        help_text='The unique identifier for the error response. This is useful for tracking the error in the logs and in Sentry if it is enabled.'
    )
    code = serializers.CharField(
        help_text='The error code that is unique to the error type. This can be used to identify the error type and can be used for debugging.'
    )
    message = serializers.CharField(
        help_text='The error message that is human readable and can be used to understand the error. Usually fit to be displayed to the user.'
    )
    details = serializers.CharField(
        help_text='The error details that can be used to understand the error in more detail. This can be used for debugging purposes.'
    )
    extra = serializers.CharField(
        help_text='The extra data that can be used to understand the error in more detail. This is usually not displayed to the user and might include stacktrace and sensitive information.'
    )


class ErrorListSerializer(serializers.Serializer):
    code = serializers.CharField(
        help_text='The error code that is unique to the error type. This can be used to identify the error type and can be used for debugging.'
    )
    errors = ErrorSerializer(many=True)
    message = serializers.CharField(
        help_text='The error message that is human readable and can be used to understand the error. Usually fit to be displayed to the user.'
    )


class WaitlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waitlist
        fields = '__all__'
        read_only_fields = ['id', 'waiting_number', 'created_at', 'has_access']


class WaitlistUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waitlist
        fields = ['has_access']


class WaitlistBulkUpdateSerializer(serializers.Serializer):
    waitlist_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text='List of waitlist entry IDs to update',
        allow_empty=False
    )
    has_access = serializers.BooleanField(
        help_text='Whether to grant or revoke access for the selected users'
    )


class AliasSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        read_only_fields = ['id', 'updated_at', 'created_at']
        exclude = ['alias', ]


class SkillSerializer(serializers.ModelSerializer):
    alias = AliasSkillSerializer(many=True)

    class Meta:
        model = Skill
        fields = ('id', 'category', 'name',
                  'preferred', 'alias',
                  'updated_at', 'created_at')
        read_only_fields = ['id', 'updated_at', 'created_at']
