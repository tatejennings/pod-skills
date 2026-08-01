# orca-skills

Local Claude Code plugin marketplace holding all Orca-related skills in a single
plugin named `orca`. This repo contains only markdown and JSON — there is no
build step.

## Where things go

- New skills: `plugins/orca/skills/<skill-name>/SKILL.md` (folder + one file).
- Skills about maintaining *this repo* (not shipped to users) live in
  `.claude/skills/` — e.g. `/ship`, which cuts a GitHub release.
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

Five files are read by several skills and are dangerous when they drift. Change
the shared file, not a skill's restatement of it:

- `_shared/github-backlog.md` — milestone resolution, the readiness query, `gh`
  constraints. *(app-agnostic: GitHub only, nothing Orca-specific)*
- `_shared/agents-fragment.md` — the block `/orca:migrate` appends to a consuming
  repo's `AGENTS.md`. *(app-agnostic)*
- `_shared/issue-schema.md` — the `### Done when` contract all five skills read.
- `_shared/orca-lanes.md` — Orca identity, selectors, safety rules, the handoff
  invocation.
- `_shared/evidence-gates.md` — how `/orca:verify` checks a criterion.
- `_shared/automation.md` — the scheduled automation, shipped disabled, and the
  preconditions for enabling it. A config artifact, not a skill.

The first two are **app-agnostic**: they describe GitHub and the tracking model
only, with nothing Orca-specific in them. Plugins have no dependency mechanism,
so each plugin built on this model carries its own copy rather than referencing a
shared one. Both files say so in a header — keep any copies you maintain in sync.

Repetition elsewhere (the handoff invocation, "nothing ever merges") is
deliberate — an instruction present where it is needed cannot be missed.

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
4. Check the docs for drift: `README.md`'s skills table, flag table, and pipeline
   diagram.
5. **Regenerate `GUIDE.html` whenever `README.md` changes** — it is the visual
   version of the same content (gitignored, so it never shows up in a diff to
   remind you). Create it if it is missing. A guide that silently lags the README
   is worse than none, because it reads as current. Keep them in step: every
   skill, every flag, every workflow.
6. Publish locally — local marketplaces do **not** auto-refresh, and the first
   command alone does NOT update the installed copy:

   ```bash
   claude plugin marketplace update orca-skills
   claude plugin update orca@orca-skills
   ```

   Changes apply to new sessions; existing ones need `/reload-plugins`.
