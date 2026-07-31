# The AGENTS.md fragment — transcribe, do not improvise

`/orca:adopt` appends the block below to a consuming project's `AGENTS.md` or
`CLAUDE.md`. A plugin cannot write a project's always-loaded context, so this is
the one-time manual step that makes the tracking model stick.

> **A sibling copy lives in `supacode-skills`** at
> `plugins/supacode/skills/_shared/agents-fragment.md`. The fenced block is
> app-agnostic and should stay identical in substance across both; the surrounding
> prose differs only in which skill does the appending. Claude Code plugins have no
> dependency mechanism, so each plugin must be self-contained to install
> standalone. **A fix to the fenced rules belongs in both copies.**
>
> This copy carries two rules the sibling does not yet have — the issue-body
> schema and the generated-roadmap line. Both are app-agnostic and would be
> improvements there too.

**Copy the fenced block verbatim.** These rules are what stop lanes from
re-creating the tracked-progress-file problem, and a paraphrase drifts. Append
under a `## Task tracking` heading; if one already exists, reconcile rather than
duplicating.

Write it to whichever file the project actually has. If both exist, prefer the
one already carrying contributor instructions. If neither exists, create
`AGENTS.md` — and make sure anything referring to it (such as a gutted roadmap
stub) names the file you actually wrote.

```markdown
## Task tracking

- Task state lives in GitHub Issues. No tracked file records progress, status,
  or completion.
- Never edit a roadmap, status board, or TODO file to record progress.
- Every PR body includes `Closes #<n>`. Never close an issue by hand — if a
  merge did not close its issue, the PR body was malformed; report that.
- Progress notes go in issue comments, not files.
- Design and rationale go in `docs/specs/<slug>.md`. Issue bodies link to the
  spec; they do not restate it.
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
"mark the chunk complete in the status board" — and **delete or rewrite them**.

Leaving them is the most common way a migration reverts: the tracked file becomes
a stub, the instruction survives, and the next session helpfully refills it.
