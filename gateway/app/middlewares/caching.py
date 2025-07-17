import redis
import json
from flask import request, Response, current_app
from typing import Any, Optional
from ..middleware_manager import Middleware
import logging

logger = logging.getLogger(__name__)

class CachingMiddleware(Middleware):
    def __init__(self):
        self.redis_client = None
        self.cache_ttl = None
        self.excluded_paths = []

    def _init_redis_client(self):
        """Initializes Redis client only when app context is available."""
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
                self.cache_ttl = current_app.config.get('DEFAULT_CACHE_TTL_SECONDS')
                self.excluded_paths = current_app.config.get('CACHE_EXCLUDED_PATHS', [])
                logger.info("Redis client initialized successfully for CachingMiddleware.")
            except Exception as e:
                logger.error(f"An unexpected error occurred during Redis client initialization: {e}. Caching will be disabled.", exc_info=True)
                self.redis_client = None

    def process_request(self, request: Any) -> Optional[Response]:
        self._init_redis_client()

        if self.redis_client is None:
            return None

        if request.method != 'GET':
            return None

        for excluded_path in self.excluded_paths:
            if excluded_path.endswith('/<path:path>'):
                base_path = excluded_path.replace('/<path:path>', '')
                if request.path.startswith(base_path):
                    logger.debug(f"Path {request.path} excluded from cache by {excluded_path}")
                    return None
            elif request.path == excluded_path:
                logger.debug(f"Path {request.path} excluded from cache by exact match")
                return None

        cache_key = f"cache:{request.full_path}"
        cached_response = self.redis_client.get(cache_key)

        if cached_response:
            try:
                data = json.loads(cached_response)
                logger.info(f"Serving from cache: {request.full_path}")
                return Response(response=data['content'], status=data['status_code'], headers=data['headers'])
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode cached response for {request.full_path}. Fetching from origin.")
                self.redis_client.delete(cache_key)
            except Exception as e:
                logger.error(f"Error processing cached response for {request.full_path}: {e}", exc_info=True)
                self.redis_client.delete(cache_key)

        return None

    def process_response(self, request: Any, response: Response) -> Response:
        self._init_redis_client()

        if self.redis_client is None:
            return response

        if request.method == 'GET' and response.status_code == 200:
            for excluded_path in self.excluded_paths:
                if excluded_path.endswith('/<path:path>'):
                    base_path = excluded_path.replace('/<path:path>', '')
                    if request.path.startswith(base_path):
                        return response
                elif request.path == excluded_path:
                    return response

            cache_key = f"cache:{request.full_path}"
            response_data = {
                "content": response.get_data(as_text=True),
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
            try:
                self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(response_data))
                logger.info(f"Cached response for: {request.full_path}")
            except Exception as e:
                logger.error(f"Failed to cache response for {request.full_path}: {e}", exc_info=True)

        return response
