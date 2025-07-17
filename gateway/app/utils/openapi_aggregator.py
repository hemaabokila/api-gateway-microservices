import requests
import json
import logging
import time
from typing import Optional, List,Tuple

from .service_discovery import ConsulServiceDiscovery 

logger = logging.getLogger(__name__)

class OpenAPIAggregator:
    def __init__(self, service_discovery_client: ConsulServiceDiscovery, discoverable_services: List[str]):
        self.service_discovery_client = service_discovery_client
        self.discoverable_services = discoverable_services
        self._cached_spec = None
        self._last_aggregation_time = 0
        self.cache_ttl = 300

    def _fetch_service_openapi_spec(self, service_name: str, service_base_url: str) -> Optional[dict]:
        """Fetches the OpenAPI spec from a single microservice."""
        spec_url = f"{service_base_url}/swagger.json"
        try:
            response = requests.get(spec_url, timeout=5)
            response.raise_for_status()
            logger.info(f"Successfully fetched OpenAPI spec from {service_name} at {spec_url}")
            return response.json()
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to {service_name} at {spec_url}. Service might be down or not ready.")
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching OpenAPI spec from {service_name} at {spec_url}.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching OpenAPI spec from {service_name} at {spec_url}: {e}")
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from OpenAPI spec of {service_name} at {spec_url}.")
        return None

    def _merge_openapi_specs_final(self, specs_with_names: List[Tuple[str, dict]]) -> dict:
        """
        Merges multiple OpenAPI specs into a single one.
        Assumes paths and schema names are already transformed with service prefixes.
        """
        merged_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "API Gateway Unified API",
                "description": "Unified API documentation for all microservices accessible via the Gateway.",
                "version": "1.0.0"
            },
            "servers": [{"url": "/api"}],
            "paths": {},
            "components": {"schemas": {}}
        }

        for service_name, spec in specs_with_names:

            for path, path_item in spec.get("paths", {}).items():

                
                proxy_service_base_name = service_name.replace('_service', '')
                transformed_path = f"/api/{proxy_service_base_name}{path}"
                merged_spec["paths"][transformed_path] = path_item
            
            for schema_name, schema_def in spec.get("components", {}).get("schemas", {}).items():

                new_schema_name = f"{service_name}_{schema_name}"
                merged_spec["components"]["schemas"][new_schema_name] = schema_def

        merged_spec_str = json.dumps(merged_spec)
        for service_name, _ in specs_with_names:
            merged_spec_str = merged_spec_str.replace(f"#/components/schemas/", f"#/components/schemas/{service_name}_")
        merged_spec = json.loads(merged_spec_str)
        
        return merged_spec

    def get_aggregated_spec(self, force_refresh: bool = False) -> dict:
        """
        Retrieves the aggregated OpenAPI spec. Caches the result.
        """
        current_time = time.time()
        if not force_refresh and self._cached_spec and (current_time - self._last_aggregation_time < self.cache_ttl):
            logger.info("Returning cached aggregated OpenAPI spec.")
            return self._cached_spec

        logger.info("Aggregating OpenAPI specs from microservices...")
        all_specs_with_names = []
        for service_name in self.discoverable_services:
            service_url = self.service_discovery_client.get_service_address(service_name)
            if service_url:
                spec = self._fetch_service_openapi_spec(service_name, service_url)
                if spec:
                    all_specs_with_names.append((service_name, spec))
            else:
                logger.warning(f"Could not find healthy instance for service '{service_name}'. Skipping OpenAPI spec aggregation for it.")
        
        if not all_specs_with_names:
            logger.warning("No OpenAPI specs could be fetched from any discoverable microservice.")
            return {
                "openapi": "3.0.0",
                "info": {"title": "No Services Available", "version": "1.0.0", "description": "Could not fetch OpenAPI specs from any microservice."},
                "paths": {},
                "components": {"schemas": {}}
            }

        self._cached_spec = self._merge_openapi_specs_final(all_specs_with_names)
        self._last_aggregation_time = current_time
        logger.info("Aggregated OpenAPI spec generated and cached.")
        return self._cached_spec
