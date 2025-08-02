from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
from CORE.services import CoreService
from JOB.services import ScrapeJobCallbackService

def grpc_handlers(server):
    core_app_registry = AppHandlerRegistry(app_name='CORE', server=server)
    core_app_registry.register(CoreService)

    job_app_registry = AppHandlerRegistry(app_name='JOB', server=server)
    job_app_registry.register(ScrapeJobCallbackService)
