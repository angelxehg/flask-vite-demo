from __future__ import annotations

from flask import Flask, Response, request

# How long CloudFront and a browser may serve the index without asking again.
# An hour is the trade this application accepts: the CD role holds no
# cloudfront:CreateInvalidation, so a deploy is invisible for up to this long.
# It does not break -- asset filenames are content-hashed and the sync does not
# delete, so a stale index keeps referring to files that are still there.
INDEX_MAX_AGE = 3600

# Endpoints whose responses are worth caching at the edge, by name rather than by
# path so a renamed route fails loudly instead of silently going uncached.
# Deliberately just the one: /about and /contact are as static as the index
# today, and the moment either stops being so, the cost of having assumed
# otherwise is a stale page nobody can invalidate. Adding one here is a line, and
# it should be a decision.
CACHEABLE_ENDPOINTS = frozenset({"home"})


def cache_control_for(endpoint: str | None, method: str, status_code: int) -> str:
    """What to tell the edge about one response.

    Only a plain successful GET is cacheable. A POST response, a redirect and an
    error page are all `no-store`, which is the safe default rather than a
    considered one: nothing here is per-user yet, and the day something is, the
    mistake this avoids is the expensive one.
    """
    if method == "GET" and status_code == 200 and endpoint in CACHEABLE_ENDPOINTS:
        return f"public, max-age={INDEX_MAX_AGE}"
    return "no-store"


def init_cache(app: Flask) -> None:
    """Attach a Cache-Control header to every response.

    Every response, including the ones Flask generates itself, because the
    distribution in front of this application is configured to let the origin
    decide: its cache policy has a zero default TTL and a non-zero ceiling, so a
    response arriving without a Cache-Control is not cached at all. That makes
    silence safe but also makes it invisible -- nothing would report that the
    index stopped being cached. Saying it explicitly on every response is what
    makes the intent readable from a single `curl -I`.

    Static files are not covered here. They never reach this application: the
    distribution routes /static/* to a bucket, and their Cache-Control is set at
    upload time by .github/workflows/cd.yml.
    """

    @app.after_request
    def add_cache_control(response: Response) -> Response:
        response.headers["Cache-Control"] = cache_control_for(
            request.endpoint, request.method, response.status_code
        )
        return response
