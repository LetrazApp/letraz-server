import logging
from django_socio_grpc import generics
from django_socio_grpc.exceptions import GRPCException, StatusCode, NotFound
from requests.models import Response

from CORE.models import Process
from JOB.proto_serialzers import ScrapeJobCallbackRequestSerializer, ScrapeJobResponseSerializer
from letraz_server.settings import PROJECT_NAME
from django_socio_grpc.decorators import grpc_action

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


class ScrapeJobCallbackService(generics.GenericService):

    @grpc_action(
        request=ScrapeJobCallbackRequestSerializer,
        response=ScrapeJobResponseSerializer,  # Empty response
    )
    async def ScrapeJobCallBack(self, request, context):
        # Your implementation here
        print(request)
        process_qs = Process.objects.filter(util_id=request.processId)
        if not await process_qs.aexists():
            raise NotFound("No process found with that util_id")

        return ScrapeJobResponseSerializer("OK").message