import pika
import json
import logging
import time 
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MessageQueueClient:
    """
    Client for interacting with RabbitMQ to publish messages.
    """
    def __init__(self, host: str, port: int, username: str = 'guest', password: str = 'guest', retries: int = 5, delay: int = 5):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.retries = retries
        self.delay = delay
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[pika.channel.Channel] = None
        self._connect()

    def _connect(self):
        """Establishes a connection to RabbitMQ with retry logic."""
        for i in range(self.retries):
            try:
                logger.info(f"Attempting to connect to RabbitMQ at {self.host}:{self.port} (Attempt {i+1}/{self.retries})...")
                credentials = pika.PlainCredentials(self.username, self.password)
                parameters = pika.ConnectionParameters(self.host, self.port, '/', credentials)
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()
                logger.info(f"Successfully connected to RabbitMQ at {self.host}:{self.port}.")
                return
            except pika.exceptions.AMQPConnectionError as e:
                logger.error(f"Failed to connect to RabbitMQ (attempt {i+1}/{self.retries}): {e}")
                self._connection = None
                self._channel = None
                if i < self.retries - 1:
                    time.sleep(self.delay)
                else:
                    logger.critical(f"Exceeded max retries ({self.retries}) to connect to RabbitMQ. Service cannot function without MQ.")
                    raise
            except Exception as e:
                logger.error(f"An unexpected error occurred during RabbitMQ connection (attempt {i+1}/{self.retries}): {e}", exc_info=True)
                self._connection = None
                self._channel = None
                if i < self.retries - 1:
                    time.sleep(self.delay)
                else:
                    logger.critical(f"Exceeded max retries ({self.retries}) to connect to RabbitMQ due to unexpected error. Service cannot function without MQ.")
                    raise

    def _ensure_connection(self):
        """Ensures the connection is active, reconnecting if necessary."""
        if not self._connection or self._connection.is_closed:
            logger.warning("RabbitMQ connection lost or never established, attempting to reconnect...")
            self._connect()
        if self._connection and self._channel and self._channel.is_closed:
            logger.warning("RabbitMQ channel closed, reopening...")
            try:
                self._channel = self._connection.channel()
            except pika.exceptions.ChannelClosed as e:
                logger.error(f"Failed to reopen RabbitMQ channel: {e}. Attempting full reconnect.", exc_info=True)
                self._connect()
            except Exception as e:
                logger.error(f"An unexpected error occurred while reopening RabbitMQ channel: {e}", exc_info=True)
                self._connect()

    def publish_event(self, exchange_name: str, routing_key: str, event_data: Dict[str, Any], exchange_type: str = 'topic'):
        """
        Publishes an event message to a specified RabbitMQ exchange.
        """
        self._ensure_connection()
        if not self._channel:
            logger.error("Cannot publish event: No active RabbitMQ channel after ensuring connection.")
            return

        try:
            self._channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=True
            )
            
            message_body = json.dumps(event_data)
            self._channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                )
            )
            logger.info(f"Published event to exchange '{exchange_name}' with routing key '{routing_key}': {message_body}")
        except Exception as e:
            logger.error(f"Failed to publish event to RabbitMQ: {e}", exc_info=True)
            
    def close(self):
        """Closes the RabbitMQ connection."""
        if self._connection and self._connection.is_open:
            self._connection.close()
            logger.info("RabbitMQ connection closed.")