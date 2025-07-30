import logging
from django_socio_grpc import generics
from django_socio_grpc.decorators import grpc_action
from CORE.serializers import HealthCheckSerializer
from letraz_server import settings
from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


class CoreService(generics.GenericService):
    @grpc_action(
        request=[],
        response=HealthCheckSerializer,
    )
    async def HealthCheck(self, request, context):

        response = {'instance_id': settings.INSTANCE_ID, 'status': 'OPERATIONAL', 'details': {
            'sentry': settings.SENTRY_STATUS, "clerk": settings.CLERK_STATUS, "db": settings.DB_STATUS,
            'util_service': settings.UTIL_GRPC_CHANNEL_STATUS
        }}
        if not (settings.CLERK_STATUS == settings.DB_STATUS == settings.UTIL_GRPC_CHANNEL_STATUS == "OPERATIONAL"):
            response = {'instance_id': settings.INSTANCE_ID, 'status': 'DEGRADED', 'details': {
                'sentry': settings.SENTRY_STATUS, "clerk": settings.CLERK_STATUS, "db": settings.DB_STATUS,
                'util_service': settings.UTIL_GRPC_CHANNEL_STATUS
            }}
            logger.error(
                f'status: OPERATIONAL, details: <sentry: {settings.SENTRY_STATUS}, "clerk": {settings.CLERK_STATUS}, "db": {settings.DB_STATUS}, "util_service": {settings.UTIL_GRPC_CHANNEL_STATUS}>')
        serializer = HealthCheckSerializer(data=response)
        serializer.is_valid(raise_exception=True)
        return serializer.message
