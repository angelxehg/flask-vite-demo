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


def asset_url(entry: str) -> str:
    manifest = _load_manifest()
    try:
        rel_path = manifest[entry]["file"]
    except KeyError:
        raise KeyError(
            f"No Vite manifest entry for {entry!r}; run `npm run build` in frontend/."
        ) from None

    static_url = os.environ.get("STATIC_URL", "").strip()
    if static_url:
        return static_url.rstrip("/") + "/" + rel_path
    return url_for("static", filename=f"dist/{rel_path}")


def init_assets(app: Flask) -> None:
    app.jinja_env.globals["asset_url"] = asset_url
