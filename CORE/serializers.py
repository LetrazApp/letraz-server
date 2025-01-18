from random import choices

from rest_framework import serializers
from .models import Country, Waitlist


class HealthCheckSerializer(serializers.Serializer):
    STATUS_CHOICES = [
        ('OK', 'ok'),
        ('DEGRADED', 'degraded'),
        ('FAILING', 'failing')
    ]

    status = serializers.CharField(help_text='The health status of the server. The status can be ok, degraded or failing.')
    sentry = serializers.BooleanField(
        default=True,
        help_text='The status of the sentry integration. If False, the sentry is not initialized, possibly due to absense of environment variables, which is expected or misconfigured initialization.'
    )

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
        read_only_fields = ['id', 'waiting_number', 'created_at']
