import uuid
from rest_framework.response import Response


class ErrorResponse:
    def __init__(self, code, message, details=None, extra=None, status_code=400):
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
        }, 400)
