import json
import os
from functools import lru_cache
from pathlib import Path

from flask import Flask, url_for

MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent
    / "static"
    / "dist"
    / ".vite"
    / "manifest.json"
)


@lru_cache(maxsize=1)
def _load_manifest() -> dict:
    try:
        with MANIFEST_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}


def _resolve(rel_path: str) -> str:
    """Where a built file lives: STATIC_URL when set, else Flask's own static.

    STATIC_URL is an absolute URL in production -- a CloudFront distribution on
    a hostname of its own, answering /static/* from a bucket this application's
    pipeline synchronizes. Those files are therefore cross-origin with the pages
    that reference them, which is why the distribution answers CORS and why
    core/csp.py has to allow this host explicitly.

    A relative value still works and still means "same host", which is what a
    deployment serving its own assets would set. Empty means neither, which is
    what local and test runs get: Flask serves the build out of its own static
    directory.
    """
    static_url = os.environ.get("STATIC_URL", "").strip()
    if static_url:
        return static_url.rstrip("/") + "/" + rel_path
    return url_for("static", filename=f"dist/{rel_path}")


def asset_url(entry: str) -> str:
    """The built URL for a Vite entry, looked up by its manifest key."""
    manifest = _load_manifest()
    try:
        rel_path = manifest[entry]["file"]
    except KeyError:
        raise KeyError(
            f"No Vite manifest entry for {entry!r}; run `npm run build` in frontend/."
        ) from None

    return _resolve(rel_path)


def static_url(path: str) -> str:
    """The URL for a file Vite copies verbatim out of ``frontend/public/``.

    Those files never enter the manifest -- Vite copies them to the output root
    untouched and unhashed -- so ``asset_url`` cannot find them and would raise.
    They still land in the same place everything else does, which is why this
    shares ``_resolve``: the CDN when STATIC_URL is set, Flask's own static
    directory otherwise.

    Being unhashed is the trade. It buys a stable URL for the well-known files
    that need one, and it costs the ability to cache them forever -- see the
    Cache-Control split in .github/workflows/cd.yml.
    """
    return _resolve(path.lstrip("/"))


def init_assets(app: Flask) -> None:
    app.jinja_env.globals["asset_url"] = asset_url
    app.jinja_env.globals["static_url"] = static_url
