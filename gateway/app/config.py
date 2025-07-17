import os

class Config:
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'a_very_secret_key_for_flask')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    CIRCUIT_BREAKER_SETTINGS = {
        'FAILURE_THRESHOLD': int(os.getenv('CB_FAILURE_THRESHOLD', 5)),
        'RECOVERY_TIMEOUT_SECONDS': int(os.getenv('CB_RECOVERY_TIMEOUT_SECONDS', 30)),
        'HALF_OPEN_TIMEOUT_SECONDS': int(os.getenv('CB_HALF_OPEN_TIMEOUT_SECONDS', 5))
    }
    CIRCUIT_BREAKER_FALLBACK_MESSAGE = "Service is currently unavailable. Circuit breaker is open."
    CONSUL_HOST = os.getenv('CONSUL_HOST', 'consul') 
    CONSUL_PORT = int(os.getenv('CONSUL_PORT', 8500))
    DISCOVERABLE_SERVICES = ['users_service', 'products_service']
    RATE_LIMIT_MAX_REQUESTS = int(os.getenv('RATE_LIMIT_MAX_REQUESTS', 100))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv('RATE_LIMIT_WINDOW_SECONDS', 60))
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis_cache') 
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    DEFAULT_CACHE_TTL_SECONDS = int(os.getenv('DEFAULT_CACHE_TTL_SECONDS', 300))

    CACHE_EXCLUDED_PATHS = ['/gateway/health', '/openapi.json', '/docs/', '/docs/<path:path>', '/metrics']
    CACHE_METHODS = ['GET']

    LOGGING_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'json': {
                'format': '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },

        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True
            },
            'werkzeug': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False
            },
            'app': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False
            }
        }
    }

    AUTH_EXCLUDED_PATHS = [
        '/proxy/users_service/login',
        '/proxy/users_service/users',
        '/gateway/health',
        '/openapi.json',
        '/docs/',
        '/docs/<path:path>',
        '/metrics'
    ]
