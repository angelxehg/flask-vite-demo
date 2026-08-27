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
    # Reached whenever STATIC_URL names another host, which in production it
    # does: assets are served by a CloudFront distribution on a hostname of its
    # own, so STATIC_URL is an absolute URL and this source is what makes the
    # bundle loadable at all. A policy of 'self' alone would block every script
    # and stylesheet the page references.
    #
    # Local and test runs pass no STATIC_URL, or a relative one, and fall through
    # to None above -- 'self' is right there, because Flask serves the build out
    # of its own static directory.
    #
    # Keep the path (e.g. /static/) rather than trimming to the bare origin: the
    # same host also answers /media/, and a trailing "/" makes CSP match one
    # prefix and anything beneath it rather than the whole origin.
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
