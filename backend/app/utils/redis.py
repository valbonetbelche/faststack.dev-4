from redis import asyncio as aioredis
from app.config.settings import settings
from typing import Optional, Any
from functools import wraps
import pickle
import json
import inspect

redis_client = None

async def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            ssl=True,
            decode_responses=False  # Important for caching binary data
        )
    return redis_client

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

# Cache Operations
async def cache_get(key: str) -> Optional[Any]:
    """Get cached data with automatic deserialization"""
    redis = await get_redis()
    data = await redis.get(key)
    if data:
        try:
            return pickle.loads(data)
        except:
            try:
                return json.loads(data.decode('utf-8'))
            except:
                return data
    return None

async def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set cached data with automatic serialization"""
    redis = await get_redis()
    try:
        if isinstance(value, (str, int, float, bool)):
            serialized = json.dumps(value).encode('utf-8')
        else:
            serialized = pickle.dumps(value)
        return await redis.set(key, serialized, ex=ttl)
    except Exception as e:
        logger.error(f"Cache set failed for key {key}: {str(e)}")
        return False

async def cache_delete(key: str) -> bool:
    """Delete cached data"""
    redis = await get_redis()
    return await redis.delete(key) > 0

# Cache Decorator
def cached(ttl: int = 300, key_prefix: str = "cache"):
    def decorator(func):
        is_async = inspect.iscoroutinefunction(func)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if 'request' in kwargs and kwargs['request'].method not in ('GET', 'HEAD'):
                return await func(*args, **kwargs) if is_async else func(*args, **kwargs)

            cache_key = f"{key_prefix}:{func.__module__}:{func.__name__}"
            if 'request' in kwargs:
                cache_key += f":path:{kwargs['request'].url.path}"

            cached_result = await cache_get(cache_key)
            if cached_result is not None:
                return cached_result

            result = await func(*args, **kwargs) if is_async else func(*args, **kwargs)
            await cache_set(cache_key, result, ttl)
            return result

        return async_wrapper
    return decorator
