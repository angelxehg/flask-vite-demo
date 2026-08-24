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
    # Only reached when STATIC_URL names another host. In production it does not:
    # assets are served from this application's own hostname under /static/, so
    # STATIC_URL is the relative "/static", urlsplit finds no scheme and no
    # netloc, and the policy stays 'self' -- which already covers same-origin
    # requests. There is no CDN source to allow because there is no CDN origin.
    #
    # The absolute form still works, because a deployment that does put assets on
    # a separate host is a configuration change rather than a code change. Keep
    # the path (e.g. /flask-vite-demo/prod/) rather than trimming to the bare
    # origin: a shared asset host serves several applications' prefixes, and a
    # trailing "/" makes CSP match that prefix and anything beneath it rather
    # than the whole origin.
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
