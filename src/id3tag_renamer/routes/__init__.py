"""Route modules for the web application."""


def register_routes(app):
    """Register all route modules with the FastAPI app."""
    # Import routes here to avoid circular imports
    from . import auth, files, tags, api

    # Auth routes
    app.include_router(auth.router)

    # File management routes
    app.include_router(files.router)

    # Tag management routes
    app.include_router(tags.router)

    # API routes
    app.include_router(api.router)
