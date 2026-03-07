"""Authentication routes."""
import secrets
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ..config import config
from ..dependencies import require_user


router = APIRouter()
templates = Jinja2Templates(directory=config.TEMPLATE_DIR)


@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    """Display login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_post(
    request: Request, username: str = Form(...), password: str = Form(...)
):
    """Process login form submission."""
    if not config.WEB_REQUIRES_AUTH:
        request.session["user"] = "guest"
        return RedirectResponse("/", status_code=303)

    is_correct_username = secrets.compare_digest(
        username.encode("utf8"), config.WEB_USERNAME.encode("utf8")
    )
    is_correct_password = secrets.compare_digest(
        password.encode("utf8"), config.WEB_PASSWORD.encode("utf8")
    )

    if is_correct_username and is_correct_password:
        request.session["user"] = username
        return RedirectResponse("/", status_code=303)
    else:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"},
        )


@router.post("/logout")
async def logout(request: Request):
    """Log out the current user."""
    request.session.pop("user", None)
    return RedirectResponse("/", status_code=303)
