---
name: wave
description: Plan several issues at once, each in its own terminal in the current worktree, so you can move between them answering their questions instead of planning one at a time. Takes a list of issue numbers (or offers the active milestone's ready ones), starts a planning context per issue titled with its number, waits for you to work through them, then reviews the finished plans against each other for file collisions before anything is launched. Stops there - launching the survivors as lanes is a second, deliberate step. Use when the user says "/orca:wave", "/orca:wave 84 85 86", "plan these all at once", "plan a wave", "start planning several issues", "I want to plan these in parallel", or asks to work through the ready list together. This plans in parallel; it does not create worktrees - each planning context shares the current checkout, and only /orca:launch creates a lane. For planning a single issue, use /orca:plan directly.
---

# Wave

Plan several issues **concurrently**, one terminal each, then check the finished
plans against each other before any work starts.

The value is not just speed. Two issues that are independently ready can still
edit the same file — `/orca:status` cannot see that, because it only knows
dependency edges. **Comparing finished plans is the only place a file collision
is detectable before launch**, and that check is why this skill stops rather than
launching automatically.

## What this skill is not for

- **Planning one issue** ⇒ `/orca:plan`. This is the fan-out wrapper.
- **Creating worktrees** ⇒ it deliberately does not. Planning writes no repo
  files, so every context shares the current checkout — which is what Orca's
  bundled `orchestration` skill prescribes ("parallelism is not an isolation
  requirement"). Only `/orca:launch` creates a worktree.
- **Supervising the planning agents** ⇒ this skill starts them and reports. It
  does not poll them, wait on them, or coordinate a DAG; that is
  `orchestration`'s job.

## 0. Preconditions

```bash
command -v orca && orca status --json      # result.runtime.reachable
gh auth status
orca worktree current --json               # the worktree every context shares
```

Orca unreachable ⇒ **stop.** There is nowhere to put the contexts. Say that
`/orca:plan` still works for one issue at a time.

## 1. Choose the issues

`$ARGUMENTS` may be issue numbers (`84 85 86`), or empty.

**Empty** ⇒ resolve the active milestone's ready issues per
`../_shared/github-backlog.md`, then **present them and ask which to plan.**
Never fan out over a whole milestone unasked — each context costs tokens and
attention.

Exclude, and say why:

- **Already in flight** — an open PR, an assignee, or a live lane
  (`orca worktree ps --json`, `linkedIssue`).
- **Blocked** — any blocker still `OPEN` in `blockedBy.nodes[].state`.
- **`manual`** — no agent can do it, so a plan is wasted
  (`../_shared/issue-schema.md`).
- **No `### Done when` checklist** — plannable, but say so: the plan will have to
  establish criteria, and `/orca:triage` is the cheaper place to do that.

**Cap the wave at ~4.** Past that you cannot realistically hold four planning
conversations, and the contexts sit idle waiting on you. Offer the rest as a
second wave.

Confirm before starting anything:

```
Plan these 4 in parallel? Each gets its own terminal in this worktree.

  #84  E1 · Balance tuning pass        game balance
  #85  G2 · Board-window overlay fixes board ui
  #86  T2 · Event instrumentation      analytics
  #87  K1 · CloudSyncService           cloud sync

You'll answer each context's questions as they come up.
```

## 2. Start one planning context per issue

For each issue, in **one message** so they start together:

```bash
orca terminal create --worktree <selector> \
  --title "plan #<n>" \
  --command "claude" --json
```

Read `result.terminal.handle` from each. Then, per context, **wait for the TUI
to be ready before sending anything** — a prompt sent into a booting TUI is
lost:

```bash
orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json
orca terminal send --terminal <handle> \
  --text "/orca:plan <n>" --enter --json
```

Notes that matter:

- **`--title "plan #<n>"`** is how you tell the tabs apart. Without it they are
  indistinguishable and the whole flow falls apart.
- **Terminal handles are routing metadata** — do not cache them across
  operations; re-resolve with `orca terminal list --worktree <selector> --json`
  (`../_shared/orca-lanes.md`).
- **Send `/orca:plan <n>`, not a paraphrase.** Each context runs the real
  planning skill, including its adversarial review.
- A context that fails to start is reported and skipped; the others continue.

## 3. Hand control back — the contexts are interactive

**Tell the user the wave is running and stop.** Each context will ask its own
questions and wait; they are meant to be visited, not supervised from here.

Report the tab titles and issue numbers so they can be found:

```
4 planning contexts started, one tab each:

  plan #84   plan #85   plan #86   plan #87

Visit each tab and answer its questions. When they are all done, run
/orca:wave --review to check the plans against each other.
```

**Do not poll the terminals, read their output, or wait on them.** They are
talking to the user, not to you. Reading their output to "check progress" both
wastes context and risks acting on a half-finished plan.

## 4. `--review` — check the finished plans against each other

Run when the user says the plans are done.

Collect each plan. `/orca:plan` writes to `~/.claude/plans/<repo-name>/`, so read
the files for the issues in this wave; if a plan is missing, say which and treat
that issue as not ready.

Then check **every pair** for real overlap:

- **The same file modified by both.** The core check. Read each plan's Steps for
  named files and symbols.
- **The same subsystem or shared type**, even where the files differ — two plans
  changing one type's shape will conflict at merge even in separate files.
- **The same test baseline or fixture.**
- **An ordering the plans assume differently** — both assuming they land first.

**Repo-mandated shared files do not count.** A changelog or checklist every PR
touches is expected, and lanes resolve it at push time. Flag genuine
architectural overlap, not the file everyone edits by construction.

Report:

```
3 of 4 ready to launch.

  #84  ready
  #87  ready
  #85  ready
  #86  COLLIDES with #85 — both modify GameScene.swift and the
       overlay layout constants. Launch one, then re-plan the other
       against the merged result.
```

A collision is **not** a verdict that one plan is wrong. The usual resolution is
sequencing: launch one, let it merge, re-plan the other. Say that rather than
asking the user to pick a winner.

## 5. `--launch` — start the survivors

Only after §4, and only for plans with no unresolved collision. For each, invoke
the `orca:launch` skill via the Skill tool with that issue number.

**Launch them one at a time, checking each result** — a failed launch (a
`kind: folder` repo, a name collision, an issue that went in-flight since §1)
must not silently take the rest of the wave with it. Report per issue: launched
with its branch, or skipped with the reason.

Never launch an issue that collided, unless the user explicitly overrides after
being told what the overlap is.

## Failure modes to avoid

- **Fanning out over a whole milestone unasked.** Present and confirm; cap at ~4.
- **Creating worktrees for planning.** Planning writes no repo files; contexts
  share the checkout.
- **Polling the planning contexts.** They are interactive with the user, not
  with you.
- **Launching automatically after planning.** The cross-plan review exists
  precisely so a human sees the plans together first.
- **Treating a repo-mandated shared file as a collision.** Every lane touches
  the changelog; that is handled at push time.
- **Reporting a collision as "one of these plans is wrong."** It is usually a
  sequencing problem.
- **Letting one failed launch abort the wave.**
