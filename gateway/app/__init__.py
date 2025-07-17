from flask import Flask, request
from flask_restx import Api
from typing import Optional

from .config import Config
from .routes import register_routes
from .middleware_manager import MiddlewareManager
from .middlewares.auth import AuthMiddleware
from .middlewares.rate_limiter import RateLimiterMiddleware
from .middlewares.caching import CachingMiddleware
from .middlewares.circuit_breaker import CircuitBreakerMiddleware
from .logging_setup import setup_logging
from .utils.openapi_aggregator import OpenAPIAggregator
from .utils.service_discovery import ConsulServiceDiscovery
from .utils.errors import register_error_handlers
from .metrics import metrics_bp

api = Api(
    version='1.0',
    title='API Gateway Unified API',
    description='Unified API documentation for all microservices accessible via the Gateway.',
    doc='/docs/'
)

openapi_aggregator: Optional[OpenAPIAggregator] = None
service_discovery_client: Optional[ConsulServiceDiscovery] = None

def create_app():
    global openapi_aggregator, service_discovery_client

    app = Flask(__name__)
    app.config.from_object(Config)

    setup_logging(app.config)
    app.logger.info("Application logging initialized.")

    api.init_app(app)
    register_error_handlers(app)

    consul_host = app.config.get('CONSUL_HOST')
    consul_port = app.config.get('CONSUL_PORT')
    service_discovery_client = ConsulServiceDiscovery(host=consul_host, port=consul_port)
    app.logger.info("ConsulServiceDiscovery client initialized.")

    discoverable_services = app.config.get('DISCOVERABLE_SERVICES', [])
    openapi_aggregator = OpenAPIAggregator(service_discovery_client, discoverable_services)
    app.logger.info("OpenAPIAggregator initialized.")

    app.middleware_manager = MiddlewareManager()
    app.middleware_manager.add_middleware(CircuitBreakerMiddleware()) 
    app.middleware_manager.add_middleware(CachingMiddleware())
    # auth_middleware = AuthMiddleware()
    # auth_middleware.set_excluded_paths(app.config.get('AUTH_EXCLUDED_PATHS', []))
    # app.middleware_manager.add_middleware(auth_middleware)
    app.middleware_manager.add_middleware(RateLimiterMiddleware())

    register_routes(app, api, openapi_aggregator, service_discovery_client)
    app.register_blueprint(metrics_bp) 
    @app.before_request
    def before_request_middleware():
        response = app.middleware_manager.process_request(request)
        if response:
            return response 

    @app.after_request
    def after_request_middleware(response):
        return app.middleware_manager.process_response(request, response)

    return app