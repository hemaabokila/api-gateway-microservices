from flask import jsonify, current_app, request
from werkzeug.exceptions import HTTPException 
from http import HTTPStatus
import traceback

class APIError(HTTPException):
    """Base class for custom API errors."""
    code = HTTPStatus.INTERNAL_SERVER_ERROR.value
    message = "An unexpected error occurred."
    
    def __init__(self, message=None, code=None, payload=None):
        super().__init__(description=message)
        if message:
            self.message = message
        if code:
            self.code = code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        if self.code:
            rv['status_code'] = self.code
        return rv

class BadRequestError(APIError):
    code = HTTPStatus.BAD_REQUEST.value
    message = "Bad request."

class UnauthorizedError(APIError):
    code = HTTPStatus.UNAUTHORIZED.value
    message = "Authentication required or invalid credentials."

class ForbiddenError(APIError):
    code = HTTPStatus.FORBIDDEN.value
    message = "You do not have permission to access this resource."

class NotFoundError(APIError):
    code = HTTPStatus.NOT_FOUND.value
    message = "The requested resource was not found."

class ConflictError(APIError):
    code = HTTPStatus.CONFLICT.value
    message = "Conflict with current state of the resource."

class ServiceUnavailableError(APIError):
    code = HTTPStatus.SERVICE_UNAVAILABLE.value
    message = "Service is temporarily unavailable. Please try again later."

class TooManyRequestsError(APIError):
    code = HTTPStatus.TOO_MANY_REQUESTS.value
    message = "Too many requests. Please try again after some time."


def handle_api_error(e):
    """
    Handles custom APIError exceptions and returns a JSON response.
    Includes traceback in debug mode.
    """
    if isinstance(e, APIError):
        current_app.logger.warning(f"API Error ({e.code}): {e.message} - Path: {request.path}")
        response = jsonify(e.to_dict())
        response.status_code = e.code
    elif isinstance(e, HTTPException):
        current_app.logger.warning(f"HTTP Exception ({e.code}): {e.description} - Path: {request.path}")
        response = jsonify({
            "message": e.description,
            "status_code": e.code
        })
        response.status_code = e.code
    else:
        current_app.logger.exception(f"Unhandled Exception: {e} - Path: {request.path}")
        message = "An unexpected error occurred."
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
        
        error_response = {
            "message": message,
            "status_code": status_code
        }
        
        if current_app.config.get('DEBUG'):
            error_response["exception"] = str(e)
            error_response["traceback"] = traceback.format_exc().splitlines()
        
        response = jsonify(error_response)
        response.status_code = status_code
    
    return response

def register_error_handlers(app):
    """
    Registers custom and generic error handlers for the Flask application.
    """
    app.register_error_handler(APIError, handle_api_error)
    app.register_error_handler(BadRequestError, handle_api_error)
    app.register_error_handler(UnauthorizedError, handle_api_error)
    app.register_error_handler(ForbiddenError, handle_api_error)
    app.register_error_handler(NotFoundError, handle_api_error)
    app.register_error_handler(ConflictError, handle_api_error)
    app.register_error_handler(ServiceUnavailableError, handle_api_error)
    app.register_error_handler(TooManyRequestsError, handle_api_error)

    app.register_error_handler(HTTPStatus.NOT_FOUND.value, handle_api_error)
    app.register_error_handler(HTTPStatus.INTERNAL_SERVER_ERROR.value, handle_api_error)

    app.register_error_handler(Exception, handle_api_error)
