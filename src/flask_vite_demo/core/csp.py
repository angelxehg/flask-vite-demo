from __future__ import annotations

import os
from urllib.parse import urlsplit

from flask import Flask, Response


def _static_source() -> str | None:
    static_url = os.environ.get("STATIC_URL", "").strip()
    if not static_url:
        return None
    parts = urlsplit(static_url)
    if not parts.scheme or not parts.netloc:
        return None
    # Keep the path (e.g. /flask-vite-demo/prod/) rather than trimming to the
    # bare origin: static.angelxehg.com is a shared CDN for multiple apps'
    # prefixes, and a trailing "/" makes CSP match it and anything beneath it,
    # not the whole origin.
    path = parts.path if parts.path.endswith("/") else parts.path + "/"
    return f"{parts.scheme}://{parts.netloc}{path}"


def build_content_security_policy() -> str:
    source = _static_source()

    def directive(name: str) -> str:
        value = "'self'" if source is None else f"'self' {source}"
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
