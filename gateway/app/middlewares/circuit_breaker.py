import redis
import time
from flask import request, jsonify, Response, current_app
from typing import Any, Optional, Dict
from ..middleware_manager import Middleware
import logging
import json
from http import HTTPStatus
logger = logging.getLogger(__name__)


CIRCUIT_CLOSED = "CLOSED"
CIRCUIT_OPEN = "OPEN"
CIRCUIT_HALF_OPEN = "HALF_OPEN"


service_breakers: Dict[str, Any] = {}

class CircuitBreakerMiddleware(Middleware):
    def __init__(self):
        self.redis_client = None
        self.config = {}

    def _init_redis_client_and_config(self):
        """Initializes Redis client and loads config only when app context is available."""
        if self.redis_client is None and current_app:
            try:
                redis_host = current_app.config.get('REDIS_HOST')
                redis_port = current_app.config.get('REDIS_PORT')
                redis_db = current_app.config.get('REDIS_DB')
                redis_password = current_app.config.get('REDIS_PASSWORD')

                self.redis_client = redis.StrictRedis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=True
                )
                self.redis_client.ping()
                self.config = current_app.config.get('CIRCUIT_BREAKER_SETTINGS', {})
                logger.info("Redis client initialized successfully for CircuitBreakerMiddleware.")
            except Exception as e:
                logger.error(f"An unexpected error occurred during Redis client initialization for Circuit Breaker: {e}. Circuit Breaker will be disabled.", exc_info=True)
                self.redis_client = None

    def _get_breaker_state(self, service_name: str) -> Dict[str, Any]:
        """Retrieves circuit breaker state from Redis."""
        if not self.redis_client:
            return {"state": CIRCUIT_CLOSED, "failures": 0, "last_failure_time": 0, "half_open_attempts": 0}

        state_str = self.redis_client.get(f"cb:{service_name}")
        if state_str:
            return json.loads(state_str)
        return {"state": CIRCUIT_CLOSED, "failures": 0, "last_failure_time": 0, "half_open_attempts": 0}

    def _set_breaker_state(self, service_name: str, state: Dict[str, Any]):
        """Sets circuit breaker state in Redis."""
        if self.redis_client:
            self.redis_client.set(f"cb:{service_name}", json.dumps(state))

    def process_request(self, request: Any) -> Optional[Response]:
        self._init_redis_client_and_config()

        if self.redis_client is None:
            return None 

        path_parts = request.path.split('/')
        if len(path_parts) < 3 or path_parts[1] != 'api':
            return None 

        service_name = path_parts[2]

        state = self._get_breaker_state(service_name)
        current_time = time.time()

        if state["state"] == CIRCUIT_OPEN:
            if current_time - state["last_failure_time"] > self.config.get('RECOVERY_TIMEOUT_SECONDS', 30):
                state["state"] = CIRCUIT_HALF_OPEN
                state["half_open_attempts"] = 0
                self._set_breaker_state(service_name, state)
                logger.info(f"Circuit for service '{service_name}' transitioned to HALF-OPEN.")
            else:
                logger.warning(f"Circuit for service '{service_name}' is OPEN. Request rejected.")
                fallback_message = current_app.config.get('CIRCUIT_BREAKER_FALLBACK_MESSAGE', "Service is currently unavailable.")
                return Response(response=jsonify({"message": fallback_message}).data,
                                status=HTTPStatus.SERVICE_UNAVAILABLE.value,
                                mimetype='application/json')
        
        return None

    def process_response(self, request: Any, response: Response) -> Response:
        self._init_redis_client_and_config()

        if self.redis_client is None:
            return response

        path_parts = request.path.split('/')
        if len(path_parts) < 3 or path_parts[1] != 'api':
            return response

        service_name = path_parts[2]
        state = self._get_breaker_state(service_name)
        
        if response.status_code >= 500:
            state["failures"] += 1
            state["last_failure_time"] = time.time()
            logger.warning(f"Service '{service_name}' recorded a failure. Total failures: {state['failures']}")

            if state["state"] == CIRCUIT_HALF_OPEN:
                state["state"] = CIRCUIT_OPEN
                logger.error(f"Circuit for service '{service_name}' transitioned back to OPEN due to failure in HALF-OPEN state.")
            elif state["state"] == CIRCUIT_CLOSED and state["failures"] >= self.config.get('FAILURE_THRESHOLD', 5):
                state["state"] = CIRCUIT_OPEN
                logger.error(f"Circuit for service '{service_name}' transitioned to OPEN after {state['failures']} failures.")
            
            self._set_breaker_state(service_name, state)

        elif response.status_code < 500:
            if state["state"] == CIRCUIT_HALF_OPEN:
                state["state"] = CIRCUIT_CLOSED
                state["failures"] = 0
                state["half_open_attempts"] = 0
                logger.info(f"Circuit for service '{service_name}' transitioned to CLOSED after successful request in HALF-OPEN state.")
                self._set_breaker_state(service_name, state)
            elif state["state"] == CIRCUIT_CLOSED:
                state["failures"] = 0
                self._set_breaker_state(service_name, state)

        return response
