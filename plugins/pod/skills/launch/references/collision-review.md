# Launching several issues — collision review first

`../SKILL.md` §1 sends you here when `$ARGUMENTS` names more than one issue, or
carries `--review`. Two issues can be independently ready and still edit the
same file; dependency edges cannot express that, so **comparing the finished
plans is the only place a collision shows before work starts.**

- `/pod:launch 84 85 86 87` — review, then launch the ones that do not collide.
- `/pod:launch --review 84 85 86 87` — review only; launch nothing.

## 1. Check the plans against each other

### Which plans are in scope

`/pod:plan` writes to `~/.claude/plans/<repo-name>/`, and **that directory
accumulates every plan ever written for the repo** — including ones that already
became lanes, and ones from waves weeks ago. A fresh context has no memory of
which issues *this* batch planned, so reading the directory is not the same as
reading this batch.

Scope it, in this order:

1. **Issue numbers in `$ARGUMENTS`** — the unambiguous form; prefer it and say
   so when the user omits them.
2. **The wave started in this conversation**, if there was one.
3. **Otherwise, infer and confirm.** Take the most recent plan files, exclude
   anything already in flight (below), present what you propose to review, and
   **ask before proceeding**. Never silently adopt every plan on disk.

### Exclude plans that already became lanes — always

**Before reviewing anything, drop plans whose work is already running.** This is
the step that stops a second wave re-proposing the first wave's issues:

```bash
orca worktree ps --limit 200 --json      # spans all repos — filter on repoId
gh pr list --state open --json number,headRefName,closingIssuesReferences
```

A plan is **not** a candidate when its issue has a live lane (`linkedIssue`
matching, `isMainWorktree == false`, same `repoId`), an open PR, or an assignee.
Say which plans were excluded and why — *"#84–#87 already have lanes; reviewing
the remaining 3"* — rather than dropping them silently, so the user can tell the
difference between "excluded" and "never found".

**Nothing left after exclusion** ⇒ say that plainly: every plan on disk is
already in flight, and there is nothing to review. That is a normal outcome
between waves, not an error.

If a plan is missing for an issue that *is* in scope, say which and treat that
issue as not ready.

Then check **every pair** for real overlap:

- **The same file modified by both.** The core check. Read each plan's Steps for
  named files and symbols.
- **The same subsystem or shared type**, even where the files differ — two plans
  changing one type's shape will conflict at merge even in separate files.
- **The same test baseline or fixture.**
- **An ordering the plans assume differently** — both assuming they land first.

**Repo-mandated shared files do not count.** A changelog or checklist every PR
touches is expected, and lanes resolve it at push time. Flag genuine
architectural overlap, not the file everyone edits by construction.

Report:

```
3 of 4 ready to launch.

  #84  ready
  #87  ready
  #85  ready
  #86  COLLIDES with #85 — both modify GameScene.swift and the
       overlay layout constants. Launch one, then re-plan the other
       against the merged result.
```

A collision is **not** a verdict that one plan is wrong. The usual resolution is
sequencing: launch one, let it merge, re-plan the other. Say that rather than
asking the user to pick a winner.

## 2. Launch the survivors

**Under `--review`, stop after §1 and launch nothing.** Otherwise continue,
only for plans with no unresolved collision: take each issue through
`../SKILL.md` §1–§5 in turn, exactly as a single launch.

**Re-check in-flight immediately before each launch**, not once at the top. §1's
exclusion may be minutes old, and in that time another wave, another session, or
the user by hand could have started a lane on the same issue. Skip anything that
gained a lane, PR, or assignee since — and say so, rather than launching a second
agent onto work already running.

`../SKILL.md` §1 refuses in-flight work itself, so this is a second net rather
than the only one. Two nets are right here: a duplicate lane means two agents opening
two competing PRs for one issue, which is expensive to notice and annoying to
unpick.

**Launch them one at a time, checking each result** — a failed launch (a
`kind: folder` repo, a name collision, an issue that went in-flight since planning)
must not silently take the rest of the batch with it. Report per issue: launched
with its branch, or skipped with the reason.

Never launch an issue that collided, unless the user explicitly overrides after
being told what the overlap is.

## Failure modes to avoid

- **Treating every plan on disk as in scope.** Scope by issue number, and always
  exclude work that already has a lane.
- **Checking in-flight once, at the top.** Re-check immediately before each
  launch.
- **Launching under `--review`.**
- **Treating a repo-mandated shared file as a collision.**
- **Reporting a collision as "one of these plans is wrong."** It is usually a
  sequencing problem.
- **Letting one failed launch abort the batch.**
