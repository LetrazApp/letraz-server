import logging

from django.db.models import QuerySet
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from CORE.models import Waitlist
from CORE.serializers import WaitlistSerializer
from letraz_server.contrib.constant import ErrorCode
from letraz_server.contrib.error_framework import ErrorResponse, ErrorResponseList
from letraz_server.settings import PROJECT_NAME, SENTRY_STATUS

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


@api_view(['GET'])
def health_check(request):
    logger.info(f'HEALTH_CHECK: ok | SENTRY: {SENTRY_STATUS}')
    return Response({'status': 'ok', 'sentry': SENTRY_STATUS})


@api_view(['GET'])
def error_example(request):
    error_response: ErrorResponse = ErrorResponse(
        code=ErrorCode.INVALID, message='Example error!',
        details='Example error details!', extra='Example extra data!'
    )
    logger.error(f'UUID -> {error_response.uuid} | Error example was called!')
    return error_response.response


@api_view(['GET'])
def error_list_example(request):
    error_list: ErrorResponseList = ErrorResponseList('Multiple error found!')
    for i in range(1, 5):
        error_response: ErrorResponse = ErrorResponse(
            code=ErrorCode.INVALID, message=f'Example error - {i + 1}!',
            details='Example error details!', extra='Example extra data!'
        )
        logger.error(f'UUID -> {error_response.uuid} | Error Response List example was called!')
        error_list.add_error_obj(error_response)
    return error_list.get_error_list_response()


@api_view(['GET', 'POST'])
def waitlist_crud(request):
    try:
        if request.method == 'GET':
            waitlist_qs: QuerySet[Waitlist] = Waitlist.objects.all().order_by('waiting_number')
            return Response(WaitlistSerializer(waitlist_qs, many=True).data)
        if request.method == 'POST':
            waitlist_serializer: WaitlistSerializer = WaitlistSerializer(data=request.data)
            if waitlist_serializer.is_valid():
                waitlist: Waitlist = waitlist_serializer.save()
                return Response(WaitlistSerializer(waitlist).data, status=status.HTTP_201_CREATED)
            else:
                return ErrorResponse(
                    code=ErrorCode.INVALID_REQUEST, message=f'Invalid Data provided!',
                    details=waitlist_serializer.errors, extra={'data': request.data}
                ).response
    except Exception as e:
        error_response = ErrorResponse(code=ErrorCode.INVALID_REQUEST, message=e.__str__(),
                                       extra={'data': request.data})
        logger.exception(f'UUID -> {error_response.uuid} | Unknown error encountered: {e.__str__()}')
        return error_response.response
