# orca-skills

Local Claude Code plugin marketplace holding all Orca-related skills in a single
plugin named `orca`. This repo contains only markdown and JSON — there is no
build step.

## Where things go

- New skills: `plugins/orca/skills/<skill-name>/SKILL.md` (folder + one file).
- Skills about maintaining *this repo* (not shipped to users) live in
  `.claude/skills/`:
  - **`/ship`** — cuts a GitHub release.
  - **`/audit-orca`** — re-verifies every `orca` CLI fact against the installed
    binary, checks whether Orca's bundled skills have started claiming trigger
    phrases that collide with `/orca:*`, and updates the version stamp. **Run it
    after every Orca upgrade** — the CLI moves independently, and nothing else
    here would notice a flag that vanished.
- Marketplace catalog: `.claude-plugin/marketplace.json` (repo root).
- Plugin identity/version: `plugins/orca/.claude-plugin/plugin.json`.
- Skills are invoked namespaced: `/orca:<skill-name>`.

## Skill-authoring rules

- The frontmatter `description` is the only thing Claude sees before deciding to
  load a skill — put all trigger phrases and "use when" contexts there, and make
  it pushy (skills undertrigger by default). Keep the body imperative.
- **Verify every `orca` CLI fact against live `orca <group> --help` before
  writing it into a skill — never from memory, never from a plan document.**
  This rule has caught real defects, including a repo selector that would have
  failed in every skill. Worktree IDs are `<repoId>::<absolute-path>`; note that
  `worktree list` returns it as `id` while `worktree ps` returns it as
  `worktreeId`.
- **Every skill states what it is NOT for, and names the bundled Orca skill that
  owns that case.** The namespace collides semantically with Orca's own
  `orca-cli` and `orchestration` skills — "use orca to hand this off" could route
  either way. Orca's bundled skills already disambiguate each other this way;
  match that.
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
- `_shared/agents-fragment.md` — the block `/orca:migrate` appends to a consuming
  repo's `AGENTS.md`. *(app-agnostic)*
- `_shared/issue-schema.md` — the `### Done when` contract every skill reads.
- `_shared/orca-lanes.md` — Orca identity, selectors, safety rules, the handoff
  invocation.
- `_shared/evidence-gates.md` — how a criterion is checked, and the four
  verdicts. Read by the lane's own self-gate (`launch/references/self-gate.md`),
  by `/orca:verify`, and by `/orca:status`, which greps for the verdict string.
  **The verdict vocabulary is lowercase** — `pass`, `pass-agent-judged`,
  `pass-with-review`, `fail` — and a fifth consumer that cannot match what a
  producer emits reports a gated PR as ungated.
- `_shared/automation.md` — the scheduled automation, shipped disabled, and the
  preconditions for enabling it. A config artifact, not a skill.

The first two are **app-agnostic**: they describe GitHub and the tracking model
only, with nothing Orca-specific in them. Plugins have no dependency mechanism,
so each plugin built on this model carries its own copy rather than referencing a
shared one. Both files say so in a header — keep any copies you maintain in sync.

Repetition elsewhere (the handoff invocation, "nothing ever merges") is
deliberate — an instruction present where it is needed cannot be missed.

## `/orca:tech-lead` is the one skill that composes the others

Every other skill is a leaf: it does its job and stops. `tech-lead` is the loop
over them, so it has rules the others do not.

- **It invokes, it never restates.** It calls `/orca:status` for the lane ×
  backlog join, `/orca:plan` for planning, `/orca:launch` for lanes. If you find
  yourself writing a contract template or a status query into it, stop — the
  skill exists. Its own listed failure modes say this; keep it true.
- **Its bounds are the design, not tuning knobs.** Three plan-review rounds, two
  fix rounds per PR, one rework per gate, two owner-only ticks before idling out,
  an eight-hour hard cap. Same lesson as 1.13.1 and 1.16.0: a reviewer loop with
  no termination rule always finds one more thing. Do not relax one without
  saying in the changelog what replaces it.
- **It never merges and never closes an issue.** No wording from a user unlocks
  it. This is the invariant the whole plugin exists to protect.
- **It has no flags.** Scope, cap, and steering are plain language; whether the
  user asked or told is what selects propose-vs-act. Do not add a flag to it —
  the interface *is* that reading.
- **Its `references/` are load-bearing, not overflow.** `expert-panel.md` (the
  roster, reviewer prompt, rounds, decision bar), `review-fix.md` (the only
  place in this plugin that reads PR review comments), `ledger-template.md` (the
  loop's memory, written outside the repo and never tracked).
- **Its defaults are defaults, not the user's config.** The roster and decision
  bar are overridden by a consuming repo's own `CLAUDE.md`, never by editing the
  reference file — a plugin update overwrites it. It carried two `TODO(user)`
  blocks as a personal skill; they were removed for exactly this reason. Do not
  reintroduce that shape.

**Its nearest collision is `/orca:status`**, which owns the read-only reading of
"what should I work on next". `tech-lead` claims that phrasing only when the user
wants it acted on. If you edit either description, re-check the other.

## How this repo itself works

**Commit straight to `main`.** No branches, no PRs, no lanes. This repo is
markdown and JSON with no runtime and no parallel work, so the lane workflow the
skills describe does not apply to it — a plugin repo cannot dogfood its own
skills. It is the one repo that opts out.

## After any skill edit

1. `claude plugin validate .` from the repo root.
2. Bump `version` in `plugins/orca/.claude-plugin/plugin.json`.
3. Add a `CHANGELOG.md` entry under the new version — what changed and why, per
   skill.
4. Check the docs for drift: `README.md`'s per-skill sections, flag table,
   pipeline diagram, workflow examples, the TOC, and the **skill count in the
   "The N skills" heading and its TOC anchor** — adding a skill changes a
   heading, a slug, and a link, and missing one leaves a dead anchor.
5. **Update `GUIDE.html` whenever `README.md` changes** — the visual version of
   the same content, gitignored, so it never shows up in a diff to remind you.
   Create it if missing. A guide that silently lags the README is worse than
   none, because it reads as current. Keep them in step: every skill, every
   flag, every workflow.

   **It is hand-authored HTML with its own design system** — CSS variables, a
   light/dark pair via both `prefers-color-scheme` and `:root[data-theme]`, and
   `.node` / `.skill` / `.flow` component classes. Do not regenerate it from the
   README mechanically; edit it, matching the existing markup, and reuse the
   classes rather than adding inline styles. Its prose is deliberately tighter
   than the README's, not a copy. Check the nesting after editing — an unclosed
   tag renders as a blank page.
6. Publish locally — local marketplaces do **not** auto-refresh, and the first
   command alone does NOT update the installed copy:

   ```bash
   claude plugin marketplace update orca-skills
   claude plugin update orca@orca-skills
   ```

   Changes apply to new sessions; existing ones need `/reload-plugins`.
