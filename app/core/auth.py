"""
Simple authentication middleware for API protection.

Supports:
- API key authentication via Authorization header or X-API-Key header
- Optional domain/origin validation
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os


# Hardcoded API key - can be overridden via environment variable
# For production, set this via: fly secrets set API_KEY=your-secret-key
API_KEY = os.getenv("API_KEY", "eidos-dev-key-change-me")

# Allowed domains (optional - leave empty to disable domain checking)
# Set via: fly secrets set ALLOWED_DOMAINS=example.com,app.example.com
ALLOWED_DOMAINS = os.getenv("ALLOWED_DOMAINS", "").split(",") if os.getenv("ALLOWED_DOMAINS") else []

# Endpoints that don't require authentication
PUBLIC_ENDPOINTS = ["/health", "/docs", "/openapi.json", "/redoc", "/"]


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to check API key and optionally validate domain."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in PUBLIC_ENDPOINTS:
            return await call_next(request)
        
        # Extract API key from headers
        api_key = None
        
        # Check Authorization header (Bearer token)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
        # Check X-API-Key header
        elif "X-API-Key" in request.headers:
            api_key = request.headers["X-API-Key"]
        
        # Validate API key
        if not api_key or api_key != API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key. Provide API key via Authorization: Bearer <key> or X-API-Key header.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Optional: Validate domain/origin
        if ALLOWED_DOMAINS:
            origin = request.headers.get("Origin", "")
            referer = request.headers.get("Referer", "")
            
            # Extract domain from origin/referer
            domain = None
            if origin:
                try:
                    domain = origin.split("//")[1].split("/")[0].split(":")[0]
                except:
                    pass
            elif referer:
                try:
                    domain = referer.split("//")[1].split("/")[0].split(":")[0]
                except:
                    pass
            
            # Check if domain is allowed
            if domain and domain not in ALLOWED_DOMAINS:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Domain '{domain}' is not allowed. Allowed domains: {', '.join(ALLOWED_DOMAINS)}"
                )
        
        # Continue with request
        response = await call_next(request)
        return response

