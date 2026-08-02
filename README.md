# orca-skills

A Claude Code **plugin** that adds a **GitHub-Issues backlog and planning layer**
on top of [Orca](https://orca.computer): groom a backlog, plan work adversarially,
launch it into worktree lanes with agents, watch those lanes, and gate the
finished branch against the issue's own acceptance checklist.

> **Requires Orca** — an app that manages git repositories as sets of worktrees,
> each with its own terminals and agents. These skills drive it through its
> `orca` CLI. Without Orca the backlog half still works (it is pure `gh`), but
> nothing can be launched — the skills detect the absence and say so rather than
> half-working.

**Nothing in this pipeline ever merges.** Lanes end at an open PR, the gate
reports, you merge.

---

## Contents

- [The idea in one minute](#the-idea-in-one-minute)
- [Install](#install)
- [The seven skills](#the-seven-skills)
- [Flags, in full](#flags-in-full)
- [Workflows](#workflows)
- [The conventions the skills read](#the-conventions-the-skills-read)
- [What this is not](#what-this-is-not)
- [Docs](#docs)

---

## The idea in one minute

Orca tracks **lanes** — a worktree, its branch, its linked issue and PR, whether
an agent is alive in it. What Orca has no notion of is a **backlog**: milestones,
readiness, dependencies, and whether finished work actually satisfies what was
asked.

These skills fill that gap, and add one thing neither side has: **an evidence
gate**. Every issue carries a `### Done when` checklist written *before* the work
starts; when a branch is done, `/orca:verify` checks the branch against that
checklist — running the commands, grepping the diff, and refusing to guess at
what only a human can judge.

That is the whole design. A PR existing proves nothing about whether the work is
right, so something has to ask.

```
       backlog                    lanes                   proof
  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
  │ milestones       │    │ worktree         │    │ ### Done when    │
  │ readiness        │ →  │ branch + agent   │ →  │ commands run     │
  │ dependencies     │    │ opens a PR       │    │ diff checked     │
  └──────────────────┘    └──────────────────┘    └──────────────────┘
      GitHub                    Orca                  /orca:verify
```

---

## Install

**From GitHub** — the usual way:

```bash
claude plugin marketplace add tatejennings/orca-skills
claude plugin install orca@orca-skills
```

**From a local clone** — if you want to read or modify the skills:

```bash
git clone git@github.com:tatejennings/orca-skills.git
claude plugin marketplace add ./orca-skills
claude plugin install orca@orca-skills
```

Either way, **inside a running session** use the slash-command equivalents and
then reload, since new skills do not appear until the plugin does:

```
/plugin marketplace add tatejennings/orca-skills
/plugin install orca@orca-skills
/reload-plugins
```

**Updating.** A GitHub-sourced marketplace does not refresh itself, and updating
the catalog alone does **not** update the installed copy — run both:

```bash
claude plugin marketplace update orca-skills
claude plugin update orca@orca-skills
```

**Requirements**

| | |
|---|---|
| [Orca](https://orca.computer) | with Claude Code running in one of its terminals; the `orca` CLI ships inside the app |
| [Claude Code](https://claude.com/claude-code) | with plugin support |
| [`gh`](https://cli.github.com) ≥ 2.94.0 | authenticated. 2.94.0 added `blocked-by`/`blocking`; everything here is verified on 2.96.0 |

If several GitHub accounts are authenticated, note that the skills check the
**active** one before any write — `gh auth status`.

**Then, once per project:**

```
/orca:migrate
```

Everything else assumes the tracking model it establishes. Skipping it works if
your repo already keeps state in GitHub milestones and issues, but the failure
mode is quiet — an unmigrated repo returns empty lists that look like "nothing to
do". Run it at least as an audit.

Re-run it after upgrading this plugin: when a release changes what the skills
expect of a repo, `/orca:migrate` is what moves your project onto the new
contract.

---

## The seven skills

Grouped by what you are trying to do.

### Getting a repo ready

#### `/orca:migrate`
Brings a repo's tracking up to the model the other skills read. Inventories every
tracking file, classifies each section (live state / finished / narrative /
reference), and proposes milestones, issues, `### Done when` checklists,
dependency edges, and the `AGENTS.md` block. **Writes nothing until you approve,
and never commits** — the diff stays rejectable.

Run it three times in a repo's life: to onboard it, after a plugin upgrade that
changes the contract, and any time you want a drift audit. It records which
schema version it applied, so a later run can tell a repo that *is* current from
one that merely *was*.

```
/orca:migrate
```

#### `/orca:triage`
**Paste in a pile of raw bugs, features, and research items — it files them as
proper GitHub issues, one at a time.** Nothing needs to exist in GitHub first;
creating the issues *is* the work being delegated.

For each item it asks what it actually means, what "done" would look like, when,
what it depends on, and whether an agent can even do it — then creates the issue
with a `### Done when` checklist, milestone, scope label, and real dependency
edges. It checks for duplicates before filing, and each item is created as it is
triaged, so an item you drop mid-pass was never filed.

```
/orca:triage
  crash when rotating the device mid-run
  workshop should remember your last tab
  do we still need Firebase at all
  splash wordmark should be the logo, not text
```

It also works on issues that already exist:

```
/orca:triage 101 103 107  # groom these specific ones
/orca:triage              # audit the whole backlog
```

With no arguments it **audits everything** — catching both never-triaged issues
and ones that have *drifted*: a `blocked` label whose blocker already closed, a
dependency written only in prose, criteria under the wrong heading.

### Deciding how to do the work

#### `/orca:plan`
Adversarial planning for one piece of work — an issue number, a milestone, or a
free-form description. Researches with parallel agents, drafts an
execution-ready plan, then hands it to a **cold-reader agent** to attack for
completeness, holes, single-context feasibility, and blast radius.

Writes the `### Done when` checklist onto the issue, because that is what makes
the work gateable later. Saves the plan to `~/.claude/plans/<repo>/` so it
survives the session.

```
/orca:plan 84                          # plan issue #84
/orca:plan fix the vent double-tap bug # free-form
/orca:plan 84 --launch                 # plan, then launch it as a lane
```

#### `/orca:wave`
Plans **several issues at once**, each in its own terminal in the current
worktree. You move between tabs answering each context's questions instead of
planning one at a time. No worktrees are created — planning writes no repo files.

Then the part that earns it: **checks the finished plans against each other for
file collisions.** Two issues can be independently ready and still edit the same
file; dependency edges cannot express that, so comparing plans is the only place
it shows up before work starts.

```
/orca:wave 84 85 86 87            # four planning contexts, one tab each
/orca:wave 84 85 86 87 --auto     # …but only stop where a real question comes up
/orca:wave --review 84 85 86 87   # check those plans against each other
/orca:wave --launch 84 85 87      # start the non-colliding ones as lanes
```

### Doing the work

#### `/orca:launch`
Turns an issue into a **lane**: a fresh Orca worktree with an agent already
implementing it. Reads the issue and its acceptance criteria, refuses work that
is already in flight or marked `manual`, writes an executor contract *outside*
the repo, creates the worktree with the issue linked natively, starts one agent
on it, and **stops**.

The contract binds the executor: implement, self-review, then **open a normal PR
on its own** with `Closes #<n>` — not a draft, since review tooling skips those.
It never merges; that stays yours.

```
/orca:launch 84
```

#### `/orca:status`
The dashboard, and the join this plugin exists for. Milestone progress, a
`READY NEXT` list of unblocked issues, a `YOUR TASKS` section for `manual` work,
and every lane's branch, PR state, and session liveness.

Read-only apart from regenerating `ROADMAP.md`, and conservative by construction
— safe to put on a loop.

```
/orca:status                    # the dashboard, + regenerate ROADMAP.md
/orca:status --no-roadmap       # dashboard only
/orca:status --reap             # also delete provably-finished lanes
/loop 15m /orca:status --reap   # keep it live
```

### Proving it was done

#### `/orca:verify`
**The evidence gate.** Checks a finished branch against its issue's own
`### Done when` checklist: runs the criteria that are commands, greps *added
lines* for the ones that are diff assertions, and **refuses to guess** at the
ones only a human can judge.

Evidence comes from the branch and the commands — never from the executor's
report of them. Never merges, never closes an issue, never marks a PR ready.

```
/orca:verify 84       # by issue
/orca:verify          # the current worktree's lane
```

| Verdict | Meaning |
|---|---|
| `pass` | every checkable criterion met, and there were no human ones |
| `pass-with-review` | checkable criteria met, but ≥1 needs your judgement — **listed** |
| `fail` | ≥1 checkable criterion failed — **every** failure named, with evidence |

---

## Flags, in full

| Skill | Flag | Effect |
|---|---|---|
| `/orca:plan` | `--launch` | After the review, launch the plan as a lane instead of stopping for approval. Disqualified — and stops — if the review says split, a fork lacked a clear answer, **a review finding would change an adopted plan's approach**, the work is already in flight, or Orca is unavailable. |
| `/orca:wave` | `--auto` | Each planning context runs unattended and stops only if a real fork comes up. Does **not** launch — the collision review still gates every lane. |
| `/orca:wave` | `--review` | Check the finished plans against each other for file collisions. |
| `/orca:wave` | `--launch` | Start the non-colliding plans as lanes, one at a time. |
| `/orca:status` | `--reap` | Delete provably-finished lanes. Every safety check must pass; ambiguity is always a skip, never a prompt. |
| `/orca:status` | `--no-roadmap` | Skip regenerating `ROADMAP.md`. |

Everything else takes plain arguments: issue numbers, a milestone name, or a
free-form description.

---

## Workflows

### 1. Onboarding a repo

```
/orca:migrate     → proposes; you approve; nothing is committed
                    review the diff, commit it yourself
/orca:triage      → audit the backlog, fix what it finds
/orca:status      → confirm it reads correctly
```

You are done when `/orca:status` shows a milestone with progress and a
`READY NEXT` list you believe.

### 2. One issue, start to finish

```
/orca:status          → pick something from READY NEXT
/orca:plan 84         → research, draft, adversarial review
                        you approve                        ← GATE 1
/orca:launch 84       → worktree + agent; this session is free
                        …the agent implements and opens a PR on its own…
/orca:status          → the lane shows `awaiting-gate`
/orca:verify 84       → the evidence gate                  ← GATE 2
                        pass → offer to mark it ready
                        fail → criteria commented on the PR; /orca:launch 84 reworks it
you review and merge                                       ← GATE 3
/orca:status --reap   → the finished lane is cleaned up
```

### 3. Several issues in parallel

```
/orca:status             → READY NEXT: #84 #85 #86 #87
/orca:wave 84 85 86 87   → four tabs: "#84 balance tuning", "#85 overlay fixes", …
                           visit each, answer its questions
/orca:wave --review 84 85 86 87
                         → "3 ready; #86 collides with #85 in GameScene.swift"
/orca:wave --launch 84 85 87
                         → the three non-colliding ones become lanes
/orca:status             → watch all three
```

A collision is a **sequencing** problem, not a bad plan: launch one, let it
merge, re-plan the other against the merged result.

### 4. Fire and forget one issue

```
/orca:plan 84 --launch
```

Plans, reviews, and launches without stopping for approval — but only when the
decisions are unambiguous. It **defers instead of guessing**: if the review says
split, or any real fork lacked a clear answer, it stops and presents the plan
with the open question named. A deferral costs one question; a wrong guess costs
an entire executor run.

### 5. Keeping the backlog honest

```
/loop 15m /orca:status --reap   # live dashboard, finished lanes cleaned up
/orca:triage                    # periodically: drift audit + fix
/orca:migrate                   # after upgrading this plugin
```

### 6. Emptying your head into the backlog

You have been keeping a list — in a notes app, in your head, in a scratch file.
Paste it:

```
/orca:triage
  crash when rotating the device mid-run
  workshop should remember your last tab
  do we still need Firebase at all
  splash wordmark should be the logo, not text
```

It works through them one at a time, asks what each needs, and files each as a
proper issue as it goes. There is no separate capture skill because this is the
capture step — and it is the one that produces issues the rest of the pipeline
can actually consume.

---

## The conventions the skills read

Four things live in your repo's GitHub, and every skill reads them the same way.

**Milestones say *when*.** The active milestone is the open one with the nearest
due date. Give exactly one a date and leave later ones dateless, or every run has
to ask which is active.

**An issue with no milestone is the unscheduled backlog.** That is a valid state,
not a defect — assigning a milestone is what scheduling *means*. Do not create a
"Backlog" milestone.

**Blocking is a real dependency edge**, not a label:

```bash
gh issue edit <blocked> --add-blocked-by <blocker>
```

That edge is what readiness reads. A `blocked` label can mirror it for the issue
list, but a label alone is decorative — every readiness query will call that
issue ready, which is the honest reading of the data.

**Every issue carries a `### Done when` checklist**, written when the issue is
filed rather than after the work:

```markdown
### Done when

- [ ] `./scripts/test.sh` exits 0
- [ ] `parseManifest` appears in the diff
- [ ] `docs/api.md` is modified
- [ ] The importer handles a malformed header without crashing
```

The first three are machine-checkable; the fourth is not, and that is fine.
`/orca:verify` sorts every criterion into **command**, **diff assertion**, or
**human** — and it reports human criteria for your judgement rather than passing
them. A gate that quietly passes what it cannot check is worse than no gate.

**Two labels the skills understand:**

| Label | Meaning |
|---|---|
| `manual` | Only a human can do this — account access, store configuration, a physical device. `/orca:launch` refuses it; `/orca:status` lists it under `YOUR TASKS`. |
| scope labels (`sound`, `board ui`, …) | Which part of the system the work touches. Reuse an existing one; create one named for the area if none fits. |

`manual` means the **whole task** is human. An issue with a few human *criteria*
is still agent work — that belongs in the checklist, not the label.

**`ROADMAP.md` is generated and gitignored.** `/orca:status` rewrites it every
run. It is a rendering of GitHub state, never a source — delete it and regenerate
without losing anything. That is the same principle as the rest of the model:
truth is rebuilt, never stored. See **[TRACKING.md](TRACKING.md)**.

---

## What this is not

**Not a wrapper around the `orca` CLI.** Orca ships its own version-matched
skills — `orca-cli` for worktrees, terminals, and the browser; `orchestration`
for supervised multi-agent coordination. Read them with `orca skills get <name>`.
This plugin points at them rather than restating them.

The boundary, stated once: **Orca owns how the CLI works; this plugin owns what
becomes a lane, what contract binds the executor, and what proves the result.**

**No merge automation.** Lanes end at an open PR and a human merges. Since
the merge is the only state transition in the model, automating it would automate
the one decision worth keeping.

**No enabled automation.** The pipeline *can* be driven on a schedule by an Orca
automation, but this plugin ships none enabled, and turning one on has real
preconditions — chiefly that `/orca:verify` has been seen to **fail** on
incomplete work, not just pass. The command, the precheck that carries the
quotas, and the full list are in
[`_shared/automation.md`](plugins/orca/skills/_shared/automation.md).

A pipeline that can open PRs but cannot check them is a machine for generating
confident wrong work.

---

## Docs

- **[TRACKING.md](TRACKING.md)** — where roadmaps, milestones, and tasks live in
  a project these skills are pointed at, and why a tracked progress file breaks
  under parallel lanes.
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — adding skills, the after-edit
  checklist, and how *this* repo works (it commits straight to `main`).
- **[CHANGELOG.md](CHANGELOG.md)** — what changed, and the field findings behind
  each change.
- **`GUIDE.html`** — the same content as this README, laid out visually with the
  pipeline as a diagram. Generated and gitignored; open it from your clone.
  Regenerated whenever this README changes.
