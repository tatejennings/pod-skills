# The AGENTS.md fragment — transcribe, do not improvise

`/orca:migrate` appends the block below to a consuming project's `AGENTS.md` or
`CLAUDE.md`. A plugin cannot write a project's always-loaded context, so this is
the manual step that makes the tracking model stick.

> **The fenced block is app-agnostic** — it describes the tracking model only,
> and mentions no specific tool or project. Claude Code plugins have no
> dependency mechanism, so each plugin carries its own copy rather than
> referencing a shared one; if you maintain such a copy elsewhere, a fix to the
> fenced rules belongs there too.

**Copy the fenced block verbatim.** These rules are what stop lanes from
re-creating the tracked-progress-file problem, and a paraphrase drifts. Append
under a `## Task tracking` heading; if one already exists, reconcile rather than
duplicating.

Write it to whichever file the project actually has. If both exist, prefer the
one already carrying contributor instructions. If neither exists, create
`AGENTS.md` — and make sure anything referring to it (such as a gutted roadmap
stub) names the file you actually wrote.

The `<!-- orca-skills tracking model vN -->` line is **not decoration.**
`/orca:migrate` reads it on every later run to tell a repo migrated under an
older schema from one already current. Drop it and the next run cannot
distinguish the two.

```markdown
## Task tracking
<!-- orca-skills tracking model v1 -->

- Task state lives in GitHub Issues. No tracked file records progress, status,
  or completion.
- Never edit a roadmap, status board, or TODO file to record progress.
- Every PR body includes `Closes #<n>`. Never close an issue by hand — if a
  merge did not close its issue, the PR body was malformed; report that.
- Progress notes go in issue comments, not files.
- Design and rationale go in `docs/specs/<slug>.md`. Issue bodies link to the
  spec; they do not restate it. A planning doc is the plan, never a status
  board — it changes when a decision changes, not when work progresses.
- Blocking is a real dependency, not a label or a prose line:
  `gh issue edit <blocked> --add-blocked-by <blocker>`. That edge is what
  readiness reads; a label mirrors it and can go stale.
- An issue with **no milestone** is the unscheduled backlog. Assigning a
  milestone is what scheduling means.
- Every issue carries a `### Done when` checklist of acceptance criteria —
  that checklist is what gates the work, and it is written when the issue is
  filed, not after the work is done.
- `ROADMAP.md` is generated from GitHub state and gitignored. Never edit it by
  hand and never commit it; regenerate it instead.
- Session-local planning scratch goes in a gitignored path.
- Confirm the active account with `gh auth status` before any `gh` write.
```

That last line is not boilerplate. `gh` can hold several authenticated accounts
with only one active, and the active one is whichever was selected last —
frequently the wrong one for a personal project. Check before writes, not after.

## Also remove the instructions that caused the problem

Appending these rules is only half the job. Search the project's existing
`CLAUDE.md`/`AGENTS.md` for instructions telling contributors to update a
roadmap, status board, or progress file — e.g. "always update `ROADMAP.md`",
"mark the task complete in the status board" — and **delete or rewrite them**.

Leaving them is the most common way a migration reverts: the tracked file becomes
a stub, the instruction survives, and the next session helpfully refills it.
