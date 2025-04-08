# main.py

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine
from app.models.base import Base
from app.utils.logging import logger, logging_middleware
from app.api.v1.auth.router import router as auth_router
from app.api.v1.billing.router import router as billing_router
from app.api.v1.user.router import router as user_router
from app.api.v1.core.router import router as core_router
from app.utils.redis import close_redis
from app.utils.monitoring import (
    prometheus_middleware,
    metrics_endpoint,
    init_sentry
)
from app.api.middleware.rate_limiter import init_rate_limiter, rate_limit_exception_handler, get_limit
from app.config.settings import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title="Your SaaS API",
        description=settings.API_DESCRIPTION,
        version=settings.API_VERSION,
        redoc_url=settings.DOCS_REDOC_URL,
        docs_url=settings.DOCS_SWAGGER_URL,
        openapi_url=settings.OPENAPI_URL,
        servers=[
            {
                "url": settings.API_BASE_URL,
                "description": settings.ENVIRONMENT
            }
        ],
        # Security headers
        openapi_tags=settings.OPENAPI_TAGS_METADATA
    )
    return app

app = create_app()
# Add rate limiter exception handler
app.add_exception_handler(HTTPException, rate_limit_exception_handler)

# Monitoring middleware (register early)
app.middleware("http")(prometheus_middleware)

# Request logging middleware
app.middleware("http")(logging_middleware)

# Sentry initialization (if configured)
init_sentry()

# Metrics route
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])

# Healthcheck
@app.head("/api/v1/healthcheck", dependencies=[Depends(get_limit("public"))])
@app.get("/api/v1/healthcheck", dependencies=[Depends(get_limit("public"))])
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

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    try:
        # Initialize database
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized")
        
        # Initialize Redis rate limiter
        await init_rate_limiter()
        logger.info("Rate limiter initialized")
        
    except Exception as e:
        logger.error("Failed during startup", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown():
    try:
        await close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error("Error during shutdown", exc_info=True)

# Routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(billing_router, prefix="/api/v1/billing", tags=["billing"])
app.include_router(user_router, prefix="/api/v1/user", tags=["user"])
app.include_router(core_router, prefix="/api/v1/core", tags=["core"])