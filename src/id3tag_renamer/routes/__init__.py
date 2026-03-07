"""Route modules for the web application."""
from fastapi import APIRouter
from . import auth, files, tags, api


def register_routes(app):
    """Register all route modules with the FastAPI app."""
    # Auth routes
    app.include_router(auth.router)

    # File management routes
    app.include_router(files.router)

    # Tag management routes
    app.include_router(tags.router)

    # API routes
    app.include_router(api.router)
