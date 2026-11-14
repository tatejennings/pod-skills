# pod-skills

Local Claude Code plugin marketplace holding a backlog-and-planning layer for the
Orca app in a single plugin named `pod` — a pod being what a group of orcas is
called. It is not made by the Orca team. This repo is markdown and JSON plus **one script**,
`plugins/pod/skills/status/scripts/status.py` (Python 3, standard library only) — there is no
build step.

## Where things go

- New skills: `plugins/pod/skills/<skill-name>/SKILL.md` (folder + one file).
- Skills about maintaining *this repo* (not shipped to users) live in
  `.claude/skills/`:
  - **`/ship`** — cuts a GitHub release.
  - **`/audit-orca`** — re-verifies every `orca` CLI fact against the installed
    binary, checks whether Orca's bundled skills have started claiming trigger
    phrases that collide with `/pod:*`, and updates the version stamp. **Run it
    after every Orca upgrade** — the CLI moves independently, and nothing else
    here would notice a flag that vanished.
  - **`/audit-claude-code`** — re-checks the Claude Code facts the skills
    assert (tool names, `$ARGUMENTS`, `/loop`, plan mode) against the running
    harness and the docs, and proposes new features worth adopting. **Run it
    after Claude Code upgrades.** Kept apart from `/audit-orca` because the two
    upgrade on unrelated schedules.
    Last audited against Claude Code **2.1.318**, 2026-11-14.
- Marketplace catalog: `.claude-plugin/marketplace.json` (repo root).
- Plugin identity/version: `plugins/pod/.claude-plugin/plugin.json`.
- Skills are invoked namespaced: `/pod:<skill-name>`.

## Skill-authoring rules

- The frontmatter `description` is the only thing Claude sees before deciding to
  load a skill — put all trigger phrases and "use when" contexts there, and make
  it pushy (skills undertrigger by default). Keep the body imperative.
  **Write it as a `description: >-` block and keep it under 1,536 characters.**
  Unquoted, ` #84` starts a YAML comment and silently drops the rest; past
  1,536 the skill listing truncates it. Both cut the "not for" sentences first,
  since they come last.
- **Verify every `orca` CLI fact against live `orca <group> --help` before
  writing it into a skill — never from memory, never from a plan document.**
  This rule has caught real defects, including a repo selector that would have
  failed in every skill. Worktree IDs are `<repoId>::<absolute-path>`; note that
  `worktree list` returns it as `id` while `worktree ps` returns it as
  `worktreeId`.
- **Every skill states what it is NOT for, and names the bundled Orca skill that
  owns that case.** These skills sit on top of the Orca app, so their *subject*
  overlaps with Orca's own `orca-cli` and `orchestration` skills — "hand this off
  in Orca" could route either way. (The plugin was named `orca` until 2.0.0, when
  the namespace itself collided too; `pod` fixed the name, not the overlap.)
  Orca's bundled skills already disambiguate each other this way; match that.
- **Skills are app- and project-agnostic.** No skill references a specific
  project, game, milestone name, label, or acceptance criterion. Project-specific
  conventions live in the consuming repo, not here. If a skill needs a repo's
  convention, it reads it from that repo or takes it as an argument.
- Keep SKILL.md under ~500 lines; overflow goes in a `references/` subfolder with
  clear pointers from the body.

## Shared specs live in `_shared/`, not in copies

Six files are read by several skills and are dangerous when they drift. Change
the shared file, not a skill's restatement of it:

- `_shared/github-backlog.md` — milestone resolution, the readiness query, `gh`
  constraints. *(app-agnostic: GitHub only, nothing Orca-specific)*
- `_shared/agents-fragment.md` — the block `/pod:migrate` appends to a consuming
  repo's `AGENTS.md`. *(app-agnostic)*
- `_shared/issue-schema.md` — the `### Acceptance criteria` contract every skill
  reads. **`### Done when` is its former name and still reads everywhere** —
  every consumer accepts both, because a heading a skill cannot find reads as *no
  criteria*, which silently disables the gate. Write the new name; never make a
  reader strict.
- `_shared/orca-lanes.md` — Orca identity, selectors, safety rules, the handoff
  invocation.
- `_shared/evidence-gates.md` — how a criterion is checked, and the four
  verdicts. Read by the gate prompt every lane and `/pod:verify` run (`launch/references/gate-prompt.md`),
  by `/pod:verify`, and by `/pod:status`, which greps for the verdict string.
  **The verdict casing is part of the contract**: UPPERCASE (`PASS`, `FAIL`, …)
  is the literal string on the wire that consumers grep for; lowercase is only
  the verdict's *name* in prose. Do not "tidy" one into the other — a consumer
  that cannot match what a producer emits reports a gated PR as ungated.
- `_shared/automation.md` — the scheduled automation, shipped disabled, and the
  preconditions for enabling it. A config artifact, not a skill.

The first two are **app-agnostic**: they describe GitHub and the tracking model
only, with nothing Orca-specific in them. Plugins have no dependency mechanism,
so each plugin built on this model carries its own copy rather than referencing a
shared one. Both files say so in a header — keep any copies you maintain in sync.

Repetition elsewhere (the handoff invocation, "nothing ever merges") is
deliberate — an instruction present where it is needed cannot be missed.

## Mechanical work is copied or scripted, never retyped

Three things in this plugin are deterministic, and an agent re-deriving them
each run is slower and drifts (3.0.0):

- **The status join** is `status/scripts/status.py`. The skill runs it and
  prints its output; `status/references/manual-join.md` is the same procedure in
  prose, for when the script cannot run. **Change them together.** The script
  holds `orca` and `gh` facts, so `/audit-orca` covers it.
- **The executor's working rules and the gate prompt** are
  `launch/references/executor-steps.md` and `gate-prompt.md`, copied with `cp`
  beside each contract. Never have a skill paste or paraphrase them.
- **There is one gate prompt.** The lane's self-gate, `/pod:verify`, and a
  review-fix round all hand `gate-prompt.md` to a fresh agent. Do not write a
  second gate procedure into a skill.

## `/pod:tech-lead` is the one skill that composes the others

Every other skill is a leaf: it does its job and stops. `tech-lead` is the loop
over them, so it has rules the others do not.

- **It invokes, it never restates.** It runs the status script for the lane ×
  backlog join, `/pod:plan` for planning, `/pod:launch` for lanes. If you find
  yourself writing a contract template or a status query into it, stop — the
  skill exists. Its own listed failure modes say this; keep it true.
- **Its bounds are the design, not tuning knobs.** Two plan-review rounds at most
  (one by default, 3.0.0), two fix rounds per PR, one rework per gate, two owner-only ticks before idling out,
  an eight-hour hard cap. Same lesson as 1.13.1 and 1.16.0: a reviewer loop with
  no termination rule always finds one more thing. Do not relax one without
  saying in the changelog what replaces it.
- **It never merges and never closes an issue.** No wording from a user unlocks
  it. This is the invariant the whole plugin exists to protect.
- **It has no flags.** Scope, cap, and steering are plain language; whether the
  user asked or told is what selects propose-vs-act. Do not add a flag to it —
  the interface *is* that reading. **Bare `/pod:tech-lead` is a tell** (2.2.0):
  the standing order — active milestone, cap 3, propose and go. Only *words*
  that could read either way fall to propose-and-wait.
- **Its `references/` are load-bearing, not overflow.** `seats.md` (the roster
  of specialist personas — product, requirements, architecture, test, UX,
  security, domain — each lens, when it is convened, and the rule that seats
  advise and never act), `expert-panel.md` (the reviewer prompt, rounds,
  decision bar), `review-fix.md` (the only place in this plugin that reads PR
  review comments), `ledger-template.md` (the loop's memory, written outside the
  repo and never tracked).
- **Its specialists are seats, not skills.** A persona — PM, QA, art director,
  security reviewer — is a row in `references/seats.md` that the tech lead
  convenes as a fresh advisor for one question, and then decides on itself under
  the bar. Do not add `/pod:<persona>` skills: they collide with `triage`,
  `status`, `verify` and `tech-lead` in routing, and each is a second composer
  needing its own bounds and ledger. QA is `/pod:verify`; grooming is
  `/pod:triage`. Seats never edit, comment, launch, or write the ledger. Bounds
  here are also design: one product-seat round on the slate; three core seats
  always; five seats per plan round at most.
- **Its defaults are defaults, not the user's config.** The roster and decision
  bar are overridden by a consuming repo's own `CLAUDE.md`, never by editing the
  reference file — a plugin update overwrites it. It carried two `TODO(user)`
  blocks as a personal skill; they were removed for exactly this reason. Do not
  reintroduce that shape.

**Its nearest collision is `/pod:status`**, which owns the read-only reading of
"what should I work on next". `tech-lead` claims that phrasing only when the user
wants it acted on. If you edit either description, re-check the other.

## How this repo itself works

**Commit straight to `main`.** No branches, no PRs, no lanes. This repo is
markdown, JSON and one script, with no parallel work, so the lane workflow the
skills describe does not apply to it — a plugin repo cannot dogfood its own
skills. It is the one repo that opts out.

## After any skill edit

1. `claude plugin validate .` from the repo root.
2. Bump `version` in `plugins/pod/.claude-plugin/plugin.json`.
3. Add a `CHANGELOG.md` entry under the new version — what changed and why, per
   skill.
4. Check the docs for drift: `README.md`'s per-skill sections, flag table,
   pipeline diagram, workflow examples, the TOC, and the **skill count in the
   "The N skills" heading and its TOC anchor** — adding a skill changes a
   heading, a slug, and a link, and missing one leaves a dead anchor.
5. Publish locally — local marketplaces do **not** auto-refresh, and the first
   command alone does NOT update the installed copy:

   ```bash
   claude plugin marketplace update pod-skills
   claude plugin update pod@pod-skills
   ```

   Changes apply to new sessions; existing ones need `/reload-plugins`.
