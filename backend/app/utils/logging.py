import logging
from logtail import LogtailHandler
from app.config.settings import settings
from fastapi import Request, Response, HTTPException
import time
import sentry_sdk

def setup_logger(name=__name__):
    """Configure and return a logger with Sentry integration"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # BetterStack/Logtail handler
    if settings.BETTERSTACK_SOURCE_TOKEN:
        logtail_handler = LogtailHandler(
            source_token=settings.BETTERSTACK_SOURCE_TOKEN,
            host=settings.BETTERSTACK_INGESTING_HOST
        )
        logtail_formatter = logging.Formatter('%(message)s')
        logtail_handler.setFormatter(logtail_formatter)
        logger.addHandler(logtail_handler)

    return logger

async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    if request.url.path not in ["/api/v1/healthcheck"]:
        logger.info(f"{request.method} {request.url.path} from {request.client.host}")

    try:
        response = await call_next(request)
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Failed {request.method} {request.url.path} in {duration:.2f}ms", exc_info=True)
        
        # Capture exception in Sentry if configured
        if settings.SENTRY_DSN:
            with sentry_sdk.push_scope() as scope:
                scope.set_context("request", {
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers)
                })
                sentry_sdk.capture_exception(e)
        raise

    duration = (time.time() - start_time) * 1000
    if request.url.path not in ["/api/v1/healthcheck"]:
        logger.info(f"Completed {request.method} {request.url.path} {response.status_code} in {duration:.2f}ms")

    return response

logger = setup_logger("app")