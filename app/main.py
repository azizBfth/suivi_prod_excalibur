#!/usr/bin/env python3
"""
FastAPI Application for Production Time Tracking - Excalibur ERP
Refactored from Streamlit to FastAPI for better scalability and hosting flexibility.
"""
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional
from fastapi.openapi.docs import get_swagger_ui_html

# Import our modular components
from app.core.config import get_settings
from app.core.database import init_analyzer, cleanup_analyzer
from app.routes import (
    dashboard_routes,
    dashboard_analytics_routes,
    of_routes,
    health_routes,
    auth_routes,
    admin_routes,
    email_routes
)

# Import additional routes that may exist
try:
    from app.routes import alert_routes
except ImportError:
    alert_routes = None

try:
    from app.routes import export_routes
except ImportError:
    export_routes = None

try:
    from app.routes import production_routes
except ImportError:
    production_routes = None

try:
    from app.routes import inventory_routes
except ImportError:
    inventory_routes = None

try:
    from app.routes import planning_routes
except ImportError:
    planning_routes = None

try:
    from app.routes import quality_routes
except ImportError:
    quality_routes = None

# Global analyzer instance (will be initialized on startup)
analyzer = None

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize the data analyzer on startup."""
    global analyzer
    try:
        analyzer = init_analyzer()
        print("✅ Data analyzer initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize data analyzer: {e}")
        analyzer = None
    yield
    # Cleanup on shutdown
    cleanup_analyzer()



# Create FastAPI app with lifespan
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Setup static files and templates
static_dir = Path("static")
templates_dir = Path("templates")

# Create directories if they don't exist
static_dir.mkdir(exist_ok=True)
templates_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include route modules
app.include_router(auth_routes.router)  # Authentication routes first
app.include_router(admin_routes.router)  # Admin routes
app.include_router(dashboard_routes.router)
app.include_router(dashboard_analytics_routes.router)
app.include_router(of_routes.router)
app.include_router(health_routes.router)
app.include_router(email_routes.router)

# Include optional routes if they exist
if alert_routes:
    app.include_router(alert_routes.router)
if export_routes:
    app.include_router(export_routes.router)
if production_routes:
    app.include_router(production_routes.router)
if inventory_routes:
    app.include_router(inventory_routes.router)
if planning_routes:
    app.include_router(planning_routes.router)
if quality_routes:
    app.include_router(quality_routes.router)

# Root route - redirect to login if not authenticated, otherwise show dashboard
@app.get("/")
async def root(request: Request):
    """Root route - redirect based on authentication status."""
    # Check for authentication cookie
    auth_cookie = request.cookies.get("access_token")
    if auth_cookie and auth_cookie.startswith("Bearer "):
        # Import here to avoid circular imports
        from app.services.auth_service import auth_service
        token = auth_cookie.split(" ")[1]
        user = auth_service.get_current_user(token)
        if user and user.is_active:
            # User is authenticated, redirect to dashboard
            return RedirectResponse(url="/dashboard", status_code=302)

    # User is not authenticated, redirect to login
    return RedirectResponse(url="/auth/login", status_code=302)


# Login route without auth prefix for convenience
@app.get("/login")
async def login_redirect():
    """Convenience redirect to auth login."""
    return RedirectResponse(url="/auth/login", status_code=302)


@app.get("/docs", include_in_schema=False)
async def swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="FastAPI",
        swagger_favicon_url="./favicon.ico"
    )

# All routes are now handled by the modular route system above

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI Production Tracking Application with Authentication")
    print("📍 Server will be available at: http://0.0.0.0:80")
    print("🔑 Login credentials: abo/HbB6yq+R+U or abo/abomk")
    print("-" * 60)
    # Disable reload when running from within another application context
    # Use reload=False to avoid signal handling issues
    uvicorn.run("main:app", host="0.0.0.0", port=80, reload=False)
