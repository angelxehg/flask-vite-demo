# Agent Guidelines

## What this is

Flask + Vite integration demo: a Python 3.14 Flask app (`src/flask_vite_demo/`)
serving server-rendered Jinja templates, styled and scripted by a Vite-built
frontend (`frontend/`). The two are wired together at runtime, not build time —
`core/assets.py` reads Vite's `manifest.json` to resolve hashed asset URLs. Ships
as a single Docker image (`Dockerfile`), deployed behind CloudFront/S3 in
production. It's a demo/reference project, not a framework — there's no plugin
surface or public API to preserve compatibility for.

## Stack overview

- Language: Python >=3.14 (backend), JavaScript (frontend, Vite-built)
- Package manager: uv (Python), npm (frontend)
- Framework(s): Flask 3.1, Vite 6
- Key dependencies: gunicorn (WSGI server); black, ruff, pytest (Python dev group)
- Entry point: `flask_vite_demo:main` (`src/flask_vite_demo/__init__.py`)

## Why it is built this way

- **Asset resolution is manifest-driven, not path-guessed.** `asset_url()` looks
  up the built filename in Vite's `manifest.json` at request time, so hashed
  filenames never need to be hardcoded. Files under `frontend/public/` bypass the
  manifest entirely (Vite copies them verbatim) — use `static_url()` for those.
- **`STATIC_URL` switches where assets are served from, and CSP follows it.**
  Empty (local/test): Flask serves its own `static/dist`. A relative path (prod,
  e.g. `/static`): same-origin, so CSP stays `'self'`-only. An absolute URL
  (alternate CDN host): CSP grows exactly that origin+prefix, never a wildcard.
  See `core/assets.py` and `core/csp.py`.
- **Cache-Control is an explicit per-endpoint allowlist, not a header default.**
  `core/cache.py`'s `CACHEABLE_ENDPOINTS` keys by endpoint *name*, not path, so a
  renamed route silently drops out of the cache instead of silently staying in
  it. Only `home` is cacheable today — the CD pipeline's IAM role holds no
  `cloudfront:CreateInvalidation`, so a bad cached response can't be flushed and
  has to age out on its own. HEAD must return the same `Cache-Control` as GET,
  because CloudFront caches both.
- **Hashed vs. unhashed assets get different cache lifetimes at deploy time.**
  `.github/workflows/cd.yml` syncs `assets/` (content-hashed) as
  `immutable, max-age=31536000` and everything else (including the index HTML)
  as `max-age=3600`. A file only gets the long lifetime if Vite hashes it — see
  `docs/Architecture.md`.
- **Docker builds the frontend once, natively, regardless of target platform** —
  JS/CSS output isn't architecture-specific, so a multi-arch image build doesn't
  redo it per arch. A separate `FROM scratch AS assets` stage exists solely so CI
  can extract just the built files for the S3 sync, without touching the shipped
  image.

## How to build, test, and verify

Mirrors `.github/workflows/checks.yml`, in the order a change must pass:

```shell
# frontend: install + build (required before Flask can serve real assets —
# asset_url() raises KeyError against a missing/stale manifest)
cd frontend && npm ci && npm run build

# python: install (matches CI; drop --locked to let uv update the lock)
uv sync --group dev --locked

# lint (also: make lint)
uv run black --check .
uv run ruff check .

# test (also: make test)
uv run pytest
```

`make format` applies `black` and `ruff --fix` in place. There is no
typecheck/mypy step configured — don't invent one.

## Rules

- `frontend/` is excluded from `black`/`ruff` (`pyproject.toml`
  `extend-exclude`) — it has its own toolchain and no linter configured yet.
  Don't run the Python formatters against it or add one uninvited.
- Python source lives under `src/flask_vite_demo/`; tests under `tests/`
  (`pyproject.toml` `testpaths = ["tests"]`).
- A new cacheable route needs an explicit addition to `CACHEABLE_ENDPOINTS` in
  `src/flask_vite_demo/core/cache.py` — nothing is cacheable by default, and
  that's deliberate (see Why above).
- A new file under `frontend/public/` is served unhashed with only a 1-hour
  cache lifetime. If it needs to change atomically or cache forever, it belongs
  as a Vite-bundled asset (imported from `frontend/src/`) instead.

## Reference documents

Read these when the task touches them, and keep them current as part of the change:

- `docs/Architecture.md` — current and target architecture. Read before adding a
  module, a boundary, or a dependency. Curated, unlike the two below: record only the
  change you actually made, under **Current**. Never rewrite **Target** freely — it is
  aspirational on purpose and reasoned by humans; propose edits to it as a diff for
  review.
- `docs/Roadmap.md` — planned work, as checklists. Tick items off when you finish them.
- `docs/Incidents.md` — failures that are still live, and how each was solved or
  worked around. Read before debugging something that smells familiar. Add an entry
  when you hit a new one.

## Maintaining this file

- **Do not edit `AGENTS.md` on your own.** It is maintained by humans. If your change
  makes a guideline here untrue, say so and ask before touching it, then land the edit
  as a separate commit at the end. Two reasons: a file the agent rewrites mid-task
  drifts from reviewed convention into whatever the last session happened to think,
  and this file is baked into the cached prompt prefix -- leaving it changed at the
  end of a session buys the next one a cold cache, for an edit nobody reviewed.
- `CLAUDE.md` and `.junie/guidelines.md` are **symlinks to this file**, and
  `.claude/skills`, `.codex/skills`, and `.junie/skills` are symlinks to `skills/`.
  Edit `AGENTS.md` and `skills/` only. Never replace a symlink with a real file, and
  never write the same guidance into two of these paths -- it is one file.
  Run `uv run scripts/setup-agents.py` to recreate the links after a fresh clone —
  on Windows this needs Developer Mode on (Settings > System > For developers).
