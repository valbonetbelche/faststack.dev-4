import httpx
from fastapi import HTTPException
from app.config.settings import settings
from typing import Optional, Dict, Any
from pydantic import BaseModel

class ClerkClient:
    def __init__(self):
        self.api_key = settings.CLERK_SECRET_KEY
        self.api_url = settings.CLERK_API_URL
        
    async def update_user_metadata(self, user_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Update Clerk user public metadata"""
        url = f"{self.api_url}/users/{user_id}/metadata"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "public_metadata": metadata
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Clerk API error: {str(e)}"
            )
    
    async def get_user_metadata(self, user_id: str) -> Dict[str, Any]:
        """Get Clerk user metadata"""
        url = f"{self.api_url}/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("public_metadata", {})
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Clerk API error: {str(e)}"
            )

# Singleton instance of the Clerk client
clerk_client = ClerkClient()