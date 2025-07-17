# Enterprise-grade Microservices System with Flask-based API Gateway and Full Observability

![Docker](https://img.shields.io/badge/docker-ready-blue)
![CI/CD](https://img.shields.io/github/actions/workflow/status/your-username/your-repo-name/gateway_ci.yml?label=Gateway%20CI)
![License](https://img.shields.io/github/license/your-username/your-repo-name)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/flask-2.x-lightgrey)
![Pytest](https://img.shields.io/badge/tests-pytest-blue)
## Project Overview

This project demonstrates a robust and scalable microservices architecture built primarily with Flask, featuring a central API Gateway that orchestrates communication between various independent microservices. It incorporates advanced enterprise-grade patterns and tools to ensure reliability, observability, and maintainability, making it an excellent foundation for understanding modern distributed systems.

The core idea is to break down a monolithic application into smaller, loosely coupled services (Users, Products) that communicate through an API Gateway.

This gateway handles cross-cutting concerns like authentication, rate limiting, caching, and service discovery, while also providing a unified access point and aggregated API documentation.

## Key Features & Architectural Patterns

This project is designed to showcase a wide array of critical microservices patterns:

1.  ### **API Gateway (Flask)**
    * **Centralized Access:** Provides a single entry point for all client requests, simplifying client-side interactions.
    * **Request Routing:** Intelligently forwards requests to the appropriate microservice.
    * **Cross-Cutting Concerns:** Offloads common functionalities (Auth, Rate Limiting, Caching, Circuit Breaking) from individual microservices.

2.  ### **Independent Microservices (Flask)**
    * **Users Service:** Manages user data (creation, retrieval, update, deletion).
    * **Products Service:** Manages product catalog data.
    * **Loose Coupling:** Each service operates independently, managing its own data and logic.

3.  ### **Authentication (JWT - JSON Web Tokens)**
    * **Stateless Security:** JWTs are used for secure, stateless authentication, allowing the API Gateway to validate tokens without needing to query a central authentication service for every request.
    * **Middleware Integration:** Implemented as a Flask middleware in the Gateway, ensuring all protected routes are secured.

4.  ### **Rate Limiting (Flask-Limiter)**
    * **API Protection:** Prevents abuse and ensures fair usage of API resources by limiting the number of requests a client can make within a defined timeframe.
    * **Resource Management:** Protects backend microservices from being overwhelmed by excessive traffic.

5.  ### **Caching (Redis)**
    * **Performance Optimization:** Reduces latency and improves response times for frequently accessed data by storing API responses in Redis.
    * **Reduced Backend Load:** Minimizes the number of requests hitting the actual microservices, enhancing their scalability and stability.
    * **Middleware Implementation:** Integrated as a middleware, automatically caching eligible GET requests.

6.  ### **Structured Logging (Python's `logging` module)**
    * **Enhanced Observability:** Provides detailed, structured logs across all services, crucial for debugging, monitoring, and auditing in a distributed environment.
    * **Centralized-Ready:** Designed to be easily integrated with log aggregation systems like ELK Stack (Elasticsearch, Logstash, Kibana) or Grafana Loki.

7.  ### **Continuous Integration / Continuous Deployment (CI/CD with GitHub Actions)**
    * **Automated Workflow:** Automates the build, test, and deployment process for each microservice and the Gateway.
    * **Quality Assurance:** Ensures code quality and consistency by running automated tests on every push and pull request.
    * **Rapid Iteration:** Enables faster and more reliable delivery of new features and bug fixes.

8.  ### **Unified API Documentation (OpenAPI/Swagger UI)**
    * **Centralized Documentation:** The API Gateway aggregates and serves the OpenAPI (Swagger) documentation from all individual microservices.
    * **Improved Developer Experience:** Provides a single, interactive interface for developers to explore, understand, and test all available APIs, eliminating the need to consult separate documentation for each service.
    * **`Flask-RESTx` Integration:** Each microservice uses `Flask-RESTx` to generate its OpenAPI specification, which the Gateway then fetches and merges dynamically.

9.  ### **Service Discovery (Consul)**
    * **Dynamic Service Location:** Eliminates hardcoding of microservice URLs in the Gateway. Services register themselves with Consul, and the Gateway queries Consul to find healthy instances.
    * **Increased Resilience:** Automatically adapts to service failures or scaling events, as the Gateway always routes requests to available and healthy instances.
    * **Load Balancing (Basic):** Randomly selects from healthy service instances, providing basic client-side load balancing.

10. ### **Circuit Breaker Pattern (Custom Implementation with Redis)**
    * **Fault Tolerance:** Protects the API Gateway from cascading failures when a downstream microservice becomes unresponsive or overloaded.
    * **Graceful Degradation:** Prevents the Gateway from continuously hammering a failing service, allowing the service time to recover.
    * **Redis-Backed State:** The circuit breaker's state (CLOSED, OPEN, HALF-OPEN) is persisted in Redis, ensuring consistency across multiple Gateway instances.

11. ### **Database Migrations (Alembic via Flask-Migrate)**
    * **Schema Evolution:** Manages changes to the database schema of each microservice in a controlled and versioned manner.
    * **Production Readiness:** Essential for safe and reliable updates to your database in production environments.
    * **Automated Application:** Migrations are automatically applied when a microservice starts up in its Docker container.

12. ### **Detailed Monitoring & Metrics (Prometheus & Grafana)**
    * **Real-time Observability:** Collects crucial performance metrics (request counts, latency, in-progress requests) from all services.
    * **Proactive Issue Detection:** Enables real-time monitoring of system health and performance, allowing for early detection and resolution of issues.
    * **Dashboards & Alerts:** Prometheus scrapes metrics, and Grafana provides powerful visualization dashboards and alerting capabilities.

13. ### **Asynchronous Messaging (RabbitMQ)**
    * **Decoupled Communication:** Enables services to communicate asynchronously, reducing direct dependencies and improving system resilience.
    * **Event-Driven Architecture:** Services can publish events (e.g., `user_created`, `product_updated`) to RabbitMQ, and other services can consume these events for various purposes (e.g., sending welcome emails, updating search indexes).
    * **Scalability & Reliability:** Messages are queued, ensuring delivery even if a consumer is temporarily unavailable.

14. ### **Simple Frontend Dashboard**
    * **Basic UI:** A minimalist HTML/CSS/JavaScript frontend to demonstrate interaction with the API Gateway and fetch data from the microservices.
    * **Proxying via Nginx:** The frontend uses Nginx to serve static files and proxy API requests to the Gateway, showcasing a typical client-server setup.

# Architecture Overview

The project is structured around a central API Gateway that acts as the entry point for all external requests.

It interacts with independent microservices (Users and Products) for business logic.

Supporting infrastructure services like Redis, Consul, RabbitMQ, Prometheus, and Grafana provide essential functionalities for caching, service discovery, asynchronous communication, and monitoring.
```bash
+----------------+          +--------------------+       +------------------------+
|                |          |                    |       |                        |
|    Frontend    |--------->|    API Gateway     |------>|   Users Service        |
| (Nginx/HTML/JS)|          |  (Flask-RESTx)     |       |  (Flask/SQLA)          |
|                |          |                    |       |                        |
+----------------+          | - Auth (JWT)       |       | - Registers with       |
|                           | - Rate Limiting    |       |   Consul               |
|                           | - Caching (Redis)  |       | - Publishes to         |
|                           | - Circuit Breaker  |       |   RabbitMQ             |
|                           | - Service Discovery|       | - Exposes /metrics     |
|                           | - Aggregated Docs  |       | - Exposes /swagger.json|
|                           +--------------------+       +------------------------+
|                           ^
|                           |
|                           |
v                           |
+-------------------+       +------------------------+
|                   |       |                        |
|   Consul (Service |       |  Products Service      |
|     Registry)     |<----->|  (Flask/SQLA)          |
|                   |       |                        |
+-------------------+       | - Registers with       |
^                           |   Consul               |
|                           | - Publishes to         |
|                           |   RabbitMQ             |
|                           | - Exposes /metrics     |
|                           | - Exposes /swagger.json|
|                           +------------------------+
|                           ^
|                           |
+-------------------+       +-------------------+
|                   |       |                   |
|   Redis (Caching  |       |   RabbitMQ        |
|  & CB State)      |       |  (Message Broker) |
|                   |       |                   |
+-------------------+       +-------------------+
^                           ^
|                           |
|                           |
+-------------------+       +---------------------+
|                   |       |                     |
|    Prometheus     |------>|     Grafana         |
|  (Metrics Scraper)|       |  (Dashboards/Alerts)|
|                   |       |                     |
+-------------------+       +---------------------+
```
## Technologies Used

* **Backend:** Python 3, Flask, Flask-SQLAlchemy, Flask-Marshmallow, Flask-RESTx, Flask-Limiter, PyJWT, Requests, Pika (RabbitMQ client), Python-Consul
* **Database:** SQLite (for simplicity in development, easily swappable with PostgreSQL/MySQL)
* **Caching & Circuit Breaker State:** Redis
* **Service Discovery:** Consul
* **Messaging:** RabbitMQ
* **Monitoring:** Prometheus, Grafana
* **Containerization:** Docker, Docker Compose
* **CI/CD:** GitHub Actions
* **Frontend:** HTML, CSS, JavaScript (served by Nginx)
* **Database Migrations:** Alembic (via Flask-Migrate)

## Prerequisites

Before you begin, ensure you have the following installed on your system:

* **Git:** For cloning the repository.
* **Docker Desktop:** Includes Docker Engine and Docker Compose.
* **Python 3.9+:** For local development and running Alembic commands.
* **`pip`:** Python package installer.
* **`venv`:** Python virtual environment module (usually comes with Python).

## Getting Started

Follow these steps to get the entire microservices ecosystem up and running.

### 1. Clone the Repository

```bash
git https://github.com/hemaabokila/-api-gateway-microservices.git
cd -api-gateway-microservices
```
**(Replace `hemaabokila/-api-gateway-microservices.git` with your actual repository URL)**

### 2. Initial Setup for Database Migrations (Alembic)
This step is crucial and needs to be done once per microservice locally to initialize the `migrations/` folder and generate the initial migration script.

**For** `microservices/users_service`:
```Bash

cd microservices/users_service
python -m venv venv
source venv/bin/activate  # On Linux/macOS
# venv\Scripts\activate   # On Windows
pip install -r requirements.txt

export FLASK_APP=app     # On Linux/macOS
# set FLASK_APP=app       # On Windows
flask db init
flask db migrate -m "initial users service migration"

deactivate
cd ../.. # Go back to the project root
```
**For** `microservices/products_service`:
```Bash

cd microservices/products_service
python -m venv venv
source venv/bin/activate  # On Linux/macOS
# venv\Scripts\activate   # On Windows
pip install -r requirements.txt

export FLASK_APP=app     # On Linux/macOS
# set FLASK_APP=app       # On Windows
flask db init
flask db migrate -m "initial products service migration"

deactivate
cd ../.. # Go back to the project root
```
**Important:** After running `flask db init` and `flask db migrate`, you will see a `migrations/` folder created in each microservice directory.

**Ensure these `migrations/`folders are committed to your Git repository.**

### 3. Build and Run with Docker Compose
This command will build all Docker images, set up the network, and start all services (Gateway, Users Service, Products Service, Redis, Consul, RabbitMQ, Prometheus, Grafana, Frontend).

```Bash

docker-compose down --volumes # Optional: Cleans up previous runs
docker-compose build          # Builds all service images
docker-compose up             # Starts all services
```
Allow a few moments for all services to start up.

You can monitor the logs in your terminal or use `docker-compose logs -f`.

# Usage & Accessing Services
Once all services are running, you can access them via your web browser:

1. **Frontend Dashboard:**

    * Access the simple web UI: `http://localhost:80` (or simply `http://localhost`)

    * Use the buttons to fetch users and products via the API Gateway.

2. **API Gateway:**

    * Base URL: `http://localhost:5000`

    * Example: `http://localhost:5000/proxy/users_service/users/` (to list users)

    * Example: `http://localhost:5000/proxy/products_service/products/` (to list products)

3. **Unified API Documentation (Swagger UI):**

    * Explore all aggregated API endpoints: `http://localhost:5000/docs/`

    * You can interact with the APIs directly from this interface.

4. **Consul UI (Service Registry):**

    * Monitor registered services and their health: `http://localhost:8500/ui`

    * You should see `users_service` and `products_service` listed as healthy.

5. **RabbitMQ Management Interface:**

    * Access the RabbitMQ dashboard: `http://localhost:15672`

    * Default credentials: `guest/guest`

    * You can monitor exchanges, queues, and messages here. When you create a user or product, you should see messages being published to the respective exchanges.

6. **Prometheus UI (Metrics):**

    * Explore collected metrics: `http://localhost:9090`

    * Go to "Status" -> "Targets" to ensure all services (gateway, users_service, products_service) are being scraped successfully.

    * You can query metrics like http_requests_total or http_request_duration_seconds here.

7. **Grafana UI (Dashboards & Visualization):**

    * Access powerful dashboards: `http://localhost:3000`

    * Default credentials: `admin/admin` (you'll be prompted to change it).

    * First time setup: Add a Prometheus data source pointing to `http://prometheus:9090`. Then, you can create custom dashboards to visualize your service metrics.

**Example API Calls (using `curl` or Postman/Insomnia)**

**Authentication (Gateway)**
```Bash

# Register a new user (via Gateway -> Users Service)
curl -X POST -H "Content-Type: application/json" -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}' http://localhost:5000/api/users/users

# Login (via Gateway -> Users Service)
curl -X POST -H "Content-Type: application/json" -d '{"email": "test@example.com", "password": "password123"}' http://localhost:5000/api/users/login
# This will return a JWT token. Copy it for subsequent authenticated requests.
```
**Users Service (via Gateway)**

```Bash

# Get all users (requires JWT token)
curl -X GET -H "Authorization: Bearer <YOUR_JWT_TOKEN>" http://localhost:5000/api/users/users

# Get a specific user by ID (requires JWT token)
curl -X GET -H "Authorization: Bearer <YOUR_JWT_TOKEN>" http://localhost:5000/api/users/users/1

# Update a user (requires JWT token)
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer <YOUR_JWT_TOKEN>" -d '{"username": "updated_user", "is_active": true}' http://localhost:5000/api/users/users/1

# Delete a user (requires JWT token)
curl -X DELETE -H "Authorization: Bearer <YOUR_JWT_TOKEN>" http://localhost:5000/api/users/users/1
```
**Products Service (via Gateway)**
```Bash

# Create a new product (requires JWT token)
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer <YOUR_JWT_TOKEN>" -d '{"name": "Laptop Pro", "description": "High-performance laptop", "price": 1200.00, "stock_quantity": 50}' http://localhost:5000/api/products/products

# Get all products (requires JWT token)
curl -X GET -H "Authorization: Bearer <YOUR_JWT_TOKEN>" http://localhost:5000/api/products/products

# Get a specific product by ID (requires JWT token)
curl -X GET -H "Authorization: Bearer <YOUR_JWT_TOKEN>" http://localhost:5000/api/products/products/1
```
# Development Workflow

**Running Tests Locally (via GitHub Actions)**
The CI/CD setup ensures tests run on every push.

You can also run them locally:

**For Gateway:**
```Bash

cd gateway
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests/
deactivate
cd ..
```
**For Users Service:**
```Bash

cd microservices/users_service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests/
deactivate
cd ../..
```
**For Products Service:**
```Bash

cd microservices/products_service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests/
deactivate
cd ../..
```
**Managing Database Migrations**

When you make changes to your SQLAlchemy models (`app/models.py`) in a microservice:

1. **Activate the service's virtual environment** (as shown in "Running Tests Locally").

2. **Generate a new migration script:**

```Bash

flask db migrate -m "Description of your changes"
```
3. **Review the generated script in `migrations/versions/`.**

4. **Apply the migration (locally for testing):**

```Bash

flask db upgrade
```
5. **Commit the new migration script** to your Git repository. When the Docker container for that service starts, `run.py` will automatically apply any pending migrations.

# Future Enhancements (Ideas for Further Exploration)

This project provides a solid foundation.

Here are some ideas to expand it further:

* **API Versioning:** Implement URL-based or header-based API versioning.

* **Distributed Tracing:** Integrate with tools like Jaeger or Zipkin to trace requests across multiple microservices.

* **API Gateway Authentication for Microservices:** Implement a mechanism for the Gateway to authenticate itself to downstream microservices (e.g., mTLS, internal JWT).

* **Centralized Configuration:** Use a configuration server (e.g., Consul KV, Spring Cloud Config) to manage configurations for all services.

* **Advanced Load Balancing:** Integrate with a more sophisticated load balancer (e.g., Nginx, HAProxy) in front of the Gateway.

* **API Gateway Aggregation:** For complex operations, implement logic in the Gateway to call multiple microservices and aggregate their responses.

* **GraphQL Gateway:** Replace or augment the REST Gateway with a GraphQL layer.

* **Security Enhancements:** Add OAuth2/OpenID Connect integration, input validation (using Marshmallow schemas more rigorously), and more granular authorization.

* **Consumer-Driven Contracts (CDC):** Use tools like Pact to ensure compatibility between services.

* **Real-time Dashboards:** Enhance the frontend dashboard with real-time updates using WebSockets.

* **Kubernetes Deployment:** Containerize and orchestrate the entire system using Kubernetes for production-grade deployment.

# Contributing
Contributions are welcome! If you have ideas for improvements, bug fixes, or new features, please feel free to:

1. Fork the repository.

2. Create a new branch (`git checkout -b feature/your-feature-name`).

3. Make your changes and write tests.

4. Commit your changes (`git commit -m 'Add new feature'`).

5. Push to your branch (`git push origin feature/your-feature-name`).

6. Open a Pull Request.

# License
This project is licensed under the MIT [LICENSE](LICENSE).