from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
from CORE.services import CoreService

def grpc_handlers(server):
    app_registry = AppHandlerRegistry(app_name='CORE', server=server)
    app_registry.register(CoreService)