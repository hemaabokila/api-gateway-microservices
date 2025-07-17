from app import create_app, message_queue_client
from dotenv import load_dotenv
import consul
import atexit
import logging
import sys
import os

load_dotenv()


def register_service_with_consul(app_instance):
    """
    Registers the service with Consul using the provided Flask app instance.
    """
    consul_host = app_instance.config.get('CONSUL_HOST')
    consul_port = app_instance.config.get('CONSUL_PORT')
    
    app_instance.logger.info(f"Consul client will attempt to connect to: {consul_host}:{consul_port}")
    
    try:
        consul_client = consul.Consul(host=consul_host, port=consul_port)
    except Exception as e:
        app_instance.logger.error(f"Failed to initialize Consul client with host {consul_host} and port {consul_port}: {e}", exc_info=True)
        return
        
    service_name = app_instance.config.get('SERVICE_NAME')
    service_id = app_instance.config.get('SERVICE_ID')
    service_port = app_instance.config.get('SERVICE_PORT')
    service_address = app_instance.config.get('SERVICE_ADDRESS')
    health_check_interval = app_instance.config.get('HEALTH_CHECK_INTERVAL')
    health_check_timeout = app_instance.config.get('HEALTH_CHECK_TIMEOUT')
    deregister_critical_service_after = app_instance.config.get('HEALTH_CHECK_DEREGISTER_CRITICAL_SERVICE_AFTER')

    app_instance.logger.info(f"Attempting to register service '{service_name}' with ID '{service_id}' at {service_address}:{service_port} with Consul at {consul_host}:{consul_port}")
    app_instance.logger.info(f"Health check URL: http://{service_address}:{service_port}/metrics")
    
    try:
        consul_client.agent.service.register(
            name=service_name,
            service_id=service_id,
            address=service_address,
            port=service_port,
            check={
                'http': f"http://{service_address}:{service_port}/metrics",
                'interval': health_check_interval,
                'timeout': health_check_timeout,
                'deregister_critical_service_after': deregister_critical_service_after
            }
        )
        app_instance.logger.info(f"Service '{service_name}' registered successfully with Consul.")
    except Exception as e:
        app_instance.logger.error(f"CRITICAL: Failed to register service '{service_name}' with Consul. Error: {e}", exc_info=True)


def deregister_service_from_consul(app_instance):
    """
    Deregisters the service from Consul. This function is called on exit.
    """
    consul_host = app_instance.config.get('CONSUL_HOST')
    consul_port = app_instance.config.get('CONSUL_PORT')
    
    try:
        consul_client = consul.Consul(host=consul_host, port=consul_port)
    except Exception as e:
        app_instance.logger.error(f"Failed to initialize Consul client for deregistration: {e}", exc_info=True)
        return

    service_name = app_instance.config.get('SERVICE_NAME')
    service_id = app_instance.config.get('SERVICE_ID')

    app_instance.logger.info(f"Attempting to deregister service '{service_name}' with ID '{service_id}' from Consul.")
    try:
        consul_client.agent.service.deregister(service_id)
        app_instance.logger.info(f"Service '{service_name}' deregistered successfully from Consul.")
    except Exception as e:
        app_instance.logger.error(f"Failed to deregister service '{service_name}' from Consul: {e}", exc_info=True)


def close_rabbitmq_connection(app_instance):
    """Closes the RabbitMQ connection."""
    if hasattr(app_instance, 'message_queue_client') and app_instance.message_queue_client:
        app_instance.message_queue_client.close()

def create_gunicorn_app():
    app = create_app()
    
    atexit.register(deregister_service_from_consul, app)
    atexit.register(close_rabbitmq_connection, app)

    with app.app_context():
        try:
            from flask_migrate import upgrade
            app.logger.info("Applying database migrations...")
            upgrade()
            app.logger.info("Database migrations applied successfully.")
        except Exception as e:
            app.logger.error(f"Failed to apply database migrations: {e}", exc_info=True)
            sys.exit(1)

    register_service_with_consul(app)
    
    return app


if __name__ == '__main__':
    app = create_gunicorn_app()
    service_port = app.config.get('SERVICE_PORT')
    app.run(host='0.0.0.0', port=service_port, debug=app.config.get('DEBUG'), use_reloader=False)