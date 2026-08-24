#!/usr/bin/env pwsh
# Point each agent at the single AGENTS.md and skills/ in this repo.
#
# Windows counterpart of setup-agents.sh. Keep the two link lists in sync.
#
# Codex reads a root AGENTS.md on its own, so only its skills directory is linked.
# Claude and Junie each want the guidelines under their own name.
# Idempotent: re-run after a fresh clone, or after adding an agent below.
#
# Windows needs permission to create symlinks. Either turn on
# Settings > System > For developers > Developer Mode (once, no admin needed
# afterwards), or run this in an elevated shell. Without one of those,
# New-Item -ItemType SymbolicLink fails and this script says so.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Set-Location (Join-Path $PSScriptRoot '..')

function Link {
	# Link <target-relative-to-link-dir> <link-path>
	param([string]$Target, [string]$Path)

	$dir  = Split-Path -Parent $Path
	$name = Split-Path -Leaf   $Path

	$existing = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
	if ($existing -and -not ($existing.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
		Write-Warning "skip $Path (real file, not a symlink -- remove it first)"
		return
	}

	if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

	# Create from inside the link's own directory, so a relative target is stored
	# and resolved the same way ln -s does it.
	Push-Location $dir
	try {
		# .Delete() drops the reparse point only. Remove-Item -Recurse on a
		# directory symlink has historically deleted the TARGET's contents --
		# that would empty skills/.
		$link = Get-Item -LiteralPath $name -Force -ErrorAction SilentlyContinue
		if ($link) { $link.Delete() }

		try {
			New-Item -ItemType SymbolicLink -Path $name -Target $Target -Force | Out-Null
		} catch {
			throw ("cannot create symlink $Path -> $Target`n" +
			       "  Turn on Developer Mode (Settings > System > For developers)," +
			       " or run this in an elevated shell.`n  $($_.Exception.Message)")
		}
		Write-Host "  $Path -> $Target"
	} finally {
		Pop-Location
	}
}

Write-Host 'linking agent config:'
Link 'AGENTS.md'    'CLAUDE.md'               # Claude Code
Link '../skills'    '.claude/skills'
Link '../skills'    '.codex/skills'           # Codex (reads ./AGENTS.md natively)
Link '../AGENTS.md' '.junie/guidelines.md'    # Junie
Link '../skills'    '.junie/skills'
