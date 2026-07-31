# GitHub backlog queries — shared by every skill that reads or writes issues

One spec, many consumers: `adopt`, `plan`, `status`, `verify`, `handoff`.
**Do not copy these queries into a skill** — a copy is where drift starts.
Point at this file.

> **This file is app-agnostic** — nothing in it is specific to Orca, or to any
> project the skills are pointed at. It describes GitHub and `gh` only, so it is
> portable to any plugin built on the same tracking model. Claude Code plugins
> have no dependency mechanism, so each plugin carries its own copy rather than
> referencing a shared one; if you maintain such a copy elsewhere, a fix here
> belongs there too.

Verified against `gh` 2.96.0, 2026-07-31. Floor is `gh` 2.94.0, the release that
added dependencies, sub-issues, and issue types.

## The tracked-progress-file guard

**Never write progress, status, or completion into a tracked file.** Before any
edit that would record *what is done* — a roadmap row, a status-board cell, a
"mark this complete" checkbox — check whether the target is tracked:

```bash
git ls-files --error-unmatch <path> 2>/dev/null && echo TRACKED
```

If tracked, **refuse that write** and say why: parallel lanes each edit it, every
PR conflicts, and a "keep only your lane's rows" resolution silently discards
another lane's progress. Completion is recorded by `Closes #<n>` on merge.

Two things this guard is **not**:

- It is not a check on filenames. A tracked `ROADMAP.md` is perfectly legitimate
  as human-authored narrative — plenty of repos should have one. Guard the
  *write*, not the file's existence, and never refuse to run because such a file
  is present. (`/orca:adopt` is the one skill that *proposes* changing such a
  file's status, and it proposes rather than acting.)
- It is not a reason to stop the whole task. Refuse the one write, explain, and
  continue with everything else. If a repo's own `CLAUDE.md` mandates the edit,
  surface that as a conflict for the user to resolve — do not quietly comply, and
  do not quietly ignore it either.

Reading these files is always fine; they are a legitimate fallback source when a
repo has no GitHub backlog.

## Before any write

```bash
gh auth status
```

`gh` can hold several authenticated accounts with only one **active**, and the
active one is whichever was selected last — frequently the wrong one for a
personal project. If the active account cannot push to the resolved repo, stop
and say so; do not file under the wrong identity. Repo resolution comes from the
git remote (`gh repo view --json nameWithOwner -q .nameWithOwner`), so it works
from any worktree — but the *account* does not follow the repo.

## Active milestone resolution

In this order:

1. **The open milestone with the nearest `due_on`.**
2. If no open milestone has a due date and there is exactly **one** open
   milestone, use it.
3. Otherwise **ask** — never guess. Picking wrong points a whole session at the
   wrong release.

```bash
gh api "repos/{owner}/{repo}/milestones?state=open" \
  --jq 'sort_by(.due_on // "9999") | .[] |
        "\(.number)\t\(.title)\t\(.due_on // "no due date")\t\(.closed_issues)/\(.open_issues + .closed_issues)"'
```

`{owner}`/`{repo}` are placeholders `gh api` fills from the current repo — pass
them literally. The last column is milestone progress (closed/total), which is
what a dashboard header should show.

## Readiness query — one call

An issue is **ready** when it is open, in the active milestone, and has no
unresolved `blocked-by`. Everything needed comes back in a single request:

```bash
gh issue list --state open --limit 200 \
  --json number,title,milestone,labels,blockedBy,blocking
```

Then, in the caller:

- keep issues whose `.milestone.title` is the active milestone;
- **ready** = no unresolved blocker (see below);
- **blocked** = anything else — report *what* blocks it, since that is the
  actionable part.

**The `blockedBy` shape.** Verified: it returns
`{"nodes": [...], "totalCount": N}`, and `totalCount` is `0` with an empty
`nodes` array when nothing blocks the issue. That is enough for the common case:
`totalCount == 0` ⇒ ready.

What is **not** yet verified on live data is whether `nodes` entries carry a
`state`, and therefore whether `totalCount` counts *closed* blockers too. It
almost certainly does — GitHub keeps the relationship after the blocker closes.
So treat `totalCount > 0` as "inspect further, not automatically blocked":

```bash
# For the few issues with totalCount > 0, resolve the blockers' real state:
gh issue view <blocker-number> --json number,state,title
```

An issue whose every blocker is `CLOSED` is **ready**. Confirm the node shape
the first time this runs against a repo with a real dependency, and if `nodes`
does expose `state`, simplify to a single pass over the list output and update
this file.

Do not fan out to `gh issue view` per issue. It works, but it is one request per
issue, and `/orca:status` is designed to be safe under `/loop 15m`.

### Writing dependencies

```bash
gh issue edit <blocked> --add-blocked-by <blocker>
gh issue create --blocked-by <n>,<n> --blocking <n>
```

This is the mechanism readiness reads. A priority *label* changes nothing about
what gets picked up — if a blocking relationship matters, record it here. A
`blocked` label with no corresponding edge is decorative: every readiness query
will call that issue ready, which is the honest reading of the data.

## Constraints

**Use labels, not issue types.** `--type` exists but issue types are configured
at the **organization** level, so personal-account repos cannot use them. Never
emit `--type`. Create a missing label once:

```bash
gh label create <name> --description "<what it means>" --force
```

**Do not build readiness on sub-issues.** `parent`, `subIssues`, and
`subIssuesSummary` are available on `gh issue list --json`, but sub-issue
behavior is inconsistent on personal repos. The contract is **milestone
membership plus dependencies**; treat hierarchy as display-only enrichment when
present.

**Idempotency by label.** Every issue created from a spec carries
`spec:<slug>`. Before creating, list existing issues with that label and diff by
title, so a second run creates nothing:

```bash
gh issue list --state all --label "spec:<slug>" --json number,title
```

**Milestones have no `gh` subcommand.** There is no `gh milestone`. Use the API;
adding parameters switches the method to POST automatically:

```bash
gh api repos/{owner}/{repo}/milestones -f title="<name>" -f due_on="<ISO-8601>"
```

Omit `due_on` rather than inventing a date — but note that a milestone with no
due date cannot win the nearest-due-date rule above.

**Multi-line bodies go through stdin**, never a shell argument:

```bash
gh issue create --title "<t>" --body-file - <<'EOF'
<body>
EOF
```

`--body "…"` is where quoting breaks and half a body gets eaten.

## Verifying `--json` fields

When checking whether a field exists, ask for a bogus one — `gh` then enumerates
every valid field:

```bash
gh issue list --json nope
```

Do **not** grep a filtered field list and conclude a field is absent, and do not
test on a repo with no issues: an empty repo returns `[]` with exit 0, which is
indistinguishable from an unsupported field. This exact mistake produced a wrong
claim in the sibling plugin's own docs.
