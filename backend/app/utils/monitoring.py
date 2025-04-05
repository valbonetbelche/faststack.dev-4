from prometheus_client import Counter, Histogram, make_asgi_app
from fastapi import Request
import time

# Custom metrics definitions
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Latency',
    ['method', 'endpoint']
)

# Initialize metrics app
metrics_app = make_asgi_app()

def instrument_requests(app):
    """Middleware to track request count and latency"""
    @app.middleware("http")
    async def monitor_requests(request: Request, call_next):
        start_time = time.time()
        method = request.method
        endpoint = request.url.path
        
        response = await call_next(request)
        
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=method,
            endpoint=endpoint
        ).observe(time.time() - start_time)
        
        return response
    
    return app