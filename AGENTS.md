# Agent Guidelines

<!--
  DELETE EACH COMMENT AS YOU FILL ITS SECTION IN, this one included. They do not
  render, but they are not invisible: an agent reads the raw text and pays for
  every line. A filled file is content only, never content plus scaffolding.

  Keep this file short. It is loaded into every agent's context on every task, so
  each line spends budget that could go to the guidelines that actually matter.
  30-150 lines. Models reliably follow only ~150-200 instructions and the agent's
  own system prompt already spends part of that budget, so a longer file does not
  buy more coverage -- it dilutes what gets followed. Anything longer belongs in
  README.md, docs/, or a skill.

  Add a line when an agent demonstrably gets something wrong. Remove it when the
  convention changes.
-->

## What this is

<!--
  Two or three sentences. What the project does and who uses it. Name the stack
  and the entry point, not the whole dependency list -- an agent can read
  package.json. Say what this project is NOT, if it is easy to confuse with a
  neighbouring repo or service.
-->

## Why it is built this way

<!--
  The decisions an agent would otherwise undo. Constraints that are not visible
  in the code: a vendor limit, a migration half-finished, a workaround for an
  upstream bug, a deliberate duplication. One line each, with the reason.

  Name the architecture instead of describing it: "hexagonal ports/adapters",
  "TDD -- test first, always", "event-driven, one handler per event". Explain it
  once in docs/Architecture.md and link there.
-->

## How to build, test, and verify

<!--
  The exact commands, in the order a change must pass them. Include what "done"
  looks like, and what is slow enough that an agent should not run it unasked
  (e2e suites, deploys, anything that costs money).
-->

```shell
# install
# build
# test
# lint / typecheck
```

## Rules

<!--
  Prefer rules a linter, type checker, or test could enforce. A rule an agent
  can check against is a rule that gets followed.

    good: "React components are function components; no class components."
    good: "Every exported function has a unit test in the sibling *.test.ts."
    good: "No `any`. Use `unknown` and narrow."
    bad:  "Write clean code."
    bad:  "Follow best practices."

  If a rule is already enforced by tooling, do not repeat it here -- point at
  the config instead. This section is for what the tooling cannot catch.
-->

- 

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
  Run `scripts/setup-agents.sh` — or `pwsh scripts/setup-agents.ps1` on Windows, which
  needs Developer Mode on — to recreate the links after a fresh clone.
