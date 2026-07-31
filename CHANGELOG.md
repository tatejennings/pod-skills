# Changelog

Notable changes to the `orca` plugin. Versions track
`plugins/orca/.claude-plugin/plugin.json`.

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
