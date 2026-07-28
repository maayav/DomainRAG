"""API key authentication middleware."""
import hmac
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import API_KEY

API_KEY_HEADER = "x-api-key"

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        token = request.headers.get(API_KEY_HEADER, "")
        if API_KEY:
            if not token:
                raise HTTPException(status_code=401, detail="Missing API key")
            if not hmac.compare_digest(token.strip(), API_KEY.strip()):
                raise HTTPException(status_code=403, detail="Invalid API key")
        return await call_next(request)