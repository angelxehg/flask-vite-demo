#!/usr/bin/env python3
"""Point each agent at the single AGENTS.md and skills/ in this repo.

Codex reads a root AGENTS.md on its own, so only its skills directory is linked.
Claude and Junie each want the guidelines under their own name.
Idempotent: re-run after a fresh clone, or after adding an agent below.

Vendored for Python-based repos: one interpreter (uv, conda, pyenv, or system
python) replaces the separate POSIX and PowerShell scripts. Requires Python >=
3.8, standard library only -- no external deps.

Windows needs permission to create symlinks. Either turn on Settings > System >
For developers > Developer Mode (once, no admin needed afterwards), or run this
from an elevated shell. Without one of those, os.symlink() fails and this
script says so instead of raising a raw PermissionError.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def link(target: str, path: str) -> None:
    """Symlink ROOT/path -> target (target is relative to path's own directory)."""
    dest = ROOT / path

    if dest.is_symlink():
        dest.unlink()
    elif dest.exists():
        print(
            f"skip {path} (real file, not a symlink -- remove it first)",
            file=sys.stderr,
        )
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    is_dir = (dest.parent / target).resolve().is_dir()

    try:
        os.symlink(target, dest, target_is_directory=is_dir)
    except OSError as exc:
        if os.name == "nt":
            sys.exit(
                f"cannot create symlink {path} -> {target}\n"
                "  Turn on Developer Mode (Settings > System > For developers),"
                " or run this from an elevated shell.\n"
                f"  {exc}"
            )
        raise

    print(f"  {path} -> {target}")


def main() -> None:
    print("linking agent config:")
    link("AGENTS.md", "CLAUDE.md")  # Claude Code
    link("../skills", ".claude/skills")
    link("../skills", ".codex/skills")  # Codex (reads ./AGENTS.md natively)
    link("../AGENTS.md", ".junie/guidelines.md")  # Junie
    link("../skills", ".junie/skills")


if __name__ == "__main__":
    main()
