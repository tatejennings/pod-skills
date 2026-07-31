---
name: ship
description: Cut a release of this plugin marketplace - verifies the plugin version, CHANGELOG entry, README, and git state all agree, then commits any pending work, pushes, tags the version, and creates a GitHub release whose notes come from the changelog entry. Use when the user says "/ship", "ship it", "cut a release", "publish a release", "tag and release", or asks to get the latest plugin changes onto GitHub.
---

# Ship a release

Release the `orca` plugin: prove the repo is internally consistent, then tag it
and publish a GitHub release. The version in
`plugins/orca/.claude-plugin/plugin.json` is the single source of truth — the git
tag and release name follow it, never the other way around.

Nothing here merges or force-pushes, and every check that fails stops the ship
with an explanation rather than "fixing" things silently.

## 1. Preflight — all must pass

Report exactly what failed and stop if any check fails.

1. **Repo root:** you are in the marketplace repo
   (`.claude-plugin/marketplace.json` exists). Read `<version>` from
   `plugins/orca/.claude-plugin/plugin.json`.
2. **Changelog current:** `CHANGELOG.md` has a `## <version>` section at the top.
   Missing ⇒ stop and tell the user what is unreleased — offer to draft the entry
   from the commits since the last tag, but let them approve the wording;
   changelog prose is theirs.
3. **Version is new:** no existing git tag `v<version>` (`git tag -l`), and no
   published release with that tag if a remote exists. Already shipped ⇒ stop;
   the fix is a version bump, not a retag.
4. **Skills validate:** `claude plugin validate .` passes.
5. **Changelog covers the work:** compare `git log <last-tag>..HEAD --oneline`
   (or all commits, if no tag yet) against the top changelog section. Any skill
   change with no corresponding changelog line ⇒ stop and list the gaps.
   Docs-only commits (README, CLAUDE.md, this skill) need no entry.
6. **Docs not stale:** if commits since the last tag touched
   `plugins/orca/skills/`, confirm `README.md`'s skills table and pipeline
   diagram reflect them. Drift ⇒ stop and say precisely what looks out of date.
   (Same check CLAUDE.md requires after any skill edit.)

## 2. Commit pending work

This repo commits straight to `main` — no branch, no PR (see CONTRIBUTING.md).

If `git status --porcelain` is non-empty, show the user what is uncommitted and
commit it with a message describing the change (not "prepare release" — say what
actually changed). Never commit `CLAUDE.local.md` or anything else gitignored; if
something unexpected is staged, stop and ask.

## 3. Push

`git remote -v`. If there is no `origin`:

- Ask the user first — creating a **public** repo publishes everything, including
  full history. Confirm the intended name and visibility.
- On approval: `gh repo create <name> --source=. --remote=origin --push` with
  `--public` or `--private` as they chose.
- Then verify the pushed content is what they expect (`gh repo view --web` is a
  fine pointer) before continuing.

If `origin` exists: `git push` (and `git push --set-upstream origin <branch>` the
first time). Never force-push.

## 4. Tag and release

```bash
git tag -a v<version> -m "v<version>"
git push origin v<version>
gh release create v<version> --title "v<version>" --notes-file <notes-file> --verify-tag
```

Build `<notes-file>` in the scratchpad from the changelog's `## <version>`
section — its bullets verbatim, since they already describe the release. Above
them add one plain-language sentence naming what a user gets from this version,
and below them a short install/upgrade line:

    Existing installs: `claude plugin update orca@orca-skills`
    (new installs: see the README).

`--verify-tag` is deliberate: it aborts if the tag never reached the remote, so a
release cannot point at a tag nobody can fetch.

## 5. Report

Release URL, tag, version, the changelog bullets shipped, and anything the
preflight let through with a warning. Remind the user that installed plugins
still need `claude plugin update orca@orca-skills` — a GitHub release does not
reach their machine by itself.
