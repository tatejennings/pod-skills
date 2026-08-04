---
name: status
description: Dashboard joining Orca's lane state against the GitHub backlog - every worktree's branch, issue, PR state, session liveness and a verdict saying what needs attention, plus active-milestone progress and a READY NEXT list of unblocked issues, which makes this the answer to "what should I work on next". Also regenerates the gitignored ROADMAP.md from GitHub state on every run, so the rendering never goes stale; --no-roadmap suppresses that. With --reap it deletes provably-finished lanes after strict safety checks. Non-interactive and conservative by construction, so looping it is safe. Use when the user says "/orca:status", "/orca:status --reap", "what should I work on next", "what's ready", "what's blocked", "what's left in this milestone", "how are the lanes doing", "status of my worktrees", "any lanes to clean up", "reap merged worktrees", "regenerate the roadmap", or sets up "/loop 15m /orca:status". For driving the Orca app - creating worktrees, running terminals - use Orca's bundled orca-cli skill instead; apart from the roadmap file and the narrowly-scoped --reap deletion, this skill only reads.
---

# Status

Report the state of this repo's work, joined from two sources that each know
half of it:

- **Orca** knows lanes — branch, linked issue/PR, liveness, lineage. One call.
- **GitHub** knows the backlog — milestones, readiness, dependencies, PR state.

Neither is complete alone, and **that join is this skill.** Everything is derived
on each run; nothing is cached and no stored state is trusted over what
Orca/`git`/`gh` say right now.

Read `../_shared/orca-lanes.md` for the Orca model and `../_shared/github-backlog.md`
for every `gh` query. Do not restate them.

## What this skill is not for

- **Creating or driving worktrees and terminals** ⇒ Orca's bundled `orca-cli`
  skill. This skill reads; its only write is the narrow `--reap` deletion.
- **Watching a specific agent or waiting on it** ⇒ Orca's `orchestration` skill.
- **Deciding how to do a piece of work** ⇒ `/orca:plan`.

## Flags

**`ROADMAP.md` is regenerated on every run** (§7) — it is a derived, gitignored
rendering, so keeping it fresh is the point. `--no-roadmap` suppresses it.

`$ARGUMENTS` may contain:

- `--reap` — delete provably-finished lanes (§8). Strictly non-interactive:
  every ambiguous case is reported, never deleted, never prompted.
- `--no-roadmap` — skip the roadmap write; report only.

The roadmap write is the **only** thing a bare run writes, and §7's guards mean
it never touches a tracked file or a repo with no backlog. Everything else here
is read-only, which is what keeps `/loop 15m /orca:status` safe.

## 0. Preconditions and degraded mode

```bash
command -v orca && orca status --json     # result.runtime.reachable
gh auth status
```

**This skill degrades honestly rather than failing whole** — see
`../_shared/orca-lanes.md`:

- **Orca missing/unreachable** ⇒ run the backlog half (§5, §6, §7) and report the
  lane half as unavailable, naming why. Milestones and readiness are pure `gh`.
- **`gh` unavailable or no GitHub remote** ⇒ run the lane half (§2) and report the
  backlog half as unavailable.
- **Both** ⇒ say so and stop.

Never present a partial report as complete, and never silently omit a half.

## 1. Resolve the repo

Resolve by **path, never by name** — `displayName` is user-editable and often
does not match the directory:

```bash
orca worktree current --json      # cwd → path: selector, and the repoId
```

Take the `repoId` from that result. Everything in §2 filters on it.

## 2. Lanes — one call

```bash
orca worktree ps --limit 200 --json
```

**Pass `--limit` explicitly.** The default row cap is unspecified, and a silent
truncation would under-report lanes *and* drop the primary checkout this step
needs below.

**Before filtering, record the primary checkout's path** — the entry for this
`repoId` with `isMainWorktree: true`. You cannot read it afterwards, because the
lane filter removes it, and `orca worktree current` returns the *lane's* path
when this skill runs from inside one.

Then keep worktrees where `repoId` matches **and `isMainWorktree` is false**.
Never use a path prefix (`../_shared/orca-lanes.md`).

**That pair is necessary but not sufficient.** A repo registered as
`kind: folder` can hold a workspace entry with `isMainWorktree: false` whose
`path` is the *primary checkout* — verified live. Also drop any entry whose `path` equals the primary
checkout's path: it is not an isolated lane, and rendering it as one implies work
is happening somewhere it is not. Report such entries separately, in one line, as
non-isolated workspace entries rather than silently hiding them.

`worktree ps` already returns branch, `linkedIssue`, `linkedPR`,
`workspaceStatus`, `liveTerminalCount`, `agents[].state`, and `lastActivityAt`.
**Do not fan out per-lane commands to rebuild those.**

Two facts it does *not* carry, needed only for lanes that might be reapable or
that look finished — fetch per lane, and only for those:

```bash
git -C <path> status --porcelain          # dirty?
git -C <path> rev-parse HEAD              # for the headRefOid comparison
```

Isolate errors per lane: a lane whose commands fail gets verdict `unknown` and
the table still renders. One broken lane must not abort the report.

**Short-circuit:** no lanes and no GitHub remote ⇒ report "no lanes" and stop
without touching the network. That is the common case for a looped run on an idle
repo.

## 3. PR state — one call

`linkedPR` is a *number*, not a status, so resolve state from GitHub once for the
whole repo and join locally by branch:

```bash
gh pr list --state all --limit 100 \
  --json number,state,isDraft,headRefName,headRefOid,mergedAt,url,\
closingIssuesReferences,mergeable,mergeStateStatus,statusCheckRollup,updatedAt
```

The last four cost nothing extra — they come back in the same request — and each
answers a question the dashboard otherwise cannot:

- **`mergeable: CONFLICTING`** ⇒ the lane will not land as-is. Report it; a
  conflicted PR that looks healthy is how a lane sits for a week.
- **`statusCheckRollup`** ⇒ CI state. **This gate is not CI**, and a `pass` from
  `/orca:verify` says nothing about it — showing both side by side is what stops
  someone reading a passing gate as a green light.
- **`updatedAt`** ⇒ how long a PR has been waiting on a human.

`closingIssuesReferences` costs nothing extra here and gives each lane its issue
without a per-lane query — which is what keeps this skill safe under `/loop 15m`.

If a branch has several PRs, prefer the open one, else the most recently updated.

**Lanes open normal PRs, not drafts** — automated review tooling skips drafts,
so a draft PR would mean no review happens at all. `isDraft` therefore no longer
tells you whether the gate has run.

**The gate verdict is a PR comment**, so read comments for open PRs only — one
extra call, and only for the handful of lanes that have an open PR:

```bash
gh pr view <n> --json comments --jq '[.comments[].body] | map(select(test("orca:verify|PASS|PASS-WITH-REVIEW|FAIL")))| last'
```

A PR with no verdict comment is **ungated**, however ready it looks. That is the
distinction `isDraft` used to carry, and it is now the only one — an open PR
proves work was pushed, nothing more.

## 4. Verdicts

Exactly one per lane:

| Verdict | Condition |
|---|---|
| `working` | agents active or terminals live; PR absent |
| `awaiting-gate` | a PR is open, no agent is active, and no gate verdict is on it — ready for `/orca:verify` |
| `pr-open` | a PR is open and a gate verdict has been posted |
| `merged-reapable` | PR merged + clean + `HEAD == headRefOid` + no live terminals |
| `merged-live` | PR merged + clean + `HEAD == headRefOid` + terminals still live |
| `stalled` | no live terminals, no open PR |
| `needs-attention` | anything contradictory (see below) |

Resolution order:

1. **`needs-attention` wins over everything.** A contradictory lane is never
   reported healthy and never reaped. It covers: dirty tree on a merged PR,
   detached HEAD, merged PR whose `HEAD != headRefOid`, and derivation errors
   (`unknown`).
2. `awaiting-gate` beats `working` when no agent is active — that is the lane
   asking for `/orca:verify`, and it is the state this pipeline is built around.
3. `pr-open` beats `working` — the PR supersedes; the session is just waiting.

Notes: `HEAD != headRefOid` only counts as contradictory on a **merged** PR
(post-merge commits a deletion would lose). On an open PR it is ordinary unpushed
work. `stalled` means abandoned mid-flight; commit age alone never triggers it.

## 5. Backlog — milestone progress and READY NEXT

Only when the repo has a GitHub remote, and skipped entirely if §2
short-circuited. Two calls, per `../_shared/github-backlog.md`: resolve the
active milestone, then one `gh issue list`.

Header above the table:

```
v0.3 — Audio pass    4/11 closed    (due 2026-08-15)
```

Then, below the lanes:

```
READY NEXT
  #52  Footstep surfaces          ready
  #53  Reverb zones               ready
  #55  Mixer ducking              blocked by #52
```

- **Exclude issues already covered by a live lane or an open PR** — those are in
  flight, not ready.
- **Exclude `manual` issues** — they get their own section below
  (`../_shared/issue-schema.md`). They are ready, but not lane work.
- Show blocked issues **with their blockers, by number and title** — `blockedBy.nodes`
  already carries both, so it costs nothing. An issue is blocked only when some
  blocker is still `OPEN`; a non-zero `totalCount` whose blockers have all closed
  is **ready** (`../_shared/github-backlog.md`).
- Cap at ~8 and say how many more there are.
- **Flag issues with no `### Done when` checklist** — they cannot be gated by
  `/orca:verify`, so mark them `(no criteria)` and point at `/orca:plan` or
  `/orca:migrate`.
- Nothing ready and nothing blocked ⇒ one line pointing at `/orca:migrate`
  (audit the backlog) or `/orca:plan` (nothing is filed yet).

### YOUR TASKS — the `manual` section

Unblocked issues in the active milestone carrying `manual`
(`../_shared/issue-schema.md`) get their own block, directly after
`READY NEXT`:

```
YOUR TASKS (manual — no agent can do these)
  #102  Re-authorize Xcode Cloud            ready
  #90   F2 · Ship ops                       blocked by #84, #87
```

Why a separate section rather than a flag in `READY NEXT`: these are real work
and hiding them loses it, but they cannot be launched, so listing them beside
launchable work invites handing one to an agent that will stall or fake a PR.

Apply the same blocked/ready computation as `READY NEXT` — a blocked `manual`
issue is not actionable either, and saying what blocks it is still the useful
part. Nothing here ⇒ omit the section entirely rather than printing an empty
heading.

**Report decorative blocking honestly.** If issues carry a `blocked` label but no
dependency edge (`blockedBy.totalCount == 0`), every readiness query calls them
ready — which is the honest reading of the data. Say so rather than silently
trusting either signal: *"3 issues carry a `blocked` label with no dependency
edge; readiness below treats them as ready."*

## 6. Output

One compact table: lane · issue · branch · PR (# / state / gated?) · session ·
last activity · verdict. Then one line per **non-`working`** lane saying the next
action:

- `awaiting-gate` → "PR open, no agent running, not yet gated — run `/orca:verify <n>`"
- `pr-open` → **"gate passed, awaiting your review and merge"**, with the PR's
  age from `updatedAt`. This is the one lane state that is healthy *and* blocked
  on a human, so it needs an action line even though nothing is wrong. Past about
  a week, say so — a ready PR nobody merged is a real stall the verdict table
  otherwise calls fine.
- **`mergeable: CONFLICTING` on any open PR** → "will not merge as-is — rebase
  needed", regardless of verdict. Evidence gathered before a conflicting rebase
  is stale by definition.
- **failing `statusCheckRollup`** → "CI failing", stated alongside the gate
  verdict rather than instead of it. A passing gate and red CI can coexist:
  `/orca:verify` checks the issue's criteria against the branch; it is not CI and
  does not supersede it.
- `merged-reapable` → "run `/orca:status --reap` to clean it up" (or reap now if
  `--reap` was passed)
- `merged-live` → "merged — close its terminals, then it can be reaped"
- `stalled` → "session gone with unmerged work" — and **name both exits**, since
  neither is obvious:
  - **Resume it.** The executor contract still exists at
    `~/.claude/plans/<repo>/<date>-<slug>.prompt.md` and is exactly what a
    resumed session should read. Start one with `orca terminal create --worktree
    <selector> --command "claude"`, then point it at that file. Tell the resumed
    agent the branch already exists so it does not try to create one.
  - **Abandon it.** Close the PR if there is one, then run the full pre-deletion
    checklist in `../_shared/orca-lanes.md` — **especially the dirty-tree check**,
    because unmerged work is exactly what is at risk here — and only then
    `orca worktree rm`. Decide separately what happens to the issue: unassign it,
    or drop its milestone back to unscheduled. `--reap` will never do any of this
    for you; it only touches provably-merged lanes.
- `needs-attention` → the exact contradiction found
- **two lanes sharing one worktree path, or two open PRs from one branch** →
  **"lane invariant broken"**, and say why it matters: merging either PR frees
  the worktree the other still needs. One lane is one issue, one worktree, one
  branch, one PR (`../_shared/orca-lanes.md`). Report it under
  `needs-attention` — this is the state that turns a routine merge into lost
  work, and the user has no way to see it coming otherwise.
- **an open PR whose body says `Refs #n` rather than `Closes #n`** → flag it:
  that PR will merge without closing its issue, which usually means the lane is
  doing part of a larger effort that should have been its own issue.
- **merged PR that closed no issue** → "merged without `Closes #n` — the issue is
  still open." The PR body was malformed; the merge cannot be undone. **The
  remedy is for the human to close the issue with a comment naming the merged
  PR.** The "never close an issue by hand" rule binds skills and executors, not a
  person repairing a malformed merge — say so, or this lane is reported forever
  and the backlog stays permanently wrong.

## 7. The roadmap — regenerated every run

`ROADMAP.md` is a **rendering of GitHub state**, never a source (`TRACKING.md`).
It is rewritten on every run, without a flag, because a derived file that is only
sometimes refreshed goes stale silently — and a stale generated file is worse
than none, since it still looks current.

Three guards, all mandatory. **Any one failing ⇒ skip the write** and say so in
one line; never fail the whole run over it.

**1. Never write a tracked file.**

```bash
git ls-files --error-unmatch ROADMAP.md 2>/dev/null && echo TRACKED
```

Tracked ⇒ do not write, do not `git rm`. Explain that a committed roadmap
reintroduces the conflict surface the model exists to avoid, and point at
`/orca:migrate`, which proposes untracking it with consent. This guard matters
more now that the write is unprompted.

**2. Never create it in a repo with no backlog.** If §5 found no milestones and
no issues, write nothing — pointing this skill at an unrelated repo must not
litter it. An existing `ROADMAP.md` is still refreshed (it may legitimately
become empty).

**3. Never write outside the primary checkout.** Generate at the repo root, not
in a lane's worktree.

Then write all open milestones (nearest due date first) with their issues:

```markdown
# Roadmap

<!-- GENERATED by /orca:status — do not edit; it is rewritten on every run -->
<!-- <YYYY-MM-DD HH:MM> -->

## v0.3 — Audio pass (4/11 closed)

- [x] #48  Audio device enumeration
- [ ] #52  Footstep surfaces        in flight — <branch>
- [ ] #55  Mixer ducking            blocked by #52
```

Closed issues are `[x]`; in-flight ones name their lane. The generated header is
mandatory — without it someone will edit the file by hand.

Say it is gitignored, so it is not committed and cannot conflict.

## 8. `--reap` — delete provably-finished lanes

Only `merged-reapable` lanes are candidates. **Every check in
`../_shared/orca-lanes.md`'s pre-deletion checklist must pass**, and checks 1, 3,
4 and 5 must be re-run immediately before the delete — a dirty file, a reopened
terminal, or a new commit can appear in the seconds since the scan. Check 5
(`HEAD == headRefOid`) is what stops a post-merge commit being lost, so a cached
value defeats its purpose.

The check whose failure is unrecoverable is the primary-checkout proof:

```bash
git -C <path> rev-parse --git-dir --git-common-dir     # equal ⇒ NEVER delete
```

Never trade it for `isMainWorktree` from a cached scan. It costs one command;
the failure destroys the user's actual project directory.

All checks pass ⇒ delete:

```bash
orca worktree rm --worktree id:<exact-id> --force
```

Use the **exact id string** from the earlier call — never assemble one.

Report per candidate: reaped, or skipped **with the exact failed check**. Any
failure ⇒ skip, no prompt, no retry; the next run sees it again. This is what
makes `/loop 15m /orca:status --reap` safe.

Deletion removes the worktree and its Orca entry. It does not touch the branch on
the remote or the PR.

## Failure modes to avoid

- **Fanning out per-lane calls** for facts `worktree ps` already returned.
- **Trusting `linkedPR` as a state.** It is a number; PR state comes from `gh`.
- **Reporting a partial run as complete** when one half is unavailable.
- **Writing a tracked `ROADMAP.md`**, or `git rm`-ing it here. The write is
  unprompted now, so this guard carries more weight than it used to.
- **Creating `ROADMAP.md` in a repo with no backlog** — that is littering.
- **Failing the whole run because the roadmap write was skipped.** It is one
  line of report, never an error.
- **Reaping on a cached `isMainWorktree`** instead of the live git proof.
- **Prompting during `--reap`.** Ambiguity is always a skip.
- **Treating an open PR as gated.** Lanes open normal PRs, so an open PR proves
  only that work was pushed. The gate verdict comment is the signal.
