import os

class Config:
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///products.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CONSUL_HOST = os.getenv('CONSUL_HOST', 'consul') 
    CONSUL_PORT = int(os.getenv('CONSUL_PORT', 8500))
    SERVICE_NAME = os.getenv('SERVICE_NAME', 'products_service')
    SERVICE_ID = os.getenv('SERVICE_ID', SERVICE_NAME)
    SERVICE_ADDRESS = os.getenv('SERVICE_ADDRESS', SERVICE_NAME) 
    SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5002))
    SERVICE_TAGS = ['flask', 'api', 'products']
    HEALTH_CHECK_INTERVAL = os.getenv('HEALTH_CHECK_INTERVAL', '10s')
    HEALTH_CHECK_TIMEOUT = os.getenv('HEALTH_CHECK_TIMEOUT', '5s')
    HEALTH_CHECK_DEREGISTER_CRITICAL_SERVICE_AFTER = os.getenv('HEALTH_CHECK_DEREGISTER_CRITICAL_SERVICE_AFTER', '1m')
    MIGRATIONS_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'migrations')
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq') 
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
    RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', 'guest')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
    RABBITMQ_EVENTS_EXCHANGE = os.getenv('RABBITMQ_EVENTS_EXCHANGE', 'product_events_exchange')
    RABBITMQ_EVENTS_EXCHANGE_TYPE = os.getenv('RABBITMQ_EVENTS_EXCHANGE_TYPE', 'topic')

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