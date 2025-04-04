from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.auth.router import router as auth_router
from .api.v1.billing.router import router as billing_router
from .api.v1.user.router import router as user_router
from .api.v1.core.router import router as core_router
from app.config import settings
from .db.session import engine
from app.models.base import Base
import httpx
from fastapi.responses import PlainTextResponse

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



@app.head("/api/v1/healthcheck")
@app.get("/api/v1/healthcheck")
async def healthcheck():
    return {"status": "healthy"}

@app.get("/monitor/supabase")
@app.head("/monitor/supabase")
async def supabase_healthcheck():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://qhcfuheeufsutjkypubf.supabase.co/rest/v1/",
            headers={"apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFoY2Z1aGVldWZzdXRqa3lwdWJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMyNjIyMzAsImV4cCI6MjA1ODgzODIzMH0.sQB5yNvBElG3XLVUsMcMNdPlZxX9fKDj3TsT17jjs8c"}
        )
    return PlainTextResponse("OK" if response.is_success else "DOWN")