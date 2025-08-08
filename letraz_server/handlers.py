from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
from CORE.services import CoreService
from JOB.services import ScrapeJobCallbackService
from RESUME.services import TailorResumeCallBackService, GenerateScreenshotCallBackService

def grpc_handlers(server):
    core_app_registry = AppHandlerRegistry(app_name='CORE', server=server)
    core_app_registry.register(CoreService)

    job_app_registry = AppHandlerRegistry(app_name='JOB', server=server)
    job_app_registry.register(ScrapeJobCallbackService)

    resume_app_registry = AppHandlerRegistry(app_name='RESUME', server=server)
    resume_app_registry.register(TailorResumeCallBackService)
    resume_app_registry.register(GenerateScreenshotCallBackService)
