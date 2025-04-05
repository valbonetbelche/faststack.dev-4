from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
from app.db.session import engine
from app.models.base import Base
from app.utils.logging import logger
from app.api.v1.auth.router import router as auth_router
from app.api.v1.billing.router import router as billing_router
from app.api.v1.user.router import router as user_router
from app.api.v1.core.router import router as core_router
import logging
from fastapi import FastAPI, Request, HTTPException
from app.utils.monitoring import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    get_metrics
)
# Initialize FastAPI app
app = FastAPI(title="Your SaaS API")

# Add this route AFTER all other routes
@app.get("/metrics")
async def metrics(request: Request):
    # Bypass Render's redirect for health checks
    if request.headers.get("X-Forwarded-Proto") == "https":
        return get_metrics()
    raise HTTPException(status_code=400, detail="Use HTTPS")

@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """Middleware to record metrics"""
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    
    try:
        response = await call_next(request)
        
        # Record metrics
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
        
    except Exception as e:
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=500
        ).inc()
        raise

# Create database tables (use migrations in production)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")
except Exception as e:
    logger.error("Failed to initialize database tables", exc_info=True)
    raise

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Skip healthcheck logging
    if request.url.path not in ["/api/v1/healthcheck"]:
        logger.info(
            f"{request.method} {request.url.path} from {request.client.host}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "ip": request.client.host,
                "type": "request_start"
            }
        )
    
    try:
        response = await call_next(request)
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(
            f"Failed {request.method} {request.url.path} in {duration:.2f}ms",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration,
                "error": str(e),
                "type": "request_failure",
                "stack_trace": logging.Formatter().formatException(e)
            },
            exc_info=True
        )
        raise
    
    duration = (time.time() - start_time) * 1000
    if request.url.path not in ["/api/v1/healthcheck"]:
        logger.info(
            f"Completed {request.method} {request.url.path} {response.status_code} in {duration:.2f}ms",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration,
                "type": "request_complete"
            }
        )
    
    return response

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(billing_router, prefix="/api/v1/billing", tags=["billing"])
app.include_router(user_router, prefix="/api/v1/user", tags=["user"])
app.include_router(core_router, prefix="/api/v1/core", tags=["core"])

# Healthcheck endpoints
@app.head("/api/v1/healthcheck")
@app.get("/api/v1/healthcheck")
async def healthcheck():
    return {"status": "healthy"}

