# Changelog

Notable changes to the `orca` plugin. Versions track
`plugins/orca/.claude-plugin/plugin.json`.

## 1.0.0 — 2026-07-31

The suite is complete: five skills and one disabled-by-default automation.

**`/orca:status`** — the read-only dashboard, and the join this plugin exists for.
Orca knows lanes; GitHub knows the backlog; neither is complete alone.

- **The lane half is one call.** `orca worktree ps --json` already returns branch,
  `linkedIssue`, `linkedPR`, `workspaceStatus`, `liveTerminalCount`, and live
  `agents[].state`. Per-lane fan-out is explicitly forbidden — only `git status`
  and `rev-parse HEAD` are fetched per lane, and only for lanes that might be
  reapable.
- **`linkedPR` is a number, not a state**, so PR state comes from one repo-wide
  `gh pr list` joined locally by branch.
- **New verdict `awaiting-gate`** — a draft PR with no agent running. That is a
  lane asking for `/orca:verify`, and it is the state this pipeline is built
  around. A draft PR is the expected shape, never a problem to report.
- **Degrades honestly**: Orca down ⇒ backlog half only; `gh` down ⇒ lane half
  only; both ⇒ stop. Never presents a partial run as complete.
- **Reports decorative blocking**: issues with a `blocked` label but no
  dependency edge are called ready, and the report says so rather than silently
  trusting either signal.
- **`--roadmap`** regenerates the gitignored `ROADMAP.md`, and **refuses to write
  it if it is tracked** — pointing at `/orca:migrate`, which proposes untracking
  with consent.
- **`--reap`** deletes only `merged-reapable` lanes, re-running the
  primary-checkout proof immediately before each delete. Ambiguity is always a
  skip, never a prompt.

**`/orca:verify`** — the evidence gate, and the one genuinely new thing here.

- Checks the branch against the issue's own `### Done when` checklist: runs the
  command criteria, greps **added lines only** for diff assertions, and **refuses
  to guess** at prose criteria.
- **No checklist ⇒ stop.** Inventing criteria and then passing them is the exact
  failure the gate exists to prevent.
- **Checkbox state is never evidence.** `- [x]` means someone typed an `x`.
- Catches two subtle frauds by construction: a **pre-existing** artifact offered
  for a criterion demanding a new one, and **stale evidence** produced before the
  change it supposedly validates.
- Three verdicts, and `pass` vs `pass-with-review` is load-bearing — `pass` is
  impossible while any human criterion is outstanding.
- Reports **every** failed criterion, so an executor does not burn a cycle per
  failure.
- Never merges, never closes an issue, never marks a PR ready unprompted.

**`/orca:plan`** — adversarial planning: parallel research agents, a drafted plan,
then a cold-reader agent attacking completeness, holes, single-context
feasibility, and blast radius.

- **Writes the `### Done when` checklist onto the issue.** This is what makes the
  work gateable later, and it is part of planning rather than an afterthought.
  Fabricating criteria is called out as worse than a short honest list.
- Adopts a pre-written plan verbatim rather than re-planning it, while still
  reviewing it.
- **`--launch`** hands the approved plan to `/orca:handoff`. Five disqualifiers
  stop an auto-launch — a split verdict, an unresolved fork, a review finding
  against an adopted plan, work already in flight, or Orca unavailable.

**The automation** (`_shared/automation.md`) — a config artifact, not a skill,
and **shipped disabled**.

- The precheck is where safety lives: it fails closed, and carries readiness,
  concurrency caps, daily PR caps, issue-collision checks, and the circuit
  breaker.
- Eight preconditions before enabling, the first being that `/orca:verify` has
  been seen to **fail** on incomplete work — a gate that has only ever passed is
  untested.
- **Verified**: automation subcommands take a positional `<id>` (`show`, `edit`,
  `run`) except `runs`, which takes `--id`. The CLI is genuinely inconsistent
  here, so the file says so rather than assuming symmetry.

## 0.3.0 — 2026-07-31

**`/orca:handoff`** — hands a GitHub issue or an agreed plan to a fresh agent in
its own Orca worktree, then stops. Reads the issue and its `### Done when`
criteria, refuses to launch over work already in flight, derives the worktree
name, writes an executor contract outside the repo, creates the lane with the
issue linked natively, and reports the branch Orca actually derived.

The launch command itself lives in `_shared/orca-lanes.md`; this skill owns the
layer around it — what gets handed off, and what binds the executor.

Load-bearing details:

- **The contract goes outside the repo.** A new checkout cannot see another
  checkout's untracked files, but any absolute path is readable. The launch
  prompt stays a single pointer sentence so nothing multi-line has to survive
  shell quoting.
- **The issue's `### Done when` checklist is copied into the contract verbatim**,
  so the executor sees exactly the criteria `/orca:verify` will later apply. No
  checklist ⇒ the contract says so explicitly rather than letting the executor
  assume.
- **Never launch a second lane on an issue that already has one.** Checked
  against live worktrees (`linkedIssue`) and open PRs before creating anything.
- **The branch is read back, never predicted.** Orca derives
  `refs/heads/<user>/<name>` itself.
- **Draft PRs only**, and the executor is told never to mark its own PR ready —
  that waits on the evidence gate and a human.
- **A rejected `--agent claude` stops the run.** Silently substituting another
  agent is worse than failing.
- **The skill never monitors the lane it launches.** A full handoff that starts
  supervising is a different request, and Orca's bundled `orchestration` skill
  owns it.

**Honest gap:** the exact nesting of the worktree object inside the create
response is not documented by `orca agent-context`, which covers commands and
flags but not response shapes. Rather than assert a path verified only against a
transcript from an older Orca build, the skill reads the response defensively and
falls back to `orca worktree show`. Worth pinning down on the first real launch.

## 0.2.0 — 2026-07-31

First skill: **`/orca:migrate`**.

**Tracking model schema: v1.** This release establishes the versioned contract a
consuming repo is migrated *to*. The version is recorded in the repo's
`AGENTS.md` block as `<!-- orca-skills tracking model v1 -->`, and
`/orca:migrate` reads it to decide what a later run needs to do. **A schema bump
is not a plugin version bump** — most releases change no repo-side convention and
leave the schema alone.

**`/orca:migrate`** — brings a repo's tracking up to the model: inventories every
tracking file, classifies each *section* as live state / finished state /
narrative / reference, proposes milestones, issues with a `### Done when`
checklist, real dependency edges, spec files, file edits, and the `AGENTS.md`
block — then applies only what is approved. Nothing is written before approval,
and nothing is committed at all: file changes are left in the working tree so the
diff remains rejectable.

It handles three conditions, which **compose** rather than exclude each other:

| Condition | Cause |
|---|---|
| Never migrated | The model was never applied here |
| **Schema lag** | *The model moved* — a plugin release now expects something new |
| **Drift** | *The repo moved* — practice slipped away from the model |

A repo that is a version behind has usually also drifted, so both are always
evaluated and reported as one proposal with the two halves separated.

Design decisions worth recording:

- **Named `migrate`, not `adopt`.** "Adopt" implies a one-time onboarding. The
  model itself changes across releases, so a conforming repo can fall behind
  through no fault of its own — that is a migration, and it recurs.
- **The schema marker is a claim, not proof.** It records what a past run
  applied, not what is true now. A current marker never skips the drift audit.
- **Severe drift is not a fix-list.** When live work has moved back outside
  GitHub Issues, per-issue patching cannot restore the model; the skill re-runs
  its full inventory over the regressed parts instead.
- **Order is not negotiable**: labels and milestones, then issues, then
  dependencies, then specs, and only then file deletions. Never delete the only
  copy of something before its replacement exists.
- **Never fabricate acceptance criteria.** A thin issue honestly marked thin
  beats an invented checklist that would pass a gate which should have failed.
- **Gitignoring a tracked file is a no-op.** Untracking `ROADMAP.md` requires
  `git rm --cached` and therefore explicit consent; a tracked narrative roadmap
  is legitimate and stays if the user wants it.

**Also**

- `agents-fragment.md` now carries the schema marker in the fenced block, and
  documents why it is not decoration.

## 0.1.0 — 2026-07-31

Initial scaffold. No skills yet — this release is the plugin skeleton and the
shared specs every skill will read.

**Plugin**

- `.claude-plugin/marketplace.json` — the `orca-skills` catalog, one plugin.
- `plugins/orca/.claude-plugin/plugin.json` — plugin identity at `0.1.0`.

**Shared specs** (`plugins/orca/skills/_shared/`)

| File | What it fixes in place |
|---|---|
| `github-backlog.md` | Milestone resolution, the one-call readiness query, `gh` constraints and gotchas. App-agnostic — GitHub only. |
| `agents-fragment.md` | The block `/orca:migrate` appends to a consuming repo's `AGENTS.md`, including the issue-schema and generated-roadmap rules. |
| `issue-schema.md` | **New.** The `### Done when` contract all five skills read — and the three buckets (command / diff assertion / human) that make a criterion checkable. |
| `orca-lanes.md` | **New.** Orca's identity and selector model, native lane fields, deletion safety, degraded mode, and the proven handoff invocation. |
| `evidence-gates.md` | **New.** How `/orca:verify` checks a criterion: evidence rules, verdicts, and the prohibition on guessing at human criteria. |

**Docs** — `README.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `TRACKING.md`.

**Two facts verified live against `orca` 1.4.162** that would otherwise have
shipped as defects:

- **Repo `displayName` does not track the directory name.** `--repo
  name:<dir-name>` returns a hard `repo_not_found`, not an empty result. Every
  skill resolves repos by `path:` or `id:`. Found by checking rather than
  trusting a planning document — the rule that requires this caught it.
- **The worktree ID key differs between commands.** `worktree list --json`
  returns it as `id`; `worktree ps --json` returns the same value as
  `worktreeId`. Reading the wrong key yields `undefined` and degrades silently.

**Design notes**

- Scope is five skills — `migrate`, `handoff`, `status`, `verify`, `plan` — plus
  one disabled-by-default automation. An adversarial review panel cut an earlier
  8-skill proposal on the grounds that most were wrappers over capability Orca
  already has; `migrate` was added back because the other four consume a tracking
  convention that nothing else establishes.
- **Skills are app- and project-agnostic.** No skill names a project, milestone,
  label, or acceptance criterion. Project-specific conventions live in the
  consuming repo.
- **The roadmap is generated and gitignored** — a rendering of GitHub state, so
  it cannot conflict and cannot drift.
