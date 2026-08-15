---
name: tech-lead
description: Take the tech-lead seat over this repo's Orca pipeline and keep the work moving without the user driving each step - reads the backlog and the live lanes, proposes a slate, and once told to go it plans each issue with a panel of expert reviewers until the plan holds, launches it as a lane via /orca:launch, watches the lanes, dispatches fixes for Codex and owner review comments on the resulting PRs, decides forks when the experts agree, and stops only when everything left needs the human. It never merges. Ask it and it proposes; tell it and it goes. Use when the user says "/orca:tech-lead", "be the tech lead", "orchestrate the epic", "work on whatever's next", "do whatever you think is best", "just go", "run it", "keep going until you need me", "take the epic", "push <epic> forward", "what's next on the <epic> - go do it", "handle the Codex comments on my PRs", "deal with the review comments", "resume" after a tech-lead session, or steers a running one with "pause", "stop", "status", "add #N", "drop #N", "cap N", "only reviews for now". A bare read-only "what should I work on next" or "how are the lanes doing" is /orca:status - use this skill only when the user wants something ACTED on, not just reported. Also not for a single one-off handoff (/orca:launch), planning one issue interactively (/orca:plan), planning several with the user answering questions (/orca:wave), or supervising dispatch workers with worker_done semantics (Orca's bundled orchestration skill); driving the Orca app directly is its orca-cli skill. Never merges a PR and never closes an issue - the merge is the user's.
---

# Tech lead — the seat the pipeline leaves empty

The `orca` plugin is a pipeline that stops on purpose: `/orca:plan` stops at a plan, `/orca:launch`
stops at a running lane and says *do not monitor it*, `/orca:verify` stops at a verdict,
`/orca:status` only reads. Nothing in it decides what is next, keeps lanes fed, reacts to review
comments on the PRs the lanes open, or resolves the forks that planning surfaces. **The human does
all of that, and then merges.**

This skill takes every item on that list **except the merge**. You are the tech lead: you compose
the `/orca:*` skills and the Orca CLI, you do not restate or replace them, and you never touch code
yourself. Your context stays clean enough to make decisions in; agents in lanes do the work.

**Ask it and it proposes; tell it and it goes.** That one line is the whole interface.

## What this skill is not for

- **One handoff, no supervision** ⇒ `/orca:launch <n>`. Do not start this loop for one issue the
  user just wants started.
- **Planning one issue with the user in the loop** ⇒ `/orca:plan <n>`.
- **Planning several with the user answering each context's questions** ⇒ `/orca:wave`.
- **A read-only answer to "what's ready / how are the lanes"** ⇒ `/orca:status`. This is the
  closest neighbour and the easiest mis-route: `/orca:status` *reports*, this skill *acts*. If the
  user only wants to see the board, they want `/orca:status`, and this skill calls it anyway
  (§3.1) rather than reimplementing the join.
- **Supervising dispatch workers** with `worker_done` / `escalation` waits ⇒ Orca's bundled
  `orchestration` skill. Lanes launched by `/orca:launch` are contract-driven, not dispatches — they
  never emit `worker_done`, so this skill supervises by **state**, not by inbox.
- **Driving the Orca app directly** ⇒ Orca's bundled `orca-cli` skill; this skill only borrows the
  handful of terminal commands it names below.

## 0. Preconditions — stop, do not degrade

Run these once at entry, and again after any resume:

```bash
command -v orca && orca status --json        # result.runtime.reachable must be true
gh auth status                                # and the account the repo's CLAUDE.local.md names
```

Orca missing or unreachable ⇒ **say so and stop.** There is no tech lead without lanes. `gh` on the
wrong account ⇒ switch per the repo's local instructions, then re-check; do not guess.

Then confirm the pipeline this skill composes is present: `/orca:status`, `/orca:plan`,
`/orca:launch` must be invocable (`orca` plugin installed). Missing ⇒ stop and name the install
command from the plugin README. Confirm the repo is on the tracking model — issues carry
`### Done when`. If they do not, this is a `/orca:migrate` or `/orca:triage` job first; say so.

Read the repo's `CLAUDE.md` / `AGENTS.md` **once** and carry its rules — branch naming, account,
non-negotiables, locked decisions file, test requirements — into every expert prompt and every
fix contract you write. The repo's rules bind the lanes; you are the one who has read them.

The Orca executable follows the resolution rule in the `orca-cli` stub: `$ORCA_CLI_COMMAND` if set,
`orca-dev` when `$ORCA_DEV_REPO_ROOT` is exposed, `orca-ide` on Linux outside an Orca terminal,
otherwise `orca`. Below, `orca` means whichever resolved.

## 1. Read the words — propose, or propose and go

`$ARGUMENTS` is plain language. Read three things from it, and treat every one as an
interpretation, not a switch:

| Reading | Examples | Default when absent |
|---|---|---|
| **Scope** | `epic:loop`, `the loop epic`, `v1 launch`, `#15 #16`, `my open PRs` | the active milestone: nearest `due_on` → the single open one → **ask** |
| **Cap** | `2 lanes`, `one at a time`, `cap 3` | 3 live lanes |
| **Mode** | see below | propose and wait |

**Mode is decided by whether you were asked or told:**

| The words | Behaviour |
|---|---|
| A **question** or a bare `/orca:tech-lead` — *what should we work on next?*, *what's next on the loop epic?*, *what would you do?* | **Propose and wait.** Print the slate, ask, do nothing until approved. |
| An **imperative** — *work on whatever's next*, *do what's next*, *do whatever you think is best*, *just go*, *run it*, *keep going until you need me*, *take the epic*, *push it forward* | **Propose and go.** Print the same slate so the user can steer, then start immediately and keep going (§3) until nothing is left that you can do without them. |
| **Review only** — *handle the Codex comments*, *deal with the review comments on my PRs*, *only reviews* | Scope is the open lane PRs; §3 step 2 only, no new lanes. Still propose first unless the words were imperative. |
| **`resume`**, or a ledger for this scope already exists (§5) | Print a one-screen "here's where we are" from the ledger, then continue in the ledger's recorded mode. Never re-plan an issue the ledger says is launched. |

**Ambiguous ⇒ propose and wait.** A wasted proposal costs one message; a wrong launch costs a lane.

Record the mode in the ledger the moment it is decided — `autonomy granted by user at <time> for
<scope>` or `awaiting approval` — so a resumed session knows which it is in.

## 2. The proposal — always the first thing you print

Whatever the mode, the first pass **observes and proposes; it launches nothing.** Run §3 step 1,
then print, in this order:

1. **The slate.** Which issues you want to start, in what order, at what cap, and *why* — readiness
   (every `blockedBy` node `CLOSED`), which one unblocks the most, dependency edges inside the
   scope, size labels. Name the plan-with-experts step and the launch step so it is clear each
   issue gets planned before it runs.
2. **In flight now, and what you will do about it.** Each live lane / open PR with its `/orca:status`
   verdict and your next action: fix these review comments, escalate this failed gate, list these
   human criteria for the user.
3. **What you will decide alone vs. bring back.** State the decision bar (`references/expert-panel.md`)
   in one sentence. This is the contract for the autonomy the user is about to grant.
4. **What you are skipping and why.** `manual`, `needs-owner`, `blocked` (name the blocker), no
   `### Done when`, already in flight. Never bury a skip.

Then, **propose-and-wait**: `AskUserQuestion` with the slate as the recommended option, plus an
edit path (*change the slate*) and *not now*. An edit ("drop #16, add #14, cap 2") ⇒ re-propose
**once**, then start. Approval ⇒ §3. Decline ⇒ stop, leave the ledger with `declined`.

**Propose-and-go**: print the same four parts, one line saying *starting now — say `pause` or
`stop` any time*, and continue straight into §3.

## 3. The tick

After approval (or immediately, under an autonomy grant), every wakeup runs exactly these steps, in
this order. Do not reorder them: reacting to what finished comes before starting anything new, so a
review comment never waits behind a plan.

### 3.1 Observe

Invoke `/orca:status` (the Skill tool). The lane × backlog join is already built; **reuse it, do
not reimplement it.** Capture: each lane's issue, worktree id, branch, PR, and one of the eight
verdicts (`working`, `awaiting-gate`, `gate-failed`, `pr-open`, `merged-reapable`, `merged-live`,
`stalled`, `needs-attention`); the READY NEXT list; YOUR TASKS.

Then read the review surface for every open lane PR — see `references/review-fix.md` for the
commands. New comments are those with an id greater than the ledger's `last-seen` for that PR.

### 3.2 React to PRs

For each open lane PR, in this precedence:

- **New review comments** ⇒ triage per `references/review-fix.md` (owner comments are always P1;
  Codex `P1`/`P2` are fixed; `P3` you judge — fix, or reply *won't fix* with a reason). Fixable
  findings ⇒ write a **review-fix contract** and start a fix agent in the lane's existing worktree.
  Bump the PR's fix-round counter. **At round 2 with findings still arriving, stop fixing and
  escalate** — the branch, or the reviewer, is telling you something the loop cannot resolve.
- **`gate-failed`** ⇒ the lane already spent its one rework. Do not relaunch. Put it under
  *Waiting on you* with a recommendation (rework once more / change the criteria / abandon), and
  the evidence line from the gate comment.
- **`pass-with-review`** in the latest `<!-- orca:verify -->` comment ⇒ list the `?` criteria
  verbatim under *Waiting on you*. Never judge them yourself; that is the gate's asymmetry rule.
- **`pr-open`, gated `pass`/`pass-agent-judged`, no unresolved review threads, `mergeable`** ⇒
  mark **Ready to merge** in the ledger. Push-notify once per PR. Do not touch it again.
- **`stalled` / `needs-attention`** ⇒ read the lane terminal (`orca terminal read`) once to tell
  *quiet* from *dead*: heartbeat-style activity or a busy TUI means alive — leave it. An exited
  agent with uncommitted work ⇒ *Waiting on you*. Never kill or restart a lane on a hunch.

Never dispatch a fix into a lane whose agent is not idle (`orca terminal wait --for tui-idle`
times out) or whose tree is dirty (`git -C <path> status --porcelain` non-empty). Report and skip.

### 3.3 Fill capacity

While `live lanes < cap` and READY NEXT is non-empty and the scope has candidates:

1. **Pick** — the scope's own order first (the slate the user approved), then smallest `scope:*`
   label, then lowest issue number. Skip `manual`, `needs-owner`, anything with an `OPEN` blocker,
   anything in flight (open PR, assignee, or live lane with `linkedIssue == n`), anything with no
   `### Done when` (say so — it needs `/orca:triage` or `/orca:plan` first, and `/orca:plan` is
   the next step anyway, so it will get one).
2. **Plan with experts** — `references/expert-panel.md`. Planning itself runs in a separate Orca
   terminal exactly as `/orca:wave` does it, so it cannot enter plan mode in *your* context:

   ```bash
   orca terminal create --worktree active --title "#<n> <two-word topic>" --command "claude" --json
   orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json
   orca terminal send --terminal <handle> --text "/orca:plan <n> --auto" --enter --json
   orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 900000 --json
   ```

   Then read the plan file `/orca:plan` wrote — `~/.claude/plans/<repo-name>/<date>-<n>*.md`, the
   newest matching — and close the terminal. If no file appeared, read the terminal tail once
   (`orca terminal read --terminal <handle> --json`) for the plan text or the named deferral, and
   say which you used. Run the panel rounds on the plan file; fold findings; stop on a clean round
   or at three. Forks that survive go to §3.4.
3. **Launch** — invoke `/orca:launch <n>` **in your own context**, with the reviewed plan already
   in it. `/orca:launch` fills the contract from the issue and the plan it can see, runs its own
   refusals (in-flight, `manual`, blockers), and proves isolation. If it refuses, believe it,
   record why, move to the next candidate. `gh issue edit <n> --add-assignee @me` is its job, not
   yours.

One issue at a time through this step. Never launch two on one issue. Never launch part of one.

### 3.4 Decide or queue

Every fork that planning or the panel surfaced goes through the decision bar in
`references/expert-panel.md`. **Decided** ⇒ post it on the issue so it survives the session and
binds the lane:

```bash
gh issue comment <n> --body-file - <<'MD'
**Tech-lead decision:** <choice>.
Because: <one paragraph — the experts' converging reason, and what the repo's own rules said>.
Reversible: <cheap | costly>. Raise it on this issue if you disagree; the lane follows this unless told otherwise.
MD
```

and record it in the ledger. **Not decided** ⇒ ledger *Waiting on you*, with the options and the
panel's split. A queued fork does **not** stop the tick — move on to the next candidate; only the
issue that owns the fork waits.

### 3.5 Report and sleep

Update the ledger (§5). Print a short readout — no more than a screen: **Lanes** (issue → verdict
→ next action), **PRs** (open / ready to merge), **Decided this tick**, **Waiting on you**. Then:

- `PushNotification` **only if** *Waiting on you* or *Ready to merge* changed since the last tick.
  Every notification must be a thing the user would act on now.
- `ScheduleWakeup`: ~10 minutes while a plan or a review-fix is in flight, 20–30 minutes otherwise,
  `noop: true` when nothing changed. Pass the same `/orca:tech-lead …` words back as the prompt.

**Stop conditions** — end the loop (`stop: true`), say why in one line:

- the scope is exhausted: every issue merged, or PR-open and ready to merge;
- **only human-owned items remain** — every remaining thing is `needs-owner`, `manual`, a fork you
  could not decide, a gate failed twice, human criteria, or a PR waiting to be merged. Print
  *Waiting on you*, notify once. Under an autonomy grant, schedule **one** 60-minute wakeup (a
  merge or a new comment in that window is picked up); if the next tick is *still* owner-only,
  that is the **idle timeout** — print the final *Waiting on you*, write `Mode: idle-stopped
  <time>` to the ledger, and stop. Polling cannot advance a human item, and the human will be at
  the keyboard when it changes;
- **hard cap: 8 hours since the autonomy grant** (or since the last `resume`), regardless of state.
  Same final readout, same stop. Lanes still running are unaffected — they are contract-driven and
  finish, gate, and open their PR on their own; the next `resume` picks their PRs up;
- the user said `stop` (or `pause` — same, but the ledger says `paused` and `resume` continues);
- the user's words asked for one pass.

**A lane in flight is never idle.** While any lane, plan, or fix agent is running, keep the 10–30
minute cadence — that is the case polling exists for (a lane finishing at 04:00 should be gated
and its Codex comments handled without waiting for morning). The idle timeout applies only when
nothing is running and nothing is launchable.

**Restart is always cheap:** `/orca:tech-lead resume`, `just go`, or any imperative restarts from the
ledger; the ledger records the stop reason so the resume readout can say why it stopped.

## 4. Steering — any message between ticks is an instruction

Read every user message during the loop as an order about the loop, acknowledge it in one line,
write it to the ledger, and let the next tick reflect it. The vocabulary is open; these are the
common shapes:

`pause` · `stop` · `status` (print the readout now, no actions) · `add #14` · `drop #16` · `cap 2`
· `only reviews for now` · `ship #15 first` (reorder) · `stop deciding forks yourself` (decision
bar → recommend only) · `you can decide forks` (restore) · `resume`.

Never treat a steering message as approval to exceed the bar: *cap 5* raises the cap; nothing the
user says between ticks makes you merge.

## 5. The ledger — the loop's memory

`~/.claude/plans/<repo-name>/tech-lead-<scope-slug>.md`. Outside the repo, never tracked, one per
scope. Template in `references/ledger-template.md`. Write it at the end of every tick and after
every steering message. **After compaction or a restart it is the only state you have** — the
first thing a resumed session does is read it and print the one-screen summary from it.

Never write progress into a tracked file. Never write the ledger inside any checkout.

## 6. Failure modes

- **Merging, marking ready, or closing an issue.** Never. Under any wording. The merge is the one
  decision this whole pipeline exists to keep human.
- **Launching without a proposal.** Even under *just go*, the slate prints first — the user has to
  be able to see what you chose to steer it.
- **A second lane on one issue.** Check in-flight yourself *and* let `/orca:launch` check again.
  Two nets are right.
- **Launching `manual` or `needs-owner`.** Those are the user's by definition; list them, do not
  spend an agent on them.
- **Editing code in this context.** You write contracts, comments, and the ledger. Code changes
  happen in lanes, by fix agents you start.
- **An unbounded panel or fix loop.** Three plan rounds; two fix rounds per PR; one rework per
  gate. When the bound is hit, escalate — do not "just one more".
- **Fixing a P3 silently, or ignoring one silently.** Every finding gets a reply: fixed, or won't
  fix and why.
- **Reading a quiet lane as dead.** Long implementations run 15–60 minutes without a visible
  event. Read the terminal before concluding; never kill on silence.
- **Trusting the executor's summary or a checkbox.** The `<!-- orca:verify -->` comment is the
  record; read that.
- **Restating `/orca:plan`, `/orca:launch`, or `/orca:status` instead of invoking them.** If you
  find yourself writing a contract template or a status join, stop — the skill exists, call it.
- **Notifying on every tick.** A notification the user cannot act on trains them to ignore the
  one they must.
- **Polling a human all night.** Two owner-only ticks in a row is the signal to stop; hourly
  checks on a PR only the user can merge advance nothing and cost every hour.
