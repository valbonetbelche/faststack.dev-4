from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional
import os

class Settings(BaseSettings):
    ENVIRONMENT: str
    
    # Monitoring
    BETTERSTACK_SOURCE_TOKEN: str
    BETTERSTACK_INGESTING_HOST: str
    SENTRY_DSN: str
    
    # Database
    DATABASE_URL: str
    DATABASE_ASYNC_URL: str
    DATABASE_SSL: bool
    DATABASE_POOL_SIZE: int
    DATABASE_MAX_OVERFLOW: int
    DATABASE_POOL_RECYCLE: int
    DATABASE_POOL_PRE_PING: bool
    
    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    
    # Clerk
    CLERK_API_URL: str
    CLERK_SECRET_KEY: str
    CLERK_JWKS_ENDPOINT: str
    CLERK_JWT_AUDIENCE: str
    CLERK_JWT_ISSUER: str
    CLERK_PUBLISHABLE_KEY: Optional[str] = None  # For frontend
    CLERK_JWT_PUBLIC_KEY: Optional[str] = None
    CLERK_WEBHOOK_SECRET: Optional[str] = None
    
    # Stripe
    FRONTEND_URL: str
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None  # For frontend
    
    # Email/SMS
    SENDGRID_API_KEY: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    
    FROM_EMAIL: str = "noreply@yourdomain.com"
    
    # API Documentation
    API_BASE_URL: str = "http://localhost:8000"
    API_DESCRIPTION: str = "Production SaaS API"
    API_VERSION: str = "1.0.0"
    DOCS_SWAGGER_URL: Optional[str] = "/docs"
    DOCS_REDOC_URL: Optional[str] = "/redoc"
    OPENAPI_URL: Optional[str] = "/openapi.json"
    OPENAPI_TAGS_METADATA: list[dict]
    
    # Disable docs in production
    @field_validator('DOCS_SWAGGER_URL', 'DOCS_REDOC_URL', 'OPENAPI_URL', mode='before')
    def validate_docs(cls, v, values):
        if values.data.get('ENVIRONMENT') == "production":
            return None
        return v
    
    class Config:
        env_file = ".env.local"
        env_file_encoding = 'utf-8'
        extra = "ignore"  # Silently ignore extra env vars

settings = Settings()