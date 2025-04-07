# backend/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import asynccontextmanager
from app.config.settings import settings
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Connection pool configuration
POOL_SIZE = 15
MAX_OVERFLOW = 10
POOL_RECYCLE = 3600  # Recycle connections after 1 hour
POOL_PRE_PING = True  # Enable connection health checks

def get_sync_engine():
    """Create and configure synchronous SQLAlchemy engine"""
    return create_engine(
        settings.DATABASE_URL,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_pre_ping=POOL_PRE_PING,  # Check connections before use
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    )

def get_async_engine():
    """Create and configure asynchronous SQLAlchemy engine"""
    return create_async_engine(
        settings.ASYNC_DATABASE_URL,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_recycle=POOL_RECYCLE,
        pool_pre_ping=POOL_PRE_PING,
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    )

# Synchronous session setup
sync_engine = get_sync_engine()
engine = sync_engine  # For backward compatibility
SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=sync_engine,
        expire_on_commit=False  # Better for web apps
    )
)

# Asynchronous session setup
async_engine = get_async_engine()
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

def get_db():
    """Synchronous dependency for FastAPI endpoints"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        db.close()

@asynccontextmanager
async def async_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Asynchronous dependency for FastAPI endpoints"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Async database error: {str(e)}")
            raise