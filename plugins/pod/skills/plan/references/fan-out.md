# Planning several issues at once

`../SKILL.md` §0 sends you here when `$ARGUMENTS` names more than one issue.
**This context plans nothing itself**: it starts one planning terminal per
issue, each running `/pod:plan <n>` for a single issue, and hands control back.

No worktrees are created. Planning writes no repo files, so every context
shares the current checkout; only `/pod:launch` creates a lane.

Two issues that are independently ready can still edit the same file, and only
comparing finished plans shows it. That check belongs to `/pod:launch` given
several issues — which is why this stops rather than launching.

## 1. Preconditions

```bash
command -v orca && orca status --json      # result.runtime.reachable
gh auth status
orca worktree current --json               # the worktree every context shares
```

Orca unreachable ⇒ **stop.** There is nowhere to put the contexts. Offer to
plan the issues one at a time in this context instead.

## 2. Choose the issues

The issue numbers from `$ARGUMENTS`. **The user asked for "the ready ones" or
"a wave" without numbers** ⇒ resolve the active milestone's ready issues per
`../../_shared/github-backlog.md`, then **present them and ask which to plan.**
Never fan out over a whole milestone unasked — each context costs tokens and
attention.

Exclude, and say why:

- **Already in flight** — an open PR, an assignee, or a live lane. `worktree ps`
  spans **all repos** and has no `--repo` flag, so filter on `repoId` +
  `linkedIssue` + `isMainWorktree == false`; `linkedIssue` alone matches
  unrelated repos (`../../_shared/orca-lanes.md`).
- **Blocked** — any blocker still `OPEN` in `blockedBy.nodes[].state`.
- **`manual`** — no agent can do it, so a plan is wasted
  (`../../_shared/issue-schema.md`).
- **No `### Acceptance criteria` checklist** — plannable, but say so: the plan will have to
  establish criteria, and `/pod:triage` is the cheaper place to do that.

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

Under `--auto`, say instead: *"Each plans on its own; only ones hitting a real
fork will wait for you."*

## 2a. `--auto` — plan unattended, stop only on a real question

By default every context waits for you, including the ones with nothing to ask.
`--auto` removes that cost: each context plans on its own and **only stops if a
genuine fork comes up.**

```bash
/pod:plan 84 85 86 87 --auto
```

Nothing pre-filters which issues are eligible — **the plan decides**. An issue
with an obvious fix plans clean; one with a real trade-off stops and asks,
regardless of its size or labels.

Send `/pod:plan <n> --auto` instead of `/pod:plan <n>`. That mode holds a deliberately high bar for deciding alone —
it proceeds on a fork only when the codebase's conventions, the requirements, and
standard practice all agree *and* being wrong would be cheap to reverse.
Otherwise it defers and names the open question. **Deferring is a correct outcome,
not a failure**: a wrong guess costs a whole executor run, a question costs one
visit.

**`--auto` does not launch anything.** Clean plans finish and wait; the
cross-plan collision check (`/pod:launch`) still runs before any lane starts. That check is
the only thing that can catch two independently-ready issues editing the same
file, and skipping it is exactly the mistake the review exists to prevent.

Report both outcomes together when the contexts finish:

```
4 planned · 3 clean, 1 needs you

  #84  planned clean
  #85  planned clean
  #87  planned clean
  #86  QUESTION — which overlay owns the marker tray after G1?
       tab: #86 overlay fixes

Answer #86, then: /pod:launch --review 84 85 86 87
```

**A context that stopped with a question is not a failed plan** — say what it
asked and which tab to visit, so the answer is one click away rather than a
hunt.

## 3. Start one planning context per issue

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
  --text "/pod:plan <n>" --enter --json
```

**Under `--auto`, send `/pod:plan <n> --auto`** — that flag is what makes the
context plan unattended and defer rather than wait on every choice (§2a).

Notes that matter:

- **The title is not optional.** Untitled tabs are indistinguishable and the
  whole flow falls apart — you cannot answer four contexts you cannot tell
  apart.
- **Terminal handles are routing metadata** — do not cache them across
  operations; re-resolve with `orca terminal list --worktree <selector> --json`
  (`../../_shared/orca-lanes.md`).
- **Send `/pod:plan <n>`, not a paraphrase.** Each context runs the real
  planning skill, including its adversarial review.
- A context that fails to start is reported and skipped; the others continue.

## 4. Hand control back

**Tell the user the wave is running and stop.** The contexts are talking to the
user, not to you.

- **Default:** each context asks its own questions and waits. They are meant to
  be visited.
- **`--auto`:** each context plans on its own; only ones hitting a real fork
  wait. Say that, so the user knows most tabs need nothing from them — and that
  they should check back rather than sit watching.

Report the tab titles and issue numbers so they can be found:

```
4 planning contexts started, one tab each:

  #84 balance tuning   #85 overlay fixes   #86 instrumentation   #87 cloud sync

Visit each tab and answer its questions. When they are all done:
  /pod:launch --review 84 85 86 87   check the plans against each other
  /pod:launch 84 85 86 87            check, then launch the ones that do not collide
```

**Include the issue numbers in that instruction.** The plans directory
accumulates across waves, and a bare `--review` in a fresh context has to guess
which plans belong to this one.

**Do not poll the terminals, read their output, or wait on them.** They are
talking to the user, not to you. Reading their output to "check progress" both
wastes context and risks acting on a half-finished plan.

## Failure modes to avoid

- **Fanning out over a whole milestone unasked.** Present and confirm; cap at ~4.
- **Creating worktrees for planning.**
- **Polling the planning contexts.** They are interactive with the user, not
  with you.
- **Launching after planning.** The collision review is a separate, deliberate
  step, so a human sees the plans together first.
- **Omitting the issue numbers** from the next-step instruction.
