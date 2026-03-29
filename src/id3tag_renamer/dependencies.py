"""FastAPI dependencies for dependency injection."""
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from .config import config


async def get_current_user(request: Request) -> Optional[str]:
    """Get the current authenticated user from session."""
    return request.session.get("user")


async def require_user(
    request: Request,
    current_user: Optional[str] = Depends(get_current_user),
) -> str:
    """
    Require authentication for a route.

    Raises:
        HTTPException: 401 if authentication is required and user is not logged in
    """
    if not config.WEB_REQUIRES_AUTH:
        return current_user or "guest"
    if not current_user:
        # Save the intended URL so login can redirect back to it
        request.session["next"] = str(request.url)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required"
        )
    return current_user
