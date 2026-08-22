from __future__ import annotations

import os
from urllib.parse import urlsplit

from flask import Flask, Response

# Directives that can legitimately point at the asset CDN: today only CSS/JS
# are hosted there, but images, fonts, media, a web manifest, or a worker
# script could all end up on the same origin later without a CSP change.
_ASSET_DIRECTIVES = (
    "script-src",
    "style-src",
    "img-src",
    "font-src",
    "media-src",
    "connect-src",
    "manifest-src",
    "worker-src",
)


def _static_origin() -> str | None:
    static_url = os.environ.get("STATIC_URL", "").strip()
    if not static_url:
        return None
    parts = urlsplit(static_url)
    if not parts.scheme or not parts.netloc:
        return None
    return f"{parts.scheme}://{parts.netloc}"


def build_content_security_policy() -> str:
    origin = _static_origin()

    def directive(name: str) -> str:
        value = "'self'" if origin is None else f"'self' {origin}"
        return f"{name} {value}"

    return (
        "default-src 'self'; "
        f"{directive('script-src')}; "
        "script-src-attr 'none'; "
        f"{directive('style-src')}; "
        "style-src-attr 'none'; "
        f"{directive('img-src')}; "
        f"{directive('font-src')}; "
        f"{directive('media-src')}; "
        f"{directive('connect-src')}; "
        f"{directive('manifest-src')}; "
        f"{directive('worker-src')}; "
        "base-uri 'none'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "form-action 'self'"
    )


def init_csp(app: Flask) -> None:
    @app.after_request
    def add_content_security_policy(response: Response) -> Response:
        response.headers["Content-Security-Policy"] = build_content_security_policy()
        return response
