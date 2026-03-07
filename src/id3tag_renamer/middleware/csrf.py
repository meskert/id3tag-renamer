"""CSRF protection middleware."""
from fastapi import Request, Response


async def csrf_middleware(request: Request, call_next):
    """
    Middleware to protect against CSRF for state-changing requests.

    Checks Origin and Referer headers for basic CSRF protection.
    """
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        # Check Origin and Referer for basic CSRF protection
        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")
        host = request.headers.get("Host")

        # In a real-world scenario with reverse proxy, we'd need to be more careful
        # about what the expected Origin/Referer is.
        # For now, we'll check if it's the same host if provided.
        if origin and host not in origin:
            return Response("CSRF Forbidden: Origin mismatch", status_code=403)
        elif not origin and referer and host not in referer:
            return Response("CSRF Forbidden: Referer mismatch", status_code=403)

    return await call_next(request)
