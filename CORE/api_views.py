import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse, ErrorResponseList
from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


@api_view(['GET'])
def health_check(request):
    logger.info('Health check: ok')
    return Response({'status': 'ok'})


@api_view(['GET'])
def error_example(request):
    error_response: ErrorResponse = ErrorResponse(
        code=ErrorCode.INVALID, message='Example error!',
        details='Example error details!', extra='Example extra data!'
    )
    logger.info(f'UUID -> {error_response.uuid} | Error example was called!')
    return error_response.response


@api_view(['GET'])
def error_list_example(request):
    error_list: ErrorResponseList = ErrorResponseList('Multiple error found!')
    for i in range(1, 5):
        error_response: ErrorResponse = ErrorResponse(
            code=ErrorCode.INVALID, message=f'Example error - {i+1}!',
            details='Example error details!', extra='Example extra data!'
        )
        logger.info(f'UUID -> {error_response.uuid} | Error Response List example was called!')
        error_list.add_error_obj(error_response)
    return error_list.get_error_list_response()
