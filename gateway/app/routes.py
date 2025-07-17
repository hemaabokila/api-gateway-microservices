from flask import request, jsonify, current_app, Response
from flask_restx import Namespace, Resource, fields
import requests
import json
import logging
from http import HTTPStatus

from .utils.errors import (
    ServiceUnavailableError,
    NotFoundError,
    BadRequestError,
    APIError,
    TooManyRequestsError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
)

from .middlewares.circuit_breaker import service_breakers 

logger = logging.getLogger(__name__)

gateway_ns = Namespace('gateway', description='Gateway specific operations')

health_status_model = gateway_ns.model('HealthStatus', {
    'status': fields.String(required=True, description='Status of the Gateway')
})

proxy_ns = Namespace('proxy', description='Proxy requests to microservices')

_service_discovery_client = None


class GatewayRoot(Resource):
    @gateway_ns.doc('get_gateway_root')
    @gateway_ns.response(200, 'Success')
    def get(self):
        """Root endpoint for the API Gateway."""
        current_app.logger.info("GatewayRoot endpoint was accessed.")
        return jsonify({
            "message": "Welcome to the Microservices API Gateway!",
            "status": "Online",
            "documentation_url": "/docs/",
            "health_check_url": "/gateway/health",
            "metrics_url": "/metrics"
        }), 200


def register_routes(app, api_instance, openapi_aggregator_instance, service_discovery_client_param):
    global _service_discovery_client
    _service_discovery_client = service_discovery_client_param

    api_instance.add_resource(GatewayRoot, '/')

    api_instance.add_namespace(gateway_ns)
    api_instance.add_namespace(proxy_ns)

    @gateway_ns.route('/health')
    class GatewayHealth(Resource):
        @gateway_ns.doc('get_gateway_health')
        @gateway_ns.marshal_with(health_status_model)
        def get(self):
            """Check the health status of the API Gateway"""
            return {"status": "Gateway is healthy"}, 200

    @app.route('/openapi.json', methods=['GET'])
    def get_aggregated_openapi_spec():
        """
        Serves the aggregated OpenAPI specification for all microservices.
        This spec is dynamically fetched and merged from individual microservices.
        """
        try:
            spec = openapi_aggregator_instance.get_aggregated_spec()
            return jsonify(spec)
        except Exception as e:
            logger.exception("Failed to generate aggregated OpenAPI spec.")
            raise APIError(message=f"Failed to generate OpenAPI spec: {str(e)}", code=HTTPStatus.INTERNAL_SERVER_ERROR.value)

    @proxy_ns.route('/<service_name>/<path:path>')
    @proxy_ns.param('service_name', 'Name of the target microservice (e.g., users, products)')
    @proxy_ns.param('path', 'Path within the target microservice API')
    class ProxyResource(Resource):
        @proxy_ns.doc(params={
            'service_name': 'Name of the target microservice (e.g., users, products)',
            'path': 'Path within the target microservice API',
            'Authorization': {'description': 'Bearer Token for authentication', 'in': 'header', 'required': False}
        })
        @proxy_ns.response(200, 'Success')
        @proxy_ns.response(404, 'Service or resource not found')
        @proxy_ns.response(503, 'Service unavailable')
        @proxy_ns.response(401, 'Unauthorized')
        @proxy_ns.response(429, 'Too Many Requests')
        def get(self, service_name, path):
            """Proxy GET requests to the specified microservice"""
            return _proxy_request(service_name, path, request.method)

        @proxy_ns.doc(params={
            'service_name': 'Name of the target microservice (e.g., users, products)',
            'path': 'Path within the target microservice API',
            'Authorization': {'description': 'Bearer Token for authentication', 'in': 'header', 'required': False}
        })
        @proxy_ns.expect(proxy_ns.parser().add_argument('body', type=str, help='Request body (JSON)', location='json'))
        @proxy_ns.response(200, 'Success')
        @proxy_ns.response(201, 'Created')
        @proxy_ns.response(400, 'Bad Request')
        @proxy_ns.response(404, 'Service or resource not found')
        @proxy_ns.response(503, 'Service unavailable')
        @proxy_ns.response(401, 'Unauthorized')
        @proxy_ns.response(429, 'Too Many Requests')
        def post(self, service_name, path):
            """Proxy POST requests to the specified microservice"""
            return _proxy_request(service_name, path, request.method)

        @proxy_ns.doc(params={
            'service_name': 'Name of the target microservice (e.g., users, products)',
            'path': 'Path within the target microservice API',
            'Authorization': {'description': 'Bearer Token for authentication', 'in': 'header', 'required': False}
        })
        @proxy_ns.expect(proxy_ns.parser().add_argument('body', type=str, help='Request body (JSON)', location='json'))
        @proxy_ns.response(200, 'Success')
        @proxy_ns.response(400, 'Bad Request')
        @proxy_ns.response(404, 'Service or resource not found')
        @proxy_ns.response(503, 'Service unavailable')
        @proxy_ns.response(401, 'Unauthorized')
        @proxy_ns.response(429, 'Too Many Requests')
        def put(self, service_name, path):
            """Proxy PUT requests to the specified microservice"""
            return _proxy_request(service_name, path, request.method)

        @proxy_ns.doc(params={
            'service_name': 'Name of the target microservice (e.g., users, products)',
            'path': 'Path within the target microservice API',
            'Authorization': {'description': 'Bearer Token for authentication', 'in': 'header', 'required': False}
        })
        @proxy_ns.response(204, 'No Content')
        @proxy_ns.response(404, 'Service or resource not found')
        @proxy_ns.response(503, 'Service unavailable')
        @proxy_ns.response(401, 'Unauthorized')
        @proxy_ns.response(429, 'Too Many Requests')
        def delete(self, service_name, path):
            """Proxy DELETE requests to the specified microservice"""
            return _proxy_request(service_name, path, request.method)

        @proxy_ns.doc(params={
            'service_name': 'Name of the target microservice (e.g., users, products)',
            'path': 'Path within the target microservice API',
            'Authorization': {'description': 'Bearer Token for authentication', 'in': 'header', 'required': False}
        })
        @proxy_ns.expect(proxy_ns.parser().add_argument('body', type=str, help='Request body (JSON)', location='json'))
        @proxy_ns.response(200, 'Success')
        @proxy_ns.response(400, 'Bad Request')
        @proxy_ns.response(404, 'Service or resource not found')
        @proxy_ns.response(503, 'Service unavailable')
        @proxy_ns.response(401, 'Unauthorized')
        @proxy_ns.response(429, 'Too Many Requests')
        def patch(self, service_name, path):
            """Proxy PATCH requests to the specified microservice"""
            return _proxy_request(service_name, path, request.method)


def _proxy_request(service_name, path, method):
    service_url = _service_discovery_client.get_service_address(service_name)
    if not service_url:
        raise ServiceUnavailableError(f"Service '{service_name}' not found or no healthy instances available.")

    target_url = f"{service_url}/{path}"
    
    headers = {k: v for k, v in request.headers if k.lower() not in ['host', 'content-length', 'transfer-encoding']}
    data = request.get_data()
    
    try:
        resp = requests.request(
            method=method,
            url=target_url,
            headers=headers,
            data=data,
            params=request.args,
            allow_redirects=False,
            timeout=10
        )

        excluded_response_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(name, value) for name, value in resp.raw.headers.items() if name.lower() not in excluded_response_headers]

        resp.raise_for_status() 

        return Response(resp.content, resp.status_code, response_headers)

    except requests.exceptions.Timeout:
        current_app.logger.error(f"Service '{service_name}' at {service_url} timed out.")
        raise ServiceUnavailableError(f"Service '{service_name}' timed out.")
    except requests.exceptions.ConnectionError:
        current_app.logger.error(f"Service '{service_name}' at {service_url} is unavailable (Connection Error).")
        raise ServiceUnavailableError(f"Service '{service_name}' is unavailable.")
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        message = e.response.text if e.response.text else f"Error from microservice: {status_code}"
        
        try:
            error_details = e.response.json()
            message = error_details.get("message", message)
        except json.JSONDecodeError:
            pass
            
        if status_code == HTTPStatus.NOT_FOUND.value:
            raise NotFoundError(message)
        elif status_code == HTTPStatus.BAD_REQUEST.value:
            raise BadRequestError(message)
        elif status_code == HTTPStatus.UNAUTHORIZED.value:
            raise UnauthorizedError(message)
        elif status_code == HTTPStatus.FORBIDDEN.value:
            raise ForbiddenError(message)
        elif status_code == HTTPStatus.CONFLICT.value:
            raise ConflictError(message)
        elif status_code == HTTPStatus.TOO_MANY_REQUESTS.value:
            raise TooManyRequestsError(message)
        else:
            raise APIError(message, status_code)
    except Exception as e:
        current_app.logger.exception(f"An unexpected error occurred during proxying request to {service_name}: {e}")
        raise APIError(message=f"An internal error occurred: {str(e)}", code=HTTPStatus.INTERNAL_SERVER_ERROR.value)

