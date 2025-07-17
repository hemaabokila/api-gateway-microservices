import time
from flask import Blueprint, Response, request, g
from prometheus_client import generate_latest, Counter, Histogram, Gauge


REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status_code']
)


REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Latency',
    ['method', 'endpoint', 'status_code']
)

IN_PROGRESS_REQUESTS = Gauge(
    'http_requests_in_progress',
    'Number of in-progress HTTP requests',
    ['method', 'endpoint']
)

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

@metrics_bp.before_app_request
def before_request_metrics():
    g.start_time = time.time()
    endpoint = request.endpoint if request.endpoint else 'unknown'
    IN_PROGRESS_REQUESTS.labels(request.method, endpoint).inc()

@metrics_bp.after_app_request
def after_request_metrics(response):
    if hasattr(g, 'start_time'):
        request_latency = time.time() - g.start_time
        endpoint = request.endpoint if request.endpoint else 'unknown'
        status_code = response.status_code

        REQUEST_COUNT.labels(request.method, endpoint, status_code).inc()
        REQUEST_LATENCY.labels(request.method, endpoint, status_code).observe(request_latency)
        IN_PROGRESS_REQUESTS.labels(request.method, endpoint).dec()

    return response

