# main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine
from app.models.base import Base
from app.utils.logging import logger
from app.api.v1.auth.router import router as auth_router
from app.api.v1.billing.router import router as billing_router
from app.api.v1.user.router import router as user_router
from app.api.v1.core.router import router as core_router
from app.utils.monitoring import prometheus_middleware, metrics_endpoint
import time

app = FastAPI(title="Your SaaS API")

# Monitoring middleware (register early)
app.middleware("http")(prometheus_middleware)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    if request.url.path not in ["/api/v1/healthcheck"]:
        logger.info(f"{request.method} {request.url.path} from {request.client.host}")

    try:
        response = await call_next(request)
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Failed {request.method} {request.url.path} in {duration:.2f}ms", exc_info=True)
        raise

    duration = (time.time() - start_time) * 1000
    if request.url.path not in ["/api/v1/healthcheck"]:
        logger.info(f"Completed {request.method} {request.url.path} {response.status_code} in {duration:.2f}ms")

    return response

# Metrics route
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])

# Healthcheck
@app.head("/api/v1/healthcheck")
@app.get("/api/v1/healthcheck")
async def healthcheck():
    return {"status": "healthy"}

# Simulate error for development
@app.get("/api/v1/dev-error")
async def dev_error():
    raise ValueError("Intentional error")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init DB
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")
except Exception as e:
    logger.error("Failed to initialize database tables", exc_info=True)
    raise

# Routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(billing_router, prefix="/api/v1/billing", tags=["billing"])
app.include_router(user_router, prefix="/api/v1/user", tags=["user"])
app.include_router(core_router, prefix="/api/v1/core", tags=["core"])
