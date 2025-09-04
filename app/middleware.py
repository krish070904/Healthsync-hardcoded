from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from .auth import SECRET_KEY, ALGORITHM
from typing import List
import re

# List of paths that don't require authentication
PUBLIC_PATHS = [
    "/",  # Root path
    "/health",  # Health check endpoint
    "/token",  # Login endpoint
    "/users/",  # User registration
    "/static/.*",  # Static files
    "/docs",  # Swagger docs
    "/openapi.json",  # OpenAPI schema
    "/redoc",  # ReDoc
    "/predictions",  # HTML page
    "/progress-tracker",  # HTML page
    "/health-consultation",  # HTML page
    "/symptoms",  # Symptoms tracking page
    "/meals",  # Meals planning page
    "/profile",  # User profile page
    "/progress",  # Progress page
    "/alerts",  # Alerts page
    "/analysis",  # Analysis page
    "/consultation",  # Consultation page
    "/login",  # Login page
    "/register",  # Registration page
    "/@vite/client",  # Vite client for development
]

# Compile regex patterns for public paths
PUBLIC_PATHS_PATTERNS = [re.compile(f"^{path}$") for path in PUBLIC_PATHS]


class AuthMiddleware:
    """Middleware for JWT authentication"""
    
    async def __call__(self, request: Request, call_next):
        path = request.url.path
        
        # Check if the path is public
        if self._is_public_path(path):
            return await call_next(request)
        
        # Check for authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = authorization.replace("Bearer ", "")
        
        try:
            # Verify token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Add user info to request state
            request.state.user = {"username": username}
            
        except JWTError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return await call_next(request)
    
    def _is_public_path(self, path: str) -> bool:
        """Check if the path is public and doesn't require authentication"""
        for pattern in PUBLIC_PATHS_PATTERNS:
            if pattern.match(path):
                return True
        return False


def add_auth_middleware(app):
    """Add authentication middleware to the FastAPI app"""
    from starlette.middleware.base import BaseHTTPMiddleware
    app.add_middleware(BaseHTTPMiddleware, dispatch=AuthMiddleware())