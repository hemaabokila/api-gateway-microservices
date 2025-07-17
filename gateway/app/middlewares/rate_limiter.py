from flask import request, jsonify, current_app, Response
from typing import Optional, Any
from http import HTTPStatus
from ..middleware_manager import Middleware 
import time

request_counts = {}
last_reset_time = time.time()

class RateLimiterMiddleware(Middleware):
    def process_request(self, request: Any) -> Optional[Response]:
        global request_counts, last_reset_time

        max_requests = current_app.config.get('RATE_LIMIT_MAX_REQUESTS')
        window_seconds = current_app.config.get('RATE_LIMIT_WINDOW_SECONDS')

        if time.time() - last_reset_time > window_seconds:
            request_counts = {}
            last_reset_time = time.time()
            current_app.logger.debug("Rate limiter counts reset.")

        client_ip = request.remote_addr

        request_counts[client_ip] = request_counts.get(client_ip, 0) + 1

        if request_counts[client_ip] > max_requests:
            current_app.logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(response=jsonify({"message": "Too many requests. Please try again later."}).data,
                            status=HTTPStatus.TOO_MANY_REQUESTS.value,
                            mimetype='application/json',
                            headers={'Retry-After': str(window_seconds)})

        current_app.logger.debug(f"IP {client_ip} has made {request_counts[client_ip]} requests.")
        return None

    def process_response(self, request: Any, response: Response) -> Response:
        response.headers['X-RateLimit-Limit'] = str(current_app.config.get('RATE_LIMIT_MAX_REQUESTS'))
        response.headers['X-RateLimit-Remaining'] = str(current_app.config.get('RATE_LIMIT_MAX_REQUESTS') - request_counts.get(request.remote_addr, 0))
        response.headers['X-RateLimit-Reset'] = str(int(last_reset_time + current_app.config.get('RATE_LIMIT_WINDOW_SECONDS')))
        return response

