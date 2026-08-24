#!/bin/sh
# Point each agent at the single AGENTS.md and skills/ in this repo.
#
# Codex reads a root AGENTS.md on its own, so only its skills directory is linked.
# Claude and Junie each want the guidelines under their own name.
# Idempotent: re-run after a fresh clone, or after adding an agent below.
set -eu

cd "$(dirname "$0")/.."

link() { # link <target-relative-to-link-dir> <link-path>
	target=$1
	path=$2
	dir=$(dirname "$path")
	if [ -e "$path" ] && [ ! -L "$path" ]; then
		echo "skip $path (real file, not a symlink -- remove it first)" >&2
		return 0
	fi
	mkdir -p "$dir"
	ln -sfn "$target" "$path"
	echo "  $path -> $target"
}

echo "linking agent config:"
link AGENTS.md      CLAUDE.md                 # Claude Code
link ../skills      .claude/skills
link ../skills      .codex/skills             # Codex (reads ./AGENTS.md natively)
link ../AGENTS.md   .junie/guidelines.md      # Junie
link ../skills      .junie/skills
