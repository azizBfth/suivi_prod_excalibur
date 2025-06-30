"""
Authentication routes for login, logout, and user management.
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services.auth_service import auth_service, ACCESS_TOKEN_EXPIRE_MINUTES
from app.middleware.auth_middleware import get_current_user, get_admin_user, get_optional_current_user
from app.models.schemas import (
    LoginRequest, LoginResponse, Token, User, UserResponse, 
    BaseResponse, ErrorResponse
)
import logging

# Setup logger
app_logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Templates
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: Optional[User] = Depends(get_optional_current_user)):
    """Display login page."""
    # If user is already authenticated, redirect to dashboard
    if user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_model=LoginResponse)
async def login(
    username: str = Form(...),
    password: str = Form(...),
    request: Request = None
):
    """
    Authenticate user and return JWT token.
    Supports both form data and JSON requests.
    """
    try:
        # Authenticate user
        user = auth_service.authenticate_user(username, password)
        if not user:
            app_logger.warning(f"Failed login attempt for username: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            app_logger.warning(f"Inactive user login attempt: {username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        app_logger.info(f"User logged in successfully: {username}")
        
        token_data = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        )
        
        # For form submissions (web interface), redirect to dashboard
        if request and request.headers.get("Content-Type", "").startswith("application/x-www-form-urlencoded"):
            response = RedirectResponse(url="/", status_code=302)
            # Set token as httpOnly cookie for web interface
            response.set_cookie(
                key="access_token",
                value=f"Bearer {access_token}",
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax"
            )
            return response
        
        # For API requests, return JSON response
        return LoginResponse(
            success=True,
            message="Login successful",
            data=token_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.post("/login-json", response_model=LoginResponse)
async def login_json(login_request: LoginRequest):
    """
    Authenticate user with JSON request and return JWT token.
    """
    try:
        # Authenticate user
        user = auth_service.authenticate_user(login_request.username, login_request.password)
        if not user:
            app_logger.warning(f"Failed login attempt for username: {login_request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            app_logger.warning(f"Inactive user login attempt: {login_request.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        app_logger.info(f"User logged in successfully: {login_request.username}")
        
        token_data = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        )
        
        return LoginResponse(
            success=True,
            message="Login successful",
            data=token_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.post("/logout")
async def logout_post(request: Request):
    """
    Logout user (POST method for API).
    """
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response


@router.get("/logout")
async def logout_get(request: Request):
    """
    Logout user (GET method for web interface).
    """
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        success=True,
        message="User information retrieved successfully",
        data=current_user
    )


@router.get("/users", response_model=BaseResponse)
async def list_users(admin_user: User = Depends(get_admin_user)):
    """List all users (admin only)."""
    try:
        users = auth_service.list_users()
        return BaseResponse(
            success=True,
            message="Users retrieved successfully",
            data={"users": users}
        )
    except Exception as e:
        app_logger.error(f"Error listing users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )


@router.post("/users/{username}/deactivate", response_model=BaseResponse)
async def deactivate_user(username: str, admin_user: User = Depends(get_admin_user)):
    """Deactivate a user account (admin only)."""
    try:
        if username == admin_user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        success = auth_service.deactivate_user(username)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        app_logger.info(f"User deactivated by admin: {username} (by {admin_user.username})")
        return BaseResponse(
            success=True,
            message=f"User {username} deactivated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error deactivating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deactivating user"
        )


@router.post("/users/{username}/activate", response_model=BaseResponse)
async def activate_user(username: str, admin_user: User = Depends(get_admin_user)):
    """Activate a user account (admin only)."""
    try:
        success = auth_service.activate_user(username)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        app_logger.info(f"User activated by admin: {username} (by {admin_user.username})")
        return BaseResponse(
            success=True,
            message=f"User {username} activated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error activating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error activating user"
        )
