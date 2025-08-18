import functools
import logging
import uuid
from rest_framework import status
from rest_framework.response import Response
from letraz_server.contrib.constant import ErrorCode
from letraz_server.settings import PROJECT_NAME

__module_name = f'{PROJECT_NAME}.' + __name__
logger = logging.getLogger(__module_name)


class ErrorResponse:
    def __init__(self, code, message, details=None, extra=None, status_code=status.HTTP_400_BAD_REQUEST):
        self.uuid = str(uuid.uuid4())
        self.code = code
        self.message = message
        self.details = details
        self.extra = extra
        self.response = Response({
            'error': {
                'uuid': self.uuid,
                'code': self.code,
                'message': self.message,
                'details': self.details,
                'extra': self.extra
            }
        }, status_code)

    def to_dict(self):
        return self.response.data


class ErrorResponseList:
    def __init__(self, message):
        self.code = 'ERROR_LIST'
        self.errors = []
        self.message = message

    def add_error(self, code, msg, details=None, extra=None):
        self.errors.append(ErrorResponse(code, msg, details, extra).to_dict())

    def add_error_obj(self, error_response: ErrorResponse):
        self.errors.append(error_response.to_dict())

    def get_error_list_response(self):
        return Response({
            'code': self.code,
            'errors': self.errors,
            'message': self.message
        }, status.HTTP_400_BAD_REQUEST)


def letraz_restapi_exception_handled(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_response = ErrorResponse(code=ErrorCode.INTERNAL_SERVER_ERROR, message=e.__str__(),
                                           status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            logger.exception(f'[SOURCE: {func.__module__}.{func.__name__}()] '
                             f'UUID -> {error_response.uuid} | Unknown error encountered: {e.__str__()}')
            return error_response.response

    return wrapper
