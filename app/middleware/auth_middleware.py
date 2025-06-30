"""
Authentication middleware for protecting routes and validating JWT tokens.
"""

from typing import Optional
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from app.services.auth_service import auth_service
from app.models.schemas import User
import logging

# Setup logger
app_logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """Authentication middleware for JWT token validation."""

    @staticmethod
    async def get_current_user(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> User:
        """
        Get current authenticated user from JWT token.
        Raises HTTPException if authentication fails.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        token = None

        # Try to get token from Authorization header first
        if credentials:
            token = credentials.credentials
        else:
            # Try to get token from cookie for web interface
            auth_cookie = request.cookies.get("access_token")
            if auth_cookie and auth_cookie.startswith("Bearer "):
                token = auth_cookie.split(" ")[1]

        if not token:
            app_logger.warning("No authentication credentials provided")
            raise credentials_exception
        user = auth_service.get_current_user(token)
        
        if user is None:
            app_logger.warning(f"Invalid token provided: {token[:20]}...")
            raise credentials_exception
        
        if not user.is_active:
            app_logger.warning(f"Inactive user attempted access: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        app_logger.debug(f"User authenticated successfully: {user.username}")
        return user

    @staticmethod
    async def get_current_active_user(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        Get current active user (alias for get_current_user for clarity).
        """
        return current_user

    @staticmethod
    async def get_optional_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[User]:
        """
        Get current user if authenticated, otherwise return None.
        Does not raise exceptions for unauthenticated requests.
        """
        if not credentials:
            return None

        token = credentials.credentials
        user = auth_service.get_current_user(token)
        
        if user and user.is_active:
            return user
        
        return None

    @staticmethod
    def require_auth(request: Request) -> bool:
        """
        Check if the current request requires authentication.
        Returns True if authentication is required, False otherwise.
        """
        # Public endpoints that don't require authentication
        public_endpoints = {
            "/",
            "/login",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/static",
            "/favicon.ico"
        }
        
        path = request.url.path
        
        # Check if path starts with any public endpoint
        for endpoint in public_endpoints:
            if path.startswith(endpoint):
                return False
        
        # All other endpoints require authentication
        return True

    @staticmethod
    async def check_authentication(request: Request) -> Optional[RedirectResponse]:
        """
        Check if request is authenticated for protected routes.
        Returns RedirectResponse to login if authentication is required but not provided.
        """
        if not AuthMiddleware.require_auth(request):
            return None
        
        # Check for authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # For web requests, redirect to login
            if request.headers.get("Accept", "").startswith("text/html"):
                return RedirectResponse(url="/login", status_code=302)
            # For API requests, let the dependency handle the 401
            return None
        
        # Extract token and validate
        token = auth_header.split(" ")[1]
        user = auth_service.get_current_user(token)
        
        if not user or not user.is_active:
            # For web requests, redirect to login
            if request.headers.get("Accept", "").startswith("text/html"):
                return RedirectResponse(url="/login", status_code=302)
            # For API requests, let the dependency handle the 401
            return None
        
        return None


# Dependency functions for easy import
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """Get current authenticated user."""
    return await AuthMiddleware.get_current_user(request, credentials)


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    return current_user


async def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    return await AuthMiddleware.get_optional_current_user(credentials)


# Role-based access dependencies
async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify admin privileges."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def get_chef_or_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify chef or admin privileges."""
    if current_user.role not in ["admin", "chef"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chef or Admin privileges required"
        )
    return current_user


async def get_any_authenticated_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get any authenticated user (admin, chef, or user)."""
    return current_user
