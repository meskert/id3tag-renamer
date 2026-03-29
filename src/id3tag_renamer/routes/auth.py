"""Authentication routes."""
import secrets
import time
from collections import defaultdict
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ..config import config
from ..dependencies import require_user


router = APIRouter()
templates = Jinja2Templates(directory=config.TEMPLATE_DIR)

# Brute-force protection: track failed attempts per IP
_MAX_ATTEMPTS = 10
_LOCKOUT_SECONDS = 300  # 5 minutes
_ATTEMPT_WINDOW = 300   # reset counter after 5 minutes of inactivity

_failed_attempts: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _is_locked_out(ip: str) -> bool:
    now = time.monotonic()
    recent = [t for t in _failed_attempts[ip] if now - t < _ATTEMPT_WINDOW]
    _failed_attempts[ip] = recent
    return len(recent) >= _MAX_ATTEMPTS


def _record_failure(ip: str) -> None:
    _failed_attempts[ip].append(time.monotonic())


def _clear_failures(ip: str) -> None:
    _failed_attempts.pop(ip, None)


@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    """Display login page."""
    return templates.TemplateResponse(request, "login.html", {})


@router.post("/login")
async def login_post(
    request: Request, username: str = Form(...), password: str = Form(...)
):
    """Process login form submission."""
    if not config.WEB_REQUIRES_AUTH:
        request.session["user"] = "guest"
        next_url = request.session.pop("next", "/")
        return RedirectResponse(next_url, status_code=303)

    ip = _client_ip(request)

    if _is_locked_out(ip):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Too many failed attempts. Try again later."},
            status_code=429,
        )

    is_correct_username = secrets.compare_digest(
        username.encode("utf8"), config.WEB_USERNAME.encode("utf8")
    )
    is_correct_password = secrets.compare_digest(
        password.encode("utf8"), config.WEB_PASSWORD.encode("utf8")
    )

    if is_correct_username and is_correct_password:
        _clear_failures(ip)
        request.session.clear()
        request.session["user"] = username
        next_url = request.session.pop("next", "/")
        return RedirectResponse(next_url, status_code=303)
    else:
        _record_failure(ip)
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid username or password"},
        )


@router.post("/logout")
async def logout(request: Request):
    """Log out the current user."""
    request.session.clear()
    return RedirectResponse("/", status_code=303)
