import jwt
import os
from typing import Optional, Any
from flask import request, jsonify, Response, current_app
from http import HTTPStatus
from ..middleware_manager import Middleware
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(Middleware):
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET_KEY')
        if not self.jwt_secret:
            logger.error("JWT_SECRET_KEY is not set. Authentication will not work.")
        self.excluded_paths = []

    def set_excluded_paths(self, paths: list):
        self.excluded_paths = paths
        logger.info(f"AuthMiddleware excluded paths set to: {self.excluded_paths}")

    def process_request(self, request: Any) -> Optional[Response]:
        if not self.excluded_paths and current_app:
            self.set_excluded_paths(current_app.config.get('AUTH_EXCLUDED_PATHS', []))

        for excluded_path in self.excluded_paths:

            if excluded_path.endswith('/<path:path>'):
                base_path = excluded_path.replace('/<path:path>', '')
                if request.path.startswith(base_path):
                    logger.debug(f"Path {request.path} excluded from auth by {excluded_path}")
                    return None 
            elif request.path == excluded_path:
                logger.debug(f"Path {request.path} excluded from auth by exact match")
                return None 

        if request.path == '/':
            logger.debug(f"Root path {request.path} excluded from auth.")
            return None
        
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.warning("Authorization header missing for protected route.")
            return Response(response=jsonify({"message": "Authorization header missing"}).data,
                            status=HTTPStatus.UNAUTHORIZED.value,
                            mimetype='application/json')

        try:
            token_type, token = auth_header.split(' ', 1)
            if token_type.lower() != 'bearer':
                logger.warning("Invalid token type. Expected Bearer.")
                return Response(response=jsonify({"message": "Invalid token type"}).data,
                                status=HTTPStatus.UNAUTHORIZED.value,
                                mimetype='application/json')

            if not self.jwt_secret:
                raise ValueError("JWT_SECRET_KEY is not configured.")

            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            request.user = payload
            logger.debug(f"JWT authenticated for user: {payload.get('user_id')}")
            return None
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired.")
            return Response(response=jsonify({"message": "Token has expired"}).data,
                            status=HTTPStatus.UNAUTHORIZED.value,
                            mimetype='application/json')
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return Response(response=jsonify({"message": f"Invalid token: {e}"}).data,
                            status=HTTPStatus.UNAUTHORIZED.value,
                            mimetype='application/json')
        except ValueError as e:
            logger.error(f"AuthMiddleware configuration error: {e}")
            return Response(response=jsonify({"message": "Server authentication configuration error"}).data,
                            status=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                            mimetype='application/json')
        except Exception as e:
            logger.exception(f"An unexpected error occurred during authentication: {e}")
            return Response(response=jsonify({"message": "An unexpected authentication error occurred"}).data,
                            status=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                            mimetype='application/json')

    def process_response(self, request: Any, response: Response) -> Response:
        return response
