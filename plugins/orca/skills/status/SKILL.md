---
name: status
description: Read-only dashboard joining Orca's lane state against the GitHub backlog - every worktree's branch, issue, PR state, session liveness and a verdict saying what needs attention, plus active-milestone progress and a READY NEXT list of unblocked issues, which makes this the answer to "what should I work on next". With --roadmap it regenerates the gitignored ROADMAP.md from GitHub state; with --reap it deletes provably-finished lanes after strict safety checks. Non-interactive and conservative by construction, so looping it is safe. Use when the user says "/orca:status", "/orca:status --reap", "/orca:status --roadmap", "what should I work on next", "what's ready", "what's blocked", "what's left in this milestone", "how are the lanes doing", "status of my worktrees", "any lanes to clean up", "reap merged worktrees", "regenerate the roadmap", or sets up "/loop 15m /orca:status". For driving the Orca app - creating worktrees, running terminals - use Orca's bundled orca-cli skill instead; this skill only reads, plus the narrowly-scoped deletion --reap performs.
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

`$ARGUMENTS` may contain:

- `--reap` — delete provably-finished lanes (§5). Strictly non-interactive:
  every ambiguous case is reported, never deleted, never prompted.
- `--roadmap` — regenerate the gitignored `ROADMAP.md` (§6).

Both compose with the default report and with each other.

## 0. Preconditions and degraded mode

```bash
command -v orca && orca status --json     # result.runtime.reachable
gh auth status
```

**This skill degrades honestly rather than failing whole** — see
`../_shared/orca-lanes.md`:

- **Orca missing/unreachable** ⇒ run the backlog half (§3, §4, §6) and report the
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
orca worktree ps --json
```

Keep worktrees where `repoId` matches **and `isMainWorktree` is false**. Never
use a path prefix (`../_shared/orca-lanes.md`).

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
  --json number,state,isDraft,headRefName,headRefOid,mergedAt,url,closingIssuesReferences
```

`closingIssuesReferences` costs nothing extra here and gives each lane its issue
without a per-lane query — which is what keeps this skill safe under `/loop 15m`.

If a branch has several PRs, prefer the open one, else the most recently updated.

`isDraft` matters for this pipeline: a draft PR means the evidence gate has not
passed yet, and that is the normal state, not a problem.

## 4. Verdicts

Exactly one per lane:

| Verdict | Condition |
|---|---|
| `working` | agents active or terminals live; PR absent or draft |
| `pr-open` | a non-draft PR is open |
| `awaiting-gate` | a **draft** PR exists and no agent is active — ready for `/orca:verify` |
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

**Report decorative blocking honestly.** If issues carry a `blocked` label but no
dependency edge (`blockedBy.totalCount == 0`), every readiness query calls them
ready — which is the honest reading of the data. Say so rather than silently
trusting either signal: *"3 issues carry a `blocked` label with no dependency
edge; readiness below treats them as ready."*

## 6. Output

One compact table: lane · issue · branch · PR (# / state / draft) · session ·
last activity · verdict. Then one line per **non-`working`** lane saying the next
action:

- `awaiting-gate` → "draft PR open, no agent running — run `/orca:verify <n>`"
- `merged-reapable` → "run `/orca:status --reap` to clean it up" (or reap now if
  `--reap` was passed)
- `merged-live` → "merged — close its terminals, then it can be reaped"
- `stalled` → "session gone with unmerged work — reopen a session or remove it"
- `needs-attention` → the exact contradiction found
- **merged PR that closed no issue** → "merged without `Closes #n` — the issue is
  still open", which is a malformed PR body, not a state to fix by hand

## 7. `--roadmap` — regenerate the stateless roadmap

`ROADMAP.md` is a **rendering of GitHub state**, never a source (`TRACKING.md`).

**Refuse to write it if it is tracked:**

```bash
git ls-files --error-unmatch ROADMAP.md 2>/dev/null && echo TRACKED
```

Tracked ⇒ do not write. Explain that a committed roadmap reintroduces the
conflict surface the model exists to avoid, and point at `/orca:migrate`, which
proposes untracking it with consent. Never `git rm` it here.

Untracked ⇒ write all open milestones (nearest due date first) with their issues:

```markdown
# Roadmap

<!-- GENERATED by /orca:status --roadmap — do not edit; regenerate instead -->
<!-- <YYYY-MM-DD> -->

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
`../_shared/orca-lanes.md`'s pre-deletion checklist must pass**, and checks 1, 3
and 4 must be re-run immediately before the delete — a dirty file or reopened
terminal can appear in the seconds since the scan.

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
- **Writing a tracked `ROADMAP.md`**, or `git rm`-ing it here.
- **Reaping on a cached `isMainWorktree`** instead of the live git proof.
- **Prompting during `--reap`.** Ambiguity is always a skip.
- **Treating a draft PR as a problem.** It is the expected state before the gate.
