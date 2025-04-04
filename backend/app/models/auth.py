from typing import Any, Optional, Dict

from fastapi import HTTPException, Request
from fastapi.openapi.models import HTTPBearer as HTTPBearerModel
from fastapi.security import HTTPAuthorizationCredentials as FastAPIHTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
import jwt
from jwt import PyJWKClient
from starlette.status import HTTP_403_FORBIDDEN
from typing_extensions import Annotated, Doc
from pydantic import BaseModel
from app.utils.clerk import clerk_client


class ClerkConfig(BaseModel):
    jwks_url: str
    audience: Optional[str] = None
    issuer: Optional[str] = None
    verify_exp: bool = True
    verify_aud: bool = False
    verify_iss: bool = False
    jwks_cache_keys: bool = False
    jwks_max_cached_keys: int = 16
    jwks_cache_set: bool = True
    jwks_lifespan: int = 300
    jwks_headers: Optional[Dict[str, Any]] = None
    jwks_client_timeout: int = 30


class HTTPAuthorizationCredentials(FastAPIHTTPAuthorizationCredentials):
    decoded: Optional[Dict[str, Any]] = None


class ClerkHTTPBearer(HTTPBearer):
    def __init__(
        self,
        config: ClerkConfig,
        bearerFormat: Annotated[Optional[str], Doc("Bearer token format.")] = None,
        scheme_name: Annotated[Optional[str], Doc("Security scheme name.")] = None,
        description: Annotated[Optional[str], Doc("Security scheme description.")] = None,
        auto_error: Annotated[bool, Doc("Automatically raise error if token is not provided.")] = True,
        debug_mode: bool = False,
    ):
        super().__init__(bearerFormat=bearerFormat, scheme_name=scheme_name, description=description, auto_error=auto_error)
        self.model = HTTPBearerModel(bearerFormat=bearerFormat, description=description)
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error
        self.config = config
        self._check_config()
        self.jwks_url = config.jwks_url
        self.audience = config.audience
        self.issuer = config.issuer
        self.jwks_client = PyJWKClient(
            uri=config.jwks_url,
            cache_keys=config.jwks_cache_keys,
            max_cached_keys=config.jwks_max_cached_keys,
            cache_jwk_set=config.jwks_cache_set,
            lifespan=config.jwks_lifespan,
            headers=config.jwks_headers,
            timeout=config.jwks_client_timeout,
        )
        self.debug_mode = debug_mode

    def _check_config(self) -> None:
        if not self.config.audience and self.config.verify_aud:
            raise ValueError("Audience must be set in config because verify_aud is True")
        if not self.config.issuer and self.config.verify_iss:
            raise ValueError("Issuer must be set in config because verify_iss is True")

    def _decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            print("DECODING TOKEN", token)
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                key=signing_key.key,
                audience=self.audience,
                issuer=self.issuer,
                algorithms=["RS256"],
                options={
                    "verify_exp": self.config.verify_exp,
                    "verify_aud": self.config.verify_aud,
                    "verify_iss": self.config.verify_iss,
                },
            )
        except Exception as e:
            print(f"Error decoding token: {e}")
            if self.debug_mode:
                raise e
            return None
        
    def get_user_id_from_token(token: str) -> str:
        """Extract user ID (sub) from decoded JWT"""
        decoded = clerk_client._decode_token(token)
        if not decoded or "sub" not in decoded:
            raise HTTPException(status_code=403, detail="Invalid token or missing user ID")
        return decoded["sub"]

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        authorization = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Not authenticated")
            return None
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid authentication credentials")
            return None

        decoded_token = self._decode_token(token=credentials)
        if not decoded_token and self.auto_error:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid authentication credentials")

        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials, decoded=decoded_token)