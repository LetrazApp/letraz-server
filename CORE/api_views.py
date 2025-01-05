import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


@api_view(['GET'])
def health_check(request):
    logger.info('Health check: ok')
    return Response({'status': 'ok'})
