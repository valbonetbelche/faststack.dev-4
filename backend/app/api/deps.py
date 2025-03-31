# backend/app/api/deps.py
from fastapi import Request, Depends
from app.models.auth import ClerkHTTPBearer, ClerkConfig, HTTPAuthorizationCredentials
from app.config.settings import settings

# Configure Clerk (adjust verify_aud/verify_iss as needed)
clerk_config = ClerkConfig(
    jwks_url=settings.CLERK_JWKS_ENDPOINT,
    audience=settings.CLERK_JWT_AUDIENCE,
    issuer=settings.CLERK_JWT_ISSUER,
    verify_aud=False,  # Set to True if using custom audience
    verify_iss=False,  # Set to True if verifying issuer
    jwks_cache_keys=True  # Better performance
)

clerk_auth = ClerkHTTPBearer(config=clerk_config)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(clerk_auth)
) -> dict:
    """Dependency that returns the decoded JWT payload."""
    return credentials.decoded