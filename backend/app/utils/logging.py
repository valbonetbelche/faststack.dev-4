import logging
from logtail import LogtailHandler
from app.config.settings import settings
from fastapi import Request, Response, HTTPException
import time

def setup_logger(name=__name__):
    """Configure and return a logger with both console and BetterStack (Logtail) handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # BetterStack/Logtail handler (only if token is configured)
    if settings.BETTERSTACK_SOURCE_TOKEN:
        logtail_handler = LogtailHandler(
            source_token=settings.BETTERSTACK_SOURCE_TOKEN,
            host=settings.BETTERSTACK_INGESTING_HOST
        )
        # Simplified formatter that puts key info in the message
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
        raise

    duration = (time.time() - start_time) * 1000
    if request.url.path not in ["/api/v1/healthcheck"]:
        logger.info(f"Completed {request.method} {request.url.path} {response.status_code} in {duration:.2f}ms")

    return response

logger = setup_logger("app")