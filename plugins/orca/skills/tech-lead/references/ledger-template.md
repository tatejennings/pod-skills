# The ledger — the loop's memory

§5 of `../SKILL.md`. One file per scope at:

```
~/.claude/plans/<repo-name>/tech-lead-<scope-slug>.md
```

`<repo-name>` from the primary checkout; `<scope-slug>` from the words — `epic-loop`,
`v1-launch`, `reviews`, `issues-15-16`. Written at the end of every tick and after every steering
message. Read first on `resume` and after compaction. **Never inside a checkout, never tracked.**

Keep it short: the tick log is one line per tick, and old lines can be pruned once a lane is
merged. This is state, not narrative.

## Template

```markdown
# tech-lead · <repo-name> · <scope>

- Started: <ISO time> · Mode: awaiting approval | autonomy granted <ISO time> | paused | declined | stopped | idle-stopped <ISO time> | hard-cap-stopped <ISO time>
- Idle ticks (owner-only in a row): 0   ← reset to 0 whenever a tick does anything; stop at 2
- Cap: <n> · Order: #15, #16, #17, #18 (as approved/edited)
- Decision bar: default | recommend-only (set by user at <time>)
- Repo rules read: CLAUDE.md @ <commit>; locked decisions: <the file the repo names, or "none">
- Gate identity: `<login this run posts verdicts as>` · trusted producers: `<login>`, `<…>`
- Reviewers: owner `<login>`; adopted `<login>` (markers: `P1|P2|P3` badge) ; everyone else queued
- Auto-merge armed on: none | **PR #21 (enabled by `<login>`)** ← re-checked every tick, not cached

## Lanes

| Issue | Worktree id | Branch | PR | Verdict | Plan rounds | Fix rounds | Last-seen comment | Next |
|---|---|---|---|---|---|---|---|---|
| #15 | repo-1::/Users/…/<lane-slug> | feat/15-<lane-slug> | #21 | pr-open · PASS @ 9f1fd02 | 2 | 1 | 3788608310 | human-review-ready |
| #16 | — | — | — | planning (terminal <handle>) | 1 | 0 | — | panel round 2 |

## Decisions made

- #15 · <ISO time> · <choice> · <issue comment url>

## Waiting on you

- #5 · manual · <what it needs>
- #16 · fork: <A> vs <B> · panel 2–1 for A · my rec: A · queued <ISO time>
- PR #23 · **auto-merge armed** by `<login>` — will merge itself on green CI; excluded until you decide
- PR #24 · `gated-stale` — re-gated this tick, verdict expected next tick
- #9 · review state unknown — no adopted reviewer completed against head `a1b2c3d`

## Human-review-ready

- PR #21 (#15) — gate PASS @ head `9f1fd02` · CI green · review complete · no open threads · notified <ISO time>

## Skipped

- #14 · blocked by #16 (OPEN)
- #1–#4 · needs-owner

## Tick log

- <ISO time> · observed 2 lanes · dispatched fix r1 → PR #21 · launched #16 · notified: no
- <ISO time> · noop
```

## Rules

- **Mode is written the moment it is decided**, before any action, so a crash between decision
  and first launch does not resume in the wrong mode.
- **Last-seen comment id is per PR** and only moves forward.
- **Fix rounds and plan rounds are the bounds**; they never reset unless the user says so.
- **Waiting on you** is the only section the notification is allowed to be about, together with
  *Human-review-ready*. If neither changed, no notification.
- Steering messages append one line to the tick log (`user: cap 2`) and change the header fields.
- **The ledger is memory, never evidence.** It holds what only this loop knows — the user's grants
  and steering, counters and bounds, decisions made, what has been notified. Everything about the
  *world* is **re-derived every tick, never read back from here**: PR state, CI, gate verdicts and
  their freshness, head SHAs, thread state, auto-merge, whether a reviewer ran. A cached fact ages
  into a wrong one silently, and the whole point of the freshness rules is defeated by a ledger row
  that remembers `PASS` from four hours ago. When a row and the world disagree, **the world wins
  and the row was stale.**
