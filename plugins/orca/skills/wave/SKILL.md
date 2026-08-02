---
name: wave
description: Plan several issues at once, each in its own terminal in the current worktree, so you can move between them answering their questions instead of planning one at a time. Takes a list of issue numbers (or offers the active milestone's ready ones), starts a planning context per issue in its own tab, titled with the issue number and a two-word topic so you can tell them apart at a glance, waits for you to work through them, then reviews the finished plans against each other for file collisions before anything is launched. Stops there - launching the survivors as lanes is a second, deliberate step. Use when the user says "/orca:wave", "/orca:wave 84 85 86", "plan these all at once", "plan a wave", "start planning several issues", "I want to plan these in parallel", or asks to work through the ready list together. Also owns the second half of the wave: "check these plans against each other", "do these plans conflict", "will these collide", "are these safe to run in parallel" (--review, which takes the same issue numbers and skips any that already have a lane), and "launch the ones that do not collide", "start the surviving plans", "launch the wave" (--launch). This plans in parallel; it does not create worktrees - each planning context shares the current checkout, and only /orca:launch creates a lane. For planning a single issue, use /orca:plan directly.
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

- **Already in flight** — an open PR, an assignee, or a live lane. `worktree ps`
  spans **all repos** and has no `--repo` flag, so filter on `repoId` +
  `linkedIssue` + `isMainWorktree == false`; `linkedIssue` alone matches
  unrelated repos (`../_shared/orca-lanes.md`).
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
  --title "#<n> <2-3 word topic>" \
  --command "claude" --json
```

**The title is how you tell the tabs apart**, so it carries a short topic as well
as the number — a tab bar is scanned, not read:

| Issue title | Tab title |
|---|---|
| `E1 · Balance tuning pass` | `#84 balance tuning` |
| `G2 · Board-window overlay fixes: marker tray + weapon plate` | `#85 overlay fixes` |
| `K1 · CloudSyncService + meta/archive sync` | `#87 cloud sync` |

Rules for deriving it:

- **Two or three words, ~20 characters total.** Tabs truncate, and a title that
  clips mid-word is worse than a short one — the number must always survive.
- **Take the distinctive words**, not the first ones. Drop a leading task id
  (`E1 ·`), and drop anything after a colon or dash — that is usually the
  qualifier, not the subject.
- **Reuse the scope label when it fits** (`cloud sync`, `board ui`) — it is
  already the short name for that area of the system.
- Lowercase reads better at tab size than title case.

Read `result.terminal.handle` from each. Then, per context, **wait for the TUI
to be ready before sending anything** — a prompt sent into a booting TUI is
lost:

```bash
orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json
orca terminal send --terminal <handle> \
  --text "/orca:plan <n>" --enter --json
```

Notes that matter:

- **The title is not optional.** Untitled tabs are indistinguishable and the
  whole flow falls apart — you cannot answer four contexts you cannot tell
  apart.
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

  #84 balance tuning   #85 overlay fixes   #86 instrumentation   #87 cloud sync

Visit each tab and answer its questions. When they are all done, run
/orca:wave --review 84 85 86 87 to check the plans against each other.
```

**Include the issue numbers in that instruction.** The plans directory
accumulates across waves, and a bare `--review` in a fresh context has to guess
which plans belong to this one (§4).

**Do not poll the terminals, read their output, or wait on them.** They are
talking to the user, not to you. Reading their output to "check progress" both
wastes context and risks acting on a half-finished plan.

## 4. `--review` — check the finished plans against each other

Run when the user says the plans are done.

### Which plans belong to this wave

`/orca:plan` writes to `~/.claude/plans/<repo-name>/`, and **that directory
accumulates every plan ever written for the repo** — including ones that already
became lanes, and ones from waves weeks ago. A fresh context has no memory of
which issues *this* wave planned, so reading the directory is not the same as
reading the wave.

Scope it, in this order:

1. **Issue numbers in `$ARGUMENTS`** — `/orca:wave --review 84 85 86 87`. The
   unambiguous form; prefer it and say so when the user omits them.
2. **The wave started in this conversation**, if there was one.
3. **Otherwise, infer and confirm.** Take the most recent plan files, exclude
   anything already in flight (below), present what you propose to review, and
   **ask before proceeding**. Never silently adopt every plan on disk.

### Exclude plans that already became lanes — always

**Before reviewing anything, drop plans whose work is already running.** This is
the step that stops a second wave re-proposing the first wave's issues:

```bash
orca worktree ps --limit 200 --json      # spans all repos — filter on repoId
gh pr list --state open --json number,headRefName,closingIssuesReferences
```

A plan is **not** a candidate when its issue has a live lane (`linkedIssue`
matching, `isMainWorktree == false`, same `repoId`), an open PR, or an assignee.
Say which plans were excluded and why — *"#84–#87 already have lanes; reviewing
the remaining 3"* — rather than dropping them silently, so the user can tell the
difference between "excluded" and "never found".

**Nothing left after exclusion** ⇒ say that plainly: every plan on disk is
already in flight, and there is nothing to review. That is a normal outcome
between waves, not an error.

If a plan is missing for an issue that *is* in scope, say which and treat that
issue as not ready.

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

**Re-check in-flight immediately before each launch**, not once at the top. §4's
exclusion may be minutes old, and in that time another wave, another session, or
the user by hand could have started a lane on the same issue. Skip anything that
gained a lane, PR, or assignee since — and say so, rather than launching a second
agent onto work already running.

`/orca:launch` refuses in-flight work itself, so this is a second net rather than
the only one. Two nets are right here: a duplicate lane means two agents opening
two competing PRs for one issue, which is expensive to notice and annoying to
unpick.

**Launch them one at a time, checking each result** — a failed launch (a
`kind: folder` repo, a name collision, an issue that went in-flight since §1)
must not silently take the rest of the wave with it. Report per issue: launched
with its branch, or skipped with the reason.

Never launch an issue that collided, unless the user explicitly overrides after
being told what the overlap is.

## Failure modes to avoid

- **Treating every plan on disk as this wave's.** The plans directory accumulates
  across every wave the repo has ever run. Scope by issue number, and always
  exclude work that already has a lane — otherwise a second wave re-proposes the
  first wave's issues, which is the most likely way this skill wastes a run.
- **Checking in-flight once, at the top.** Re-check immediately before each
  launch; a lane can appear in the minutes between.
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
