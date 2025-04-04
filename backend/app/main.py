from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.auth.router import router as auth_router
from .api.v1.billing.router import router as billing_router
from .api.v1.user.router import router as user_router
from .api.v1.core.router import router as core_router
from app.config import settings
from .db.session import engine
from app.models.base import Base

app = FastAPI(title="Your SaaS API")

# Create tables (remove in production, use migrations instead)
Base.metadata.create_all(bind=engine)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(billing_router, prefix="/api/v1/billing", tags=["billing"])
app.include_router(user_router, prefix="/api/v1/user", tags=["user"])
app.include_router(core_router, prefix="/api/v1/core", tags=["core"])

@app.get("/healthcheck", methods=["GET", "HEAD"])
async def healthcheck():
    return {"status": "healthy"}