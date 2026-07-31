---
name: handoff
description: Hand a GitHub issue or an agreed plan off to a fresh agent in its own Orca worktree, so implementation happens in a separate lane instead of this session - reads the issue and its "### Done when" criteria, derives the worktree name, writes an executor contract to a file outside the repo, creates the worktree with the issue linked natively, launches one agent pointed at that contract, reports the lane, and STOPS. Use when the user says "/orca:handoff", "hand off #84", "hand this off", "run this in a new worktree", "spin up a session to build this", "give this to another agent", "launch a lane for issue N", or "package this plan for another context". This skill owns what gets handed off and what contract binds the executor; the mechanics of the Orca CLI belong to Orca's bundled orca-cli skill, and supervised multi-agent coordination with waits and decision gates belongs to its orchestration skill - use those directly when the request is about the CLI or about watching workers rather than handing over ownership.
---

# Handoff

Package a piece of work and give it to a fresh agent in its own worktree. **You
are the handing-off context: you do not implement anything here.**

The launch mechanics — the exact command, its flags, and why each one — are in
`../_shared/orca-lanes.md` under "The handoff invocation". Read that rather than
improvising a command. What this skill owns is everything *around* it: what gets
handed off, what the executor is bound to, and what proves the lane started.

## What this skill is not for

- **Ordinary CLI operations** — creating a worktree, running a terminal, reading
  output ⇒ Orca's bundled `orca-cli` skill (`orca skills get orca-cli`).
- **Supervised coordination** — dispatching tasks you intend to wait on, decision
  gates, worker DAGs ⇒ Orca's bundled `orchestration` skill. This skill is a
  **full ownership handoff**: it launches and stops. It never waits on the
  executor, monitors it, or coordinates several.
- **Deciding what to build** ⇒ `/orca:plan`. This skill packages work that is
  already decided.

## 0. Preconditions

```bash
command -v orca && orca status --json      # result.runtime.reachable
gh auth status
```

Orca missing or unreachable ⇒ **stop and say so.** There is no degraded handoff;
the whole point is the lane. Per `../_shared/orca-lanes.md`, never half-work.

Then resolve the repo — **by path, never by name** (`displayName` is
user-editable and frequently does not match the directory):

```bash
orca worktree current --json     # resolves cwd to a path: selector
```

Run from the repo you are handing work off in. Inside an existing lane this still
works, but check §1's in-flight rule carefully — handing off from a lane usually
means the work belongs to *this* lane instead.

## 1. Resolve the work

`$ARGUMENTS` is an issue number (`#84` or `84`), or empty.

### With an issue number

```bash
gh issue view <n> --json number,title,body,labels,milestone,state,assignees,blockedBy,url
```

Then check three things, and **report rather than silently proceeding** on any:

- **State.** A closed issue ⇒ stop and ask; handing off finished work is almost
  always a mistake.
- **Blockers.** Read `blockedBy.nodes[].state` — an issue is blocked only if some
  blocker is still `OPEN`. A non-zero `totalCount` alone means nothing; GitHub
  keeps the relationship after a blocker closes. Genuinely blocked ⇒ name the
  open blockers (`#87 (K1 · CloudSyncService)` — `nodes` carries the titles) and
  ask before continuing.
- **Already in flight.** An open PR referencing it, an assignee, or a live
  worktree with `linkedIssue == <n>`:

  ```bash
  orca worktree ps --json      # filter: linkedIssue == n, isMainWorktree false
  gh pr list --state open --json number,title,headRefName,closingIssuesReferences
  ```

  A live lane already on this issue ⇒ **stop and report it**, with its worktree
  and branch. Launching a second lane on one issue is how two agents open two
  competing PRs.

**Read the `### Done when` checklist** from the body (`../_shared/issue-schema.md`).
It goes into the contract verbatim — it is what `/orca:verify` will check, and
the executor must see the same criteria the gate will apply. **No checklist** ⇒
say so, hand off anyway, and state in the contract that acceptance criteria are
undefined so the executor knows to establish them rather than assume.

### Without an issue number

The work is whatever was agreed in this conversation, including an approved plan.
**No concrete plan exists ⇒ say so and stop.** Never invent one; a handoff of an
imagined plan wastes a whole executor run.

Ask for an issue number if the work plainly has one — `linkedIssue` is what makes
the lane visible to `/orca:status`, and `Closes #<n>` is the only thing that
records completion. Work with genuinely no issue is fine; just do not fabricate a
number.

## 2. Derive the worktree name

A short kebab-case slug from the issue title or the work: `fix-vent-retap`,
`audio-device-enum`. Rules:

- **Orca derives the branch itself** as `refs/heads/<git-username>/<name>` — do
  **not** hand-build a `<type>/<slug>` branch and assume it took. Read `branch`
  back from the create response (`../_shared/orca-lanes.md`).
- **Collision guard.** Check existing worktrees before creating; a name in use
  gets a `-2` suffix. Compare against the worktree *name*, not a path prefix.
- Keep it under ~30 characters and recognizable in a sidebar.

## 3. Write the executor contract

Write to an absolute path **outside the repo** — a new checkout cannot see
another checkout's untracked files, but any absolute path is readable:

```
~/.claude/plans/<repo-name>/<YYYY-MM-DD>-<slug>.prompt.md
```

`<repo-name>` comes from the primary checkout, not the cwd basename.

The contract is the whole reason this skill exists rather than a raw CLI call.
Fill in every section; omit a section only when it genuinely has no content.

```markdown
# <Issue title, or a one-line name for the work>

Implement the work described below. Read this entire file before starting.

## The work

<2–4 sentences: the goal and the chosen approach.>

Issue: #<n> — <url>          (omit both lines if there is no issue)

## Context

<Why now, relevant background, links to docs/specs/<slug>.md. Quote the issue
body rather than paraphrasing it.>

## Decisions already made

<Choices locked during planning, one line of rationale each, so they are not
re-litigated. Omit if the handoff carries no prior planning.>

## Done when

<The issue's ### Done when checklist, VERBATIM. These are the acceptance
criteria; /orca:verify will check this exact list against your branch.

If the issue had no checklist, say so explicitly here: "This issue has no
acceptance criteria. Establish them before implementing and record them on the
issue — do not assume." >

## How to work

1. You are in a fresh worktree with a branch already checked out. Confirm with
   `git status` — do not create another branch.
2. Follow the repo's CLAUDE.md / AGENTS.md rules (naming, required doc updates,
   test commands).
3. Implement step by step. Commit in logical increments with clear messages.
4. If reality contradicts this contract on details, adapt and record the
   deviation for your final summary. **If the core approach turns out to be
   wrong, stop and report back** instead of improvising a new design.
5. Verify against the "Done when" criteria above before considering the work
   done. Criteria that are prose rather than commands still need satisfying —
   they will be surfaced to a human reviewer.
6. Review your own full branch diff for bugs and regressions before pushing.
   Fix what is real, commit the fixes, re-run the tests.
7. Save durable learnings to memory BEFORE opening the PR — conventions or traps
   the next session would otherwise rediscover. Once this lane is finished it
   becomes eligible for cleanup, and anything unsaved goes with it.
8. Then: fetch and rebase onto the latest default branch, push, and open a
   **draft** PR. The body MUST contain `Closes #<n>` — that line is what records
   completion when it merges; nothing else does, and nobody closes the issue by
   hand. (Omit if this work has no issue.)
9. **Never merge the PR, and never mark it ready for review yourself.** It stays
   draft until the evidence gate passes and a human decides. Never write progress
   into a tracked file — no roadmap row, no status-board cell, no "mark done".

## Out of scope

<Explicit non-goals, especially adjacent work that looks related.>

## Finish with

Branch name, PR link, what was implemented, deviations and why, test results,
review findings and how they were resolved, and anything left for follow-up.
```

Two rules about this file:

- **Never overwrite an existing contract** — suffix the slug instead. An
  overwritten contract silently changes what a running lane was told to do.
- The launch prompt stays a **single short pointer sentence**. Everything
  multi-line lives here, so nothing has to survive shell quoting.

## 4. Launch the lane

Per `../_shared/orca-lanes.md`:

```bash
orca worktree create --name <slug> --no-parent \
  --agent claude \
  --prompt "Read the file <absolute contract path> and execute its instructions exactly." \
  --issue <n> --json
```

Drop `--issue <n>` when the work has no issue. Everything else stays.

**Verify the response rather than assuming it worked.** Response shape, confirmed
live at 1.4.162:

| What | Where |
|---|---|
| The created worktree | `result.worktree` — with `path`, `branch`, `id` |
| The agent's terminal handle | `result.agentTerminalHandle` (also `result.startupTerminal.handle`) |
| Warnings | `result.warnings`, when present |

An absent handle is not by itself a failure; folder-based repos may return none.

### Then verify the lane is actually isolated — this is not optional

`ok: true` does **not** mean a separate checkout exists. Against a project-backed
repo, `worktree create` can return success having made only a metadata entry that
points at the **primary checkout** — empty `branch`, `path` equal to the main
repo, and `isMainWorktree: false` despite not being isolated
(`../_shared/orca-lanes.md`).

That case is dangerous here specifically: the agent this skill launches would run
in the user's real working directory and commit onto whatever branch is checked
out there, while this report calls it a lane.

So after creating, and **before reporting success**:

```bash
git -C <result.worktree.path> rev-parse --git-dir --git-common-dir
```

- **Different** ⇒ a real linked worktree. Continue.
- **Equal**, or `path` matches the primary checkout, ⇒ **stop and report it.**
  Say the worktree was not isolated, that the agent is running in the primary
  checkout, and that the entry can be removed with
  `orca worktree rm --worktree id:<exact-id> --force`. Do not present it as a
  successful handoff.

**Branch:** take `result.worktree.branch` when non-empty. When empty — which does
occur — fall back to `git -C <path> branch --show-current`, and if that is empty
too, report that the branch could not be determined rather than inventing one.
Never predict it from the slug.

Do **not** cache the terminal handle for later use — handles are routing metadata
and change. Re-resolve via `orca terminal list --worktree <selector>` if needed
(you should not need it in this skill).

If `--agent claude` is rejected as an unknown agent id, **stop and report the
error rather than substituting a different agent.** The user asked for a Claude
lane; silently launching something else is worse than failing. `orca worktree
create --help` lists what the installed version accepts.

## 5. Report, then stop

Report:

- worktree name and path
- **branch, read back from the response**
- linked issue, if any
- the contract file path
- that the agent is running, and any warnings

Then **stop.** Do not monitor the lane, do not read its terminal, do not wait on
it, do not open the PR yourself. The executor reports to the user directly.

Point at what comes next: `/orca:status` to watch lanes, `/orca:verify <n>` to
gate the branch once a PR exists.

## Failure modes to avoid

- **Launching a second lane on an issue that already has one.** Check §1.
- **Assuming the branch name.** Orca derives it; read it back.
- **Writing the contract inside the repo.** The new checkout cannot see it.
- **Overwriting an existing contract file.** Suffix instead.
- **Cramming the contract into `--prompt`.** Quoting will eat it; the pointer
  sentence exists for this reason.
- **Substituting a different agent** when `claude` is rejected.
- **Monitoring the lane afterwards.** That is a full handoff turning into
  supervision — a different skill (`orchestration`) and a different request.
