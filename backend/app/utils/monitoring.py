# app/utils/monitoring.py

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CollectorRegistry
)
from fastapi import Request, Response, HTTPException
import time
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from app.config.settings import settings
import logging


def init_sentry():
    # Initialize Sentry if DSN is configured
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                SqlalchemyIntegration(),
                RedisIntegration(),
                LoggingIntegration(
                    level=logging.INFO,        # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors as events
                )
            ],
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            environment=settings.ENVIRONMENT,
            send_default_pii=True  # Optional: Enable if you need user data in errors
        )


# Create a custom registry
registry = CollectorRegistry()

# Metrics definitions
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Latency in Seconds',
    ['method', 'endpoint'],
    registry=registry,
    buckets=[0.1, 0.5, 1, 2.5, 5, 10]
)

IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'In-progress HTTP Requests',
    ['method', 'endpoint'],
    registry=registry
)

EXCEPTIONS_COUNT = Counter(
    'http_exceptions_total',
    'Total HTTP Exceptions',
    ['exception_type', 'endpoint'],
    registry=registry
)


# Middleware to track request metrics
async def prometheus_middleware(request: Request, call_next):
    method = request.method
    endpoint = request.url.path
    start_time = time.time()

    IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
    try:
        response = await call_next(request)
        duration = time.time() - start_time

        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()

        REQUEST_LATENCY.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        return response

    except Exception as e:
        duration = time.time() - start_time

        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=500
        ).inc()

        EXCEPTIONS_COUNT.labels(
            exception_type=type(e).__name__,
            endpoint=endpoint
        ).inc()

        raise

    finally:
        IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()


# Metrics endpoint
async def metrics_endpoint(request: Request):
    # Optional HTTPS-only check (keep if needed)
    if request.headers.get("X-Forwarded-Proto") == "https":
        return Response(
            content=generate_latest(registry),
            media_type="text/plain"
        )
    raise HTTPException(status_code=400, detail="Use HTTPS")
