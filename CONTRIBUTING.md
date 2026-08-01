# Contributing

## How this repo works — it commits straight to `main`

**No branches, no PRs, no lanes.** This repo is markdown and JSON with no
runtime, no tests, and no parallel work. The plan → handoff → verify → merge lane
workflow these skills describe is for the *consuming* projects they are pointed
at, not for the plugin itself.

Do not read the pipeline in [README.md](README.md) as instructions for working
here. It is the one repo that opts out. A plugin repo cannot dogfood its own
skills: there is nothing to build, nothing to verify, and one author.

## Adding or editing a skill

Each skill is a folder with one file: `plugins/orca/skills/<name>/SKILL.md`, with
`name` + `description` frontmatter. The description is the triggering mechanism —
every "when to use" phrase belongs there, not in the body.

Three rules that are not optional:

**Verify every `orca` CLI fact against live `orca <group> --help`**, never from
memory and never from a plan document. This has caught real defects. Worktree IDs
are `<repoId>::<absolute-path>` — and `worktree list` returns that under `id`
while `worktree ps` returns it under `worktreeId`.

**Say what the skill is NOT for.** The `/orca:*` namespace collides semantically
with Orca's bundled `orca-cli` and `orchestration` skills. Every description
names the bundled skill that owns the case it declines, the way Orca's own skills
disambiguate each other.

**Stay project-agnostic.** No skill references a specific project, game,
milestone name, label, or acceptance criterion. Those belong to the consuming
repo. A skill needing a convention reads it from the repo or takes it as an
argument.

## Shared specs live in `_shared/`, not in copies

- `_shared/github-backlog.md` — milestone resolution, readiness, `gh` constraints
- `_shared/agents-fragment.md` — the block `/orca:migrate` appends to a repo
- `_shared/issue-schema.md` — the `### Done when` contract
- `_shared/orca-lanes.md` — Orca identity, selectors, safety, the handoff command
- `_shared/evidence-gates.md` — how `/orca:verify` checks a criterion
- `_shared/automation.md` — the disabled-by-default scheduled automation

Change the shared file, not a skill's restatement of it.

**The first two are app-agnostic by design** — GitHub and the tracking model
only, with nothing Orca-specific in them. Plugins have no dependency mechanism,
so each plugin built on this model carries its own copy rather than referencing a
shared one. Both files say so in a header; if you maintain such a copy elsewhere,
keep the two in sync rather than letting them diverge silently.

## Testing a change without installing

```bash
claude --plugin-dir ./plugins/orca   # overrides the installed copy for that session
```

## After any skill edit

1. `claude plugin validate .` from the repo root.
2. Bump `version` in `plugins/orca/.claude-plugin/plugin.json`.
3. Add a `CHANGELOG.md` entry under that version.
4. Check `README.md` (skills table, flag table, pipeline) for drift.
5. **Regenerate `GUIDE.html` if `README.md` changed** — the visual guide is
   generated from it and gitignored, so nothing in a diff will remind you.
   Create it if absent; a guide that lags the README reads as current and is
   worse than none.
6. Publish locally — local marketplaces do not auto-refresh, and the first
   command alone does **not** update the installed copy:

   ```bash
   claude plugin marketplace update orca-skills
   claude plugin update orca@orca-skills
   ```

   Changes apply to new sessions; existing ones need `/reload-plugins`.

## Releasing

`/ship` — a project-level skill in `.claude/skills/`. It verifies the version,
changelog, README, and git state agree, then pushes, tags `v<version>`, and
creates a GitHub release with notes from the changelog entry.
