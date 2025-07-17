import consul
import logging
import random
from typing import Optional, List

logger = logging.getLogger(__name__)

class ConsulServiceDiscovery:
    """
    Client for interacting with Consul for service discovery.
    """
    def __init__(self, host: str, port: int):
        try:
            self.consul_client = consul.Consul(host=host, port=port)
            self.consul_client.agent.self()
            logger.info(f"Successfully connected to Consul at {host}:{port}.")
        except Exception as e:
            self.consul_client = None
            logger.error(f"Failed to connect to Consul at {host}:{port}: {e}", exc_info=True)

    def get_service_address(self, service_name: str) -> Optional[str]:
        """
        Queries Consul for a healthy instance of the given service.
        Returns the URL (http://host:port) of a random healthy instance.
        """
        if not self.consul_client:
            logger.error(f"Consul client not initialized. Cannot discover service '{service_name}'.")
            return None

        try:
            _, services = self.consul_client.health.service(service_name, passing=True)
            
            if not services:
                logger.warning(f"No healthy instances found for service: {service_name}")
                return None
            
            instance = random.choice(services)
            address = instance['Service']['Address']
            port = instance['Service']['Port']
            
            service_url = f"http://{address}:{port}"
            logger.debug(f"Discovered service '{service_name}': {service_url}")
            return service_url
        except Exception as e:
            logger.error(f"Error discovering service '{service_name}' from Consul: {e}", exc_info=True)
            return None

    def get_all_service_names(self) -> List[str]:
        """
        Returns a list of all registered service names in Consul.
        """
        if not self.consul_client:
            logger.error("Consul client not initialized. Cannot get service names.")
            return []
        try:
            _, services = self.consul_client.catalog.services()
            return list(services.keys())
        except Exception as e:
            logger.error(f"Error fetching service names from Consul: {e}", exc_info=True)
            return []
