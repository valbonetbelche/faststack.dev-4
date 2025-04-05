from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    REGISTRY,
    CollectorRegistry
)
from fastapi import Response, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os

# Create a separate registry to avoid conflicts
registry = CollectorRegistry()

# Define metrics with explicit registry
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Latency',
    ['method', 'endpoint'],
    registry=registry,
    buckets=[0.1, 0.5, 1, 2.5, 5, 10]  # Betterstack-friendly buckets
)

# Metrics endpoint
def get_metrics():
    return Response(
        content=generate_latest(registry),
        media_type="text/plain"
    )