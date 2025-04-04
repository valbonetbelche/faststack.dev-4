from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    # Monitoring
    BETTERSTACK_SOURCE_TOKEN: str
    BETTERSTACK_INGESTING_HOST: str
    # Database
    DATABASE_URL: str
    
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
    
    # App Settings
    FROM_EMAIL: str = "noreply@yourdomain.com"
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env.local"
        env_file_encoding = 'utf-8'
        extra = "ignore"  # Silently ignore extra env vars

settings = Settings()