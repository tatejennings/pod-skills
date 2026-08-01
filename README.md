# orca-skills

A Claude Code **plugin marketplace** for skills that add a **GitHub-Issues
backlog and planning layer** on top of [Orca](https://orca.computer) — migrate a
repo's tracking onto a shared model, plan work adversarially, hand it off to a
worktree agent, watch the lanes, and gate the finished branch against the issue's
own acceptance checklist.

> **Requires Orca** — an app that manages git repositories as sets of worktrees,
> each with its own terminals and agents. These skills drive it through its
> `orca` CLI. Without it, the backlog half still works (it is pure `gh`), but
> nothing can be handed off — the skills detect the absence and say so rather
> than half-working.

## What this is, and what it is not

**This is not a wrapper around the `orca` CLI.** Orca ships its own
version-matched skills for that — `orca-cli` for worktrees, terminals, and the
browser; `orchestration` for multi-agent coordination. Read those with
`orca skills get <name>`. This plugin never restates them; it points at them.

What Orca does **not** have is a backlog. It tracks lanes — `linkedIssue`,
`linkedPR`, `workspaceStatus`, lineage, liveness — but nothing about milestones,
readiness, dependencies, or whether finished work actually satisfies what was
asked. **That gap is what these skills fill.**

The boundary, stated once: *Orca owns how the CLI works; this plugin owns what to
hand off, what contract binds the executor, and what proves the result.*

## Requirements

- **[Orca](https://orca.computer)**, with Claude Code running in one of its
  terminals. The `orca` CLI ships inside the app.
- **[Claude Code](https://claude.com/claude-code)** with plugin support.
- **[`gh`](https://cli.github.com)** ≥ 2.94.0, authenticated — the release that
  added `blocked-by`/`blocking`, sub-issues, and issue types. Everything here is
  verified on 2.96.0. If several accounts are authenticated, note that the skills
  check the **active** one before writing.

## Install

```bash
git clone git@github.com:tatejennings/orca-skills.git
claude plugin marketplace add ./orca-skills
claude plugin install orca@orca-skills
```

(`claude plugin marketplace add` also accepts a GitHub `owner/repo` directly.
Inside a session use `/plugin marketplace add …` and
`/plugin install orca@orca-skills`, then `/reload-plugins` — new skills don't
appear until the plugin reloads.)

Then, in **each project** you point the skills at:

```
/orca:migrate
```

Everything else assumes the tracking model it establishes. Skipping it works if
your repo already keeps state in GitHub milestones and issues — but the failure
mode is quiet, so run it at least as an audit.

**Re-run it after upgrading this plugin.** When a release changes what the skills
expect of a repo, `/orca:migrate` is what moves your project onto the new
contract — it records which schema version it applied, so it knows the difference
between a repo that is current and one that merely was. It also catches drift the
other direction, when practice slips away from the model.

## Skills

| Skill | What it does |
|---|---|
| `/orca:migrate` | Brings a repo's tracking up to the model the other skills read — milestones and issues for state, `docs/specs/` for narrative, a `### Done when` checklist on every issue. Run it to onboard a project, again after a plugin upgrade that changes what the skills expect, and any time to audit for drift. Writes nothing until you approve. |
| `/orca:triage` | Works through a batch of raw issues with you, one at a time — what does this mean, what would "done" look like, when, what does it depend on — then writes the `### Done when` checklist, sets the milestone, and records real dependency edges. Turns captured thoughts into something `/orca:plan` can consume. |
| `/orca:launch` | Turns "start #84" into a verified lane: reads the issue and its acceptance criteria, refuses work already in flight or marked `manual`, writes the executor contract outside the repo, creates the worktree with the issue linked, starts one agent on it, and stops. |
| `/orca:status` | The dashboard: milestone progress, a `READY NEXT` list of unblocked issues, and every lane's branch/PR/session state — the backlog join Orca has no notion of. Regenerates the gitignored `ROADMAP.md` every run so it never goes stale (`--no-roadmap` to skip); `--reap` deletes provably-finished lanes. Safe to loop. |
| `/orca:verify` | The evidence gate. Checks a finished branch against its issue's own `### Done when` checklist — runs the commands, greps the diff, and refuses to guess at what only a human can judge. Never merges. |
| `/orca:plan` | Adversarial implementation planning: research with parallel agents, draft, then have a cold reader attack the plan for holes, feasibility, and blast radius. With `--launch`, continues straight into `/orca:launch`. |

**Nothing in this pipeline ever merges.** Lanes end at a PR; the gate reports;
you merge.

### Running it unattended

The pipeline can be driven on a schedule by an Orca automation, but this plugin
**ships no enabled automation** and enabling one has real preconditions — chiefly
that `/orca:verify` has been seen to *fail* on incomplete work, not just pass.
The command, the precheck that carries the quotas, and the full precondition list
are in `plugins/orca/skills/_shared/automation.md`.

The short version: a pipeline that can open PRs but cannot check them is a
machine for generating confident wrong work.

## The pipeline

```
/orca:migrate        … establishes the tracking model; re-run when it changes
      ↓
raw issues
  → /orca:triage     … one at a time: what, when, done-when
      ↓
ready issue
  → /orca:plan       … you approve the plan              ← GATE 1
  → /orca:launch     … one worktree, one agent, then stop
  → executor implements, opens a DRAFT PR
  → /orca:verify     … evidence gate, machine-checked    ← GATE 2
  → you review and merge                                 ← GATE 3
```

Three gates, and a human at the first and last. The middle one is the point:
a PR existing proves nothing about whether the work is right.

## The stateless roadmap

`ROADMAP.md` is **generated and gitignored** — a rendering of GitHub state, never
a source of truth. Regenerate it any time; delete it without losing anything. No
lane writes to it, so it never conflicts, and it cannot drift from the issues
because it *is* the issues.

This is the same principle as the rest of the model: **truth is rebuilt, never
stored.** See [TRACKING.md](TRACKING.md).

## Docs

- **[TRACKING.md](TRACKING.md)** — where roadmaps, milestones, and tasks live in
  a project these skills are pointed at, and why a tracked progress file breaks
  under parallel lanes.
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — adding skills, the after-edit
  checklist, and how *this* repo works (it commits straight to `main`).
