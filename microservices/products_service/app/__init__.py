from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restx import Api
from flask_migrate import Migrate

from .utils.message_queue import MessageQueueClient
from .metrics import metrics_bp

from .config import Config
from .logging_setup import setup_logging

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()

api = Api(
    version='1.0',
    title='Products Service API',
    description='API for managing product data.',
    doc=False
)
message_queue_client = None
def create_app():
    global message_queue_client
    app = Flask(__name__)
    app.config.from_object(Config)

    setup_logging(app.config)
    app.logger.info("Products Service logging initialized.")

    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)

    api.init_app(app)
    rabbitmq_host = app.config.get('RABBITMQ_HOST')
    rabbitmq_port = app.config.get('RABBITMQ_PORT')
    try:
        message_queue_client = MessageQueueClient(host=rabbitmq_host, port=rabbitmq_port)
        app.logger.info(f"MessageQueueClient initialized for Products Service at {rabbitmq_host}:{rabbitmq_port}.")
    except Exception as e:
        app.logger.error(f"Failed to initialize MessageQueueClient for Products Service: {e}", exc_info=True)
        message_queue_client = None
    from .routes import register_routes
    register_routes(app, api)
    app.register_blueprint(metrics_bp)
    return app