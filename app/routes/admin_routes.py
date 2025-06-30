"""
Admin routes for user management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pydantic import BaseModel

from app.middleware.auth_middleware import get_admin_user
from app.services.auth_service import auth_service
from app.models.schemas import User, BaseResponse
import logging

# Setup logger
app_logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/admin", tags=["Administration"])

# Templates
templates = Jinja2Templates(directory="templates")


class CreateUserRequest(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: str = "user"


@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(request: Request, admin_user: User = Depends(get_admin_user)):
    """Admin users management page."""
    users = auth_service.list_users()
    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "users": users,
        "current_user": admin_user
    })


@router.post("/users/create", response_model=BaseResponse)
async def create_user(
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    email: str = Form(""),
    role: str = Form("user"),
    admin_user: User = Depends(get_admin_user)
):
    """Create a new user."""
    try:
        # Validate role
        if role not in ["admin", "res", "user"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'admin', 'res', or 'user'"
            )

        # Check if user already exists
        existing_user = auth_service.get_user(username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{username}' already exists"
            )

        # Create new user
        new_user = auth_service.add_user(
            username=username,
            password=password,
            full_name=full_name or username,
            email=email or f"{username}@company.com",
            role=role
        )
        
        app_logger.info(f"New user created: {username} (by {admin_user.username})")
        
        return BaseResponse(
            success=True,
            message=f"User '{username}' created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error creating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )


@router.get("/users/{username}", response_model=BaseResponse)
async def get_user(username: str, admin_user: User = Depends(get_admin_user)):
    """Get user details."""
    try:
        user = auth_service.get_user(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' not found"
            )

        user_data = {
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": "admin" if user.username == "admin" else "user"
        }

        return BaseResponse(
            success=True,
            message="User retrieved successfully",
            data=user_data
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error retrieving user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user"
        )


@router.put("/users/{username}", response_model=BaseResponse)
async def update_user(
    username: str,
    full_name: str = Form(...),
    email: str = Form(...),
    role: str = Form("user"),
    is_active: bool = Form(True),
    admin_user: User = Depends(get_admin_user)
):
    """Update user information."""
    try:
        # Validate role
        if role not in ["admin", "res", "user"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'admin', 'res', or 'user'"
            )

        # Update user using the auth service
        updated_user = auth_service.update_user(
            username=username,
            full_name=full_name,
            email=email,
            role=role,
            is_active=is_active
        )

        app_logger.info(f"User updated: {username} (by {admin_user.username})")

        return BaseResponse(
            success=True,
            message=f"User '{username}' updated successfully",
            data={
                "username": updated_user.username,
                "full_name": updated_user.full_name,
                "email": updated_user.email,
                "role": updated_user.role,
                "is_active": updated_user.is_active
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error updating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )


@router.post("/users/{username}/password", response_model=BaseResponse)
async def change_user_password(
    username: str,
    new_password: str = Form(...),
    admin_user: User = Depends(get_admin_user)
):
    """Change user password."""
    try:
        # Check if user exists
        user = auth_service.get_user(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' not found"
            )

        # Change password using auth service
        auth_service.change_password(username, new_password)

        app_logger.info(f"Password changed for user: {username} (by {admin_user.username})")

        return BaseResponse(
            success=True,
            message=f"Password changed for user '{username}'"
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error changing password: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing password"
        )


@router.delete("/users/{username}", response_model=BaseResponse)
async def delete_user(username: str, admin_user: User = Depends(get_admin_user)):
    """Delete a user."""
    try:
        # Check if user exists
        user = auth_service.get_user(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' not found"
            )

        # Prevent admin from deleting themselves
        if username == admin_user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        # Delete user using auth service (includes admin protection)
        auth_service.delete_user(username)

        app_logger.info(f"User deleted: {username} (by {admin_user.username})")

        return BaseResponse(
            success=True,
            message=f"User '{username}' deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error deleting user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting user"
        )





@router.get("/users/export", response_model=BaseResponse)
async def export_users(admin_user: User = Depends(get_admin_user)):
    """Export users list."""
    try:
        users = auth_service.list_users()
        
        # Convert to exportable format
        users_data = []
        for username, user in users.items():
            users_data.append({
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "role": "admin" if user.username == "admin" else "user"
            })
        
        return BaseResponse(
            success=True,
            message="Users exported successfully",
            data={"users": users_data}
        )
        
    except Exception as e:
        app_logger.error(f"Error exporting users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting users"
        )
