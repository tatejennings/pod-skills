# The scheduled automation — shipped disabled, on purpose

An Orca automation can run a prompt on a schedule, in a fresh worktree per run,
gated by a precheck. That is enough to run this pipeline unattended. **This
plugin ships that automation disabled, and enabling it is a deliberate act with
preconditions.**

This is a config artifact, not a skill. Nothing invokes it; a human creates it
when they decide the guardrails below are in place.

Verified against `orca` 1.4.162, 2026-07-31 (`orca automations create --help`).

## Why disabled

An adversarial review of this design concluded that **unattended issue → PR is
not responsible to ship**, for one reason that dominates the rest:

> An agent can optimize a proxy for the goal, carry forward numbers measured
> before its own change, trim an inconvenient test, and open a polished,
> confident PR that closes an issue it did not satisfy. Every artifact looks
> correct.

`/orca:verify` exists because of that finding, and it is the precondition for
any unattended run. A pipeline that can open PRs but cannot check them is a
machine for generating confident wrong work.

The responsible shape is not "no automation" but: **human-approved issue →
supervised implementation → evidence-gated PR → human review and merge.**
The automation may drive the first leg. It must never drive the last.

## The command

```bash
orca automations create \
  --name "orca lane launcher" \
  --trigger daily --time 09:00 \
  --provider claude \
  --repo path:/absolute/path/to/repo \
  --workspace-mode new-per-run \
  --precheck "<a command that exits 0 only when a lane should start>" \
  --prompt "<the run instruction>" \
  --disabled \
  --json
```

Flags that carry the weight:

| Flag | Why |
|---|---|
| `--disabled` | **Never omit on creation.** Enabling is a separate, deliberate act. |
| `--precheck` | Exit 0 continues; anything else records a *skipped* run. This is the quota and safety valve — see below. |
| `--workspace-mode new-per-run` | Each run gets a fresh worktree, so runs cannot collide in a checkout. |
| `--repo path:…` | Resolve by path, never by name (`orca-lanes.md`). |
| `--provider claude` | Valid ids include `codex`, `claude`, `gemini`. |
| `--trigger` | `hourly`, `daily`, `weekdays`, `weekly`, a 5-field cron, or an RRULE. |

Enable later, once the preconditions hold. **Automation subcommands take a
positional `<id>`, not a `--worktree`-style selector** (see the note below on
which also accept `--id`):

```bash
orca automations list --json                  # find the id
orca automations edit <id> --enabled --json
```

## The precheck is where safety lives

A precheck is a bounded command run before each scheduled run; **non-zero exit
skips the run.** That makes it the natural home for every quota and guard, and
it fails closed — a broken precheck skips rather than launches.

It should exit non-zero unless **all** of these hold:

- **Work is actually ready** — an open, unassigned issue in the active milestone
  with no unresolved `blockedBy` *and* a `### Done when` checklist. An issue with
  no criteria must never be launched unattended: nothing could gate the result.
- **Under the concurrency cap** — count live lanes for the repo
  (`orca worktree ps --json`, filtered on `repoId` + `isMainWorktree: false`)
  and refuse past a small ceiling.
- **Under the daily PR cap** — count PRs opened in the last 24h.
- **No lane is already on that issue** — `linkedIssue` collision check.
- **The circuit breaker is closed** — after N consecutive failed or ungated runs,
  refuse everything until a human resets it.

Write it as a script in the consuming repo, not inline: it will grow, and it
deserves to be readable and testable on its own.

## Preconditions before enabling

Every one of these is a repo-side property, not a plugin feature. None of them
are provided by installing this plugin.

1. **`/orca:verify` passes on real work in this repo**, and has been seen to
   **fail** on a branch known to be incomplete. A gate that has only ever
   returned `pass` is untested.
2. **Issues carry real `### Done when` checklists** — not fabricated ones. The
   gate is only as good as the criteria.
3. **No merge authority anywhere.** The executor contract forbids merging;
   confirm nothing else does it. PRs open ready for review (drafts are skipped by
   review tooling), so the gate is advisory rather than structural — under an
   automation, nothing but the precheck and a human stands between an opened PR
   and a merge.
4. **Atomic claiming.** Assign the issue before launching, and re-validate it is
   still open and assigned to this run immediately before opening the PR.
5. **Quotas wired into the precheck** — concurrency, daily PRs, and a spend
   ceiling if the provider has one.
6. **Leases on shared resources.** If lanes contend for one file or one
   exclusive resource, a lease — not hope. Logical independence does not imply
   physical independence.
7. **A circuit breaker.** Three consecutive failures halts the automation until a
   human looks.
8. **Stale-lane cancellation.** Something must notice a lane that has produced
   nothing for hours, or worktrees accumulate silently.

## What the automation must never do

- **Merge**, or mark a PR ready for review.
- **Close an issue by hand.** Completion is `Closes #<n>` on merge.
- **Launch work with no acceptance criteria.**
- **Run without a precheck.** An automation with no gate is an unbounded loop
  with credentials.

## Checking on it

```bash
orca automations list --json                   # ids live here
orca automations show <id> --json
orca automations runs --id <id> --json         # note: --id, not positional
orca automations run <id> --json               # run once, now
```

Argument styles differ: `show`, `edit`, and `run` accept **either** a positional
id or `--id`; `runs` accepts **only** `--id`. Verified at 1.4.162 — re-check with
`--help` rather than assuming symmetry.

`automations run` is the right way to test: it runs the automation immediately
without enabling the schedule, so the first real run happens while someone is
watching. Do that before enabling, every time the prompt or precheck changes.
