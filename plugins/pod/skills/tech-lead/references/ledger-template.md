# The ledger — the loop's memory

§5 of `../SKILL.md`. One file per scope at:

```
~/.claude/plans/<repo-name>/tech-lead-<scope-slug>.md
```

`<repo-name>` is the primary checkout's folder name — the same directory `/pod:plan` and
`/pod:launch` write to, never the GitHub repo name
(`basename "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"`); `<scope-slug>` from the words — `epic-loop`,
`v1-launch`, `reviews`, `issues-15-16`. Written at the end of every tick and after every steering
message. Read first on `resume` and after compaction. **Never inside a checkout, never tracked.**

**Keep it under about 80 lines.** The tick log is one line per tick; when a lane merges, delete
its row and its tick lines. A ledger that has grown into a narrative is one that has started
storing the world — every row past the columns below is something to re-derive instead.

## Template

```markdown
# tech-lead · <repo-name> · <scope>

- Started: <ISO time> · Mode: awaiting approval | autonomy granted <ISO time> | paused | declined | stopped | idle-stopped <ISO time> | hard-cap-stopped <ISO time>
- Idle ticks (owner-only in a row): 0   ← reset to 0 whenever a tick does anything; stop at 2
- Cap: <n> · Order: #15, #16, #17, #18 (as approved/edited)
- Slate reviewed by product seat: <ISO time> | not yet   ← once; never re-convened on resume
- Decision bar: default | recommend-only (set by user at <time>)
- Repo rules read: CLAUDE.md @ <commit>; locked decisions: <the file the repo names, or "none">
- Gate identity: `<login this run posts verdicts as>` · trusted producers: `<login>`, `<…>`
- Reviewers: owner `<login>`; adopted `<login>` (markers: `P1|P2|P3` badge) ; everyone else queued
- Trust: solo-private | shared   ← from §0; re-derived on resume

## Lanes

| Issue | PR | Plan rounds | Fix rounds | Last-seen comment | Notified | Next |
|---|---|---|---|---|---|---|
| #15 | #21 | 1 | 1 | 3788608310 | ready <ISO time> | — |
| #16 | — | planning (terminal <handle>) | 0 | — | — | panel |

No worktree id, branch, verdict, head or CI column: those are the world, and the status script
returns them fresh every tick.

## Decisions made

- #15 · <ISO time> · <choice> · <issue comment url>

## Waiting on you

- #5 · manual · <what it needs>
- #16 · fork: <A> vs <B> · panel 2–1 for A · my rec: A · queued <ISO time>
- PR #23 · auto-merge armed — excluded until you decide · queued <ISO time>

## Human-review-ready

- PR #21 (#15) · notified <ISO time>

## Skipped

- #14 · blocked by #16 (OPEN)
- #1–#4 · needs-owner

## Tick log

- <ISO time> · convened product seat (reordered #16 before #15) · proposed · awaiting approval
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
