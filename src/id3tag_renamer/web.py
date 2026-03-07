"""ID3Tag-Renamer Web Application."""
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

from id3tag_renamer import MusicManager
from .config import config
from .middleware import csrf_middleware
from .routes import register_routes


# Create FastAPI app
app = FastAPI(title="ID3Tag-Renamer")

# Mount static files
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

# Initialize global state
manager = MusicManager(directory=None)
templates = Jinja2Templates(directory=config.TEMPLATE_DIR)

# Add middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=config.WEB_SESSION_SECRET.encode(),
    max_age=config.SESSION_MAX_AGE,
)
app.middleware("http")(csrf_middleware)


# Exception handlers
@app.exception_handler(HTTPException)
async def unauthorized_handler(request: Request, exc: HTTPException):
    """Redirect unauthorized requests to login page."""
    if exc.status_code == 401:
        return RedirectResponse(url="/login", status_code=303)
    raise exc


# Register all routes
register_routes(app)


def main():
    """Run the web application."""
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
