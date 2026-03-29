"""CSRF protection middleware."""
from urllib.parse import urlparse
from fastapi import Request, Response


def _hosts_match(host: str, url: str) -> bool:
    """Return True if the netloc of url exactly matches host (ignoring port on both sides)."""
    parsed = urlparse(url)
    # netloc may include port (e.g. "example.com:8080"); compare bare hostnames
    netloc_host = parsed.netloc.split(":")[0]
    bare_host = host.split(":")[0]
    return netloc_host == bare_host


async def csrf_middleware(request: Request, call_next):
    """
    Middleware to protect against CSRF for state-changing requests.

    Checks Origin and Referer headers for basic CSRF protection.
    Requests with neither header are blocked to prevent CSRF via
    tools or proxies that strip headers.
    The /login endpoint is exempt so the login form itself can POST.
    """
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        # Login endpoint is exempt — it has no session yet to protect
        if request.url.path == "/login":
            return await call_next(request)

        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")
        host = request.headers.get("Host", "")

        if origin:
            if not _hosts_match(host, origin):
                return Response("CSRF Forbidden: Origin mismatch", status_code=403)
        elif referer:
            if not _hosts_match(host, referer):
                return Response("CSRF Forbidden: Referer mismatch", status_code=403)
        else:
            # Neither header present — block to prevent header-stripping bypass
            return Response("CSRF Forbidden: missing Origin/Referer", status_code=403)

    return await call_next(request)
