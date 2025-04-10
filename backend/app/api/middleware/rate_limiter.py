from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from app.utils.redis import get_redis
from app.utils.logging import logger
from datetime import timedelta
import re

# Rate limit presets (times/interval)
DEFAULT_LIMITS = {
    "auth": {"times": 10, "minutes": 1},
    "api": {"times": 60, "minutes": 1},
    "public": {"times": 100, "hours": 1},
    "webhooks": {"times": 5, "seconds": 1}
}

def parse_timespan(limit_key: str) -> int:
    """
    Convert limit preset to seconds
    Example: "10/minute" -> 60
    """
    config = DEFAULT_LIMITS[limit_key]
    if "seconds" in config:
        return config["seconds"]
    if "minutes" in config:
        return config["minutes"] * 60
    if "hours" in config:
        return config["hours"] * 3600
    return 60  # Default fallback

def noop_dependency():
    """A no-op dependency that does nothing."""
    pass

def get_limit(limit_key: str) -> RateLimiter:
    """
    Create rate limiter dependency from preset
    Usage: @router.get("/", dependencies=[Depends(get_limit("auth"))])
    """
    if limit_key not in DEFAULT_LIMITS:
        raise ValueError(f"Unknown limit key: {limit_key}")
    
    # Exclude webhooks from rate limiting
    if limit_key == "webhooks":
        return noop_dependency  # Return a no-op callable

    return RateLimiter(
        times=DEFAULT_LIMITS[limit_key]["times"],
        seconds=parse_timespan(limit_key)
    )

async def get_client_ip(request):
    return request.client.host or "127.0.0.1"

async def init_rate_limiter():
    """
    Initialize rate limiting with Redis connection
    """
    try:
        redis = await get_redis()
        
        # Verify connection
        if not await redis.ping():
            raise ConnectionError("Redis connection failed")
            
        # Initialize with custom settings
        await FastAPILimiter.init(
            redis,
            identifier=get_client_ip,
            http_callback=lambda: HTTPException(429, "Too many requests")
        )
        logger.info("Rate limiter initialized with Redis")
        
    except Exception as e:
        logger.critical(f"Rate limiter init failed: {str(e)}")
        raise

async def rate_limit_exception_handler(request: Request, exc: HTTPException):
    """
    Custom handler for rate limit exceeded responses
    """
    retry_after = exc.headers.get("Retry-After", 60) if exc.headers else 60
    
    logger.warning(
        f"Rate limit exceeded: {request.client.host} -> {request.method} {request.url.path} "
        f"(Retry after {retry_after}s)"
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests",
            "retry_after": retry_after,
            "documentation_url": "https://your-api.com/docs/rate-limits"
        },
        headers={"Retry-After": str(retry_after)}
    )