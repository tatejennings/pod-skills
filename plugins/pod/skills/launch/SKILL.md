---
name: launch
description: >-
  Launch a lane for a GitHub issue or an agreed plan - a fresh Orca worktree
  with an agent already implementing it, so the work happens in a separate
  lane instead of this session. Reads the issue and its "### Acceptance
  criteria" checklist, refuses work already in flight or marked manual, writes
  an executor contract outside the repo, creates the worktree with the issue
  linked natively, starts one agent on that contract, reports the lane, and
  STOPS. Given several issue numbers it first checks their plans against each
  other for file collisions and launches only the ones that do not collide;
  --review does that check alone. Use when the user says "/pod:launch",
  "/pod:launch 84", "/pod:launch 84 85 87", "launch a lane for #84", "start
  work on issue 84", "run this in a new worktree", "put this in its own lane",
  "do these plans conflict", "will these collide", "are these safe to run in
  parallel", "launch the ones that do not collide", "launch the wave", or
  "hand off #84" / "hand this off" / "give this to another agent" WHEN the
  work is a GitHub issue or a plan agreed in this repo - this skill adds the
  acceptance criteria, the in-flight and manual-label checks, and the executor
  contract on top of a raw handover. Deciding WHAT to build, or an issue with
  no acceptance criteria yet, is /pod:plan. For a handover with no issue and
  no plan behind it, or raw worktree and terminal mechanics, use Orca's
  bundled orca-cli skill; for supervised coordination with waits and decision
  gates, its orchestration skill.
---

# Launch

Turn a piece of work into a **lane**: a fresh worktree with an agent already
implementing it. **You are the launching context — you do not implement anything
here.**

> **On naming:** "hand off", "handover", and "give this to another agent" are
> trigger phrases owned by Orca's bundled `orca-cli` skill, which performs the
> CLI-level handover. This skill is the layer above it — it decides *what*
> becomes a lane and *what contract binds the executor*. If the user's request is
> really about driving the CLI, that skill is the right one.

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
- **Deciding what to build** ⇒ `/pod:plan`. This skill packages work that is
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
orca worktree current --json     # → result.worktree.repoId, and the path
orca repo list --json            # all registered repos
```

**Join them by id**, never by name: take `result.worktree.repoId` from
`worktree current`, then find the `repo list` row whose `id` equals it. Matching
on `displayName` is the exact failure `../_shared/orca-lanes.md` warns about —
it is user-editable and frequently does not match the directory.

**Check `kind` before doing any work.** A repo registered as `kind: folder`
cannot produce a git worktree — `worktree create` returns `ok: true` while
sharing the primary checkout (`../_shared/orca-lanes.md`). The classification is
sticky, so a repo with commits, a remote, and a healthy working tree can still be
`folder`.

Stop before writing anything and report the fix, which is verified:

```bash
orca project setups --json                                  # find the setup id
orca project setup-update --setup <id> --kind git --json
```

(`orca repo add --path` does **not** re-detect; it returns the existing record
unchanged.) Checking here costs one call and avoids launching an agent into the
user's working directory.

Run from the repo you are handing work off in. Inside an existing lane this still
works, but check §1's in-flight rule carefully — handing off from a lane usually
means the work belongs to *this* lane instead.

## 1. Resolve the work

`$ARGUMENTS` is an issue number (`#84` or `84`), several, or empty.

**Several issue numbers, or `--review`** ⇒ read
[`references/collision-review.md`](references/collision-review.md) first. It
checks the finished plans against each other, then sends each surviving issue
through §1–§5 below one at a time; under `--review` it launches nothing.

### With an issue number

```bash
gh issue view <n> --json number,title,body,labels,milestone,state,assignees,blockedBy,url
```

Then check three things, and **report rather than silently proceeding** on any:

- **State.** A closed issue ⇒ stop and ask; handing off finished work is almost
  always a mistake.
- **The `manual` label** ⇒ **stop.** The issue is marked as work no agent can do
  — account access, store configuration, a physical device, a purchase
  (`../_shared/issue-schema.md`). Launching a lane for one wastes an agent that
  will either stall or fake its way to a PR. Say which label matched and what the
  issue needs from the user instead. Only proceed if they explicitly override,
  and say plainly that the agent is unlikely to be able to finish.
- **Blockers.** Read `blockedBy.nodes[].state` — an issue is blocked only if some
  blocker is still `OPEN`. A non-zero `totalCount` alone means nothing; GitHub
  keeps the relationship after a blocker closes. Genuinely blocked ⇒ name the
  open blockers (`#87 (K1 · CloudSyncService)` — `nodes` carries the titles) and
  ask before continuing.
- **Already in flight.** An open PR referencing it, an assignee, or a live
  worktree with `linkedIssue == <n>`:

  ```bash
  orca worktree ps --limit 200 --json
  gh pr list --state open --json number,title,headRefName,closingIssuesReferences
  ```

  **`worktree ps` returns every worktree Orca knows about, across all repos** —
  there is no `--repo` flag. Filter on **all three** of `repoId == <this repo>`,
  `linkedIssue == <n>`, and `isMainWorktree == false`. `linkedIssue` is a bare
  integer with no repo qualifier, so filtering on it alone means a lane on issue
  #84 in an unrelated repo blocks this launch. Take `repoId` from §0's
  `orca worktree current --json` (`result.worktree.repoId`).

  A live lane already on this issue ⇒ **stop and report it**, with its worktree
  and branch. Launching a second lane on one issue is how two agents open two
  competing PRs.

  **Exception — rework after a failed gate.** An existing lane or PR is
  *not* a refusal when the user is coming back from `/pod:verify` with a `fail`.
  That is the most common reason to start an agent, and blocking it would leave
  the failure path with no owner. Go to §1a instead.

**Read the acceptance checklist** from the body — `### Acceptance criteria`, or the older `### Done when`, which still counts (`../_shared/issue-schema.md`, "Finding the checklist").
It goes into the contract verbatim — it is what `/pod:verify` will check, and
the executor must see the same criteria the gate will apply.

**Refuse to launch part of an issue.** A lane is one issue, one worktree, one
branch, one PR (`../_shared/orca-lanes.md`). If the work you were handed is
*part* of an issue — a contract saying "part 1 of 3", a PR body that would say
`Refs #<n>` rather than `Closes #<n>`, criteria the lane cannot fully satisfy —
**stop.**

The failure is delayed and expensive: part A merges, its PR closes, its worktree
becomes reapable, and the later parts sharing that checkout lose it. Say what is
needed instead — an issue per part, with dependency edges recording the order
(`/pod:plan` §5a) — and launch once those exist. Each part is then an ordinary
lane closing its own issue.

**No checklist** ⇒ **offer `/pod:plan <n>` or `/pod:triage <n>` first.**
Launching criteria-less work guarantees a branch `/pod:verify` will refuse to
gate — the executor cannot know when it is done, and neither can the gate. If the
user declines, hand off anyway and state in the contract that acceptance criteria
are undefined so the executor establishes them rather than assuming.

### 1a. Rework — relaunching a lane whose gate failed

Entered when `/pod:verify` returned `fail` and the work needs another pass. The
target is **the existing lane**, not a new one.

The contract differs from a fresh launch in four ways, and getting them wrong
produces an executor that opens a second PR against its own branch:

| | Fresh launch | Rework |
|---|---|---|
| Worktree | created | **already exists — reuse it** |
| Branch | named with `--branch` | **already checked out** |
| PR | open one | **push to the existing PR** |
| Scope | the whole issue | **only the failed criteria** |

Steps:

1. **Find the lane** — `orca worktree ps --json`, filtered on `linkedIssue`. Gone
   (reaped, or deleted by hand) ⇒ this is a fresh launch after all; say so, since
   the branch still exists on the remote and the executor must check it out
   rather than branching anew.
2. **Write a rework contract** to a new file beside the original (do not
   overwrite it — the original records what was originally asked). It carries:
   - the **failed criteria verbatim**, with the gate's evidence for each — that
     evidence is the whole input, and making the executor re-derive it wastes the
     run;
   - which criteria **passed**, so they are not re-litigated or broken;
   - the four differences above, stated plainly;
   - a `## Files` section and the same two copied files as a fresh launch (§3),
     with new names beside the rework contract. The points below are what the
     rework contract says **in addition**, and they override the steps file
     where they differ;
   - the same **cold-reader review** the steps file carries (step 6), with
     its scope question narrowed to the rework: *does this diff address the
     failed criteria without touching what already passed?* Scope creep is a
     bigger risk here than on a fresh build — the executor is reading a whole
     branch it did not write, so the durability question must apply **only to
     lines this rework changed.** Pre-existing structure is out of bounds; it
     passed the gate once and is not this run's to relitigate.
   - the same **in-lane gate** the steps file carries (step 7), run against
     **the issue's full criteria, not just the failed ones.** A rework can break
     what previously passed, and a gate that only re-checks the failures would
     never notice. This is also why the rework gets its own gate pass rather than
     inheriting the earlier verdict: that verdict described a different tree.
   - **the rework's own one-pass bound.** A `FAIL` here gets one narrow fix and
     one re-gate, exactly as step 7a — then the executor pushes to the existing
     PR and reports it blocked. A branch that has now failed the gate twice
     across two sessions is telling you the criteria or the approach are wrong,
     not that it needs a third session.
   - **push to the existing PR and comment the new verdict there.** A re-gate
     adds a comment; it never edits the old one. The sequence of verdicts is the
     record of what this branch has been through.
3. **Start an agent in the existing lane** — `orca terminal create --worktree
   <selector> --command "claude"`, then `terminal wait --for tui-idle` before
   sending the pointer sentence (`../_shared/orca-lanes.md`). **Not**
   `worktree create`, which would make a second checkout of the same work.
4. **Report and stop**, as §5.

Never silently convert a rework into a fresh lane, and never launch rework into a
worktree whose tree is dirty with someone else's uncommitted work — report that
instead.

### Without an issue number

The work is whatever was agreed in this conversation, including an approved plan.
**No concrete plan exists ⇒ say so and stop.** Never invent one; a handoff of an
imagined plan wastes a whole executor run.

Ask for an issue number if the work plainly has one — `linkedIssue` is what makes
the lane visible to `/pod:status`, and `Closes #<n>` is the only thing that
records completion. Work with genuinely no issue is fine; just do not fabricate a
number.

## 2. Derive the worktree name and branch

**Name** — a short kebab-case slug from the issue title or the work:
`fix-vent-retap`, `audio-device-enum`. Under ~30 characters and recognizable in
a sidebar. Check existing worktrees first; a name in use gets a `-2` suffix.
Compare against the worktree *name*, not a path prefix.

**Branch** — `<type>/<slug>`, passed to `worktree create` as `--branch` (§4).
It says what the work is, which is what a branch list, a PR list, and a
changelog generator want. Without `--branch`, Orca names the branch
`<git-username>/<name>`.

| Signal | Type |
|---|---|
| a `bug` label, or the title describes broken behavior | `fix` |
| a new capability | `feat` |
| docs-only work | `docs` |
| tooling, deps, config, cleanup | `chore` |
| a research or investigation issue | `spike` |

**Match the repo's own convention first** — read a few recent branch names
(`git branch -r --sort=-committerdate | head -20`) and use the prefixes already
in use. A repo using `feature/` should not suddenly get `feat/`.

A taken branch name gets a numeric suffix from Orca, so **read `branch` back
from the create response** and use that value everywhere downstream. Never
predict it.

## 3. Write the lane's three files

All three go to an absolute path **outside the repo** — a new checkout cannot
see another checkout's untracked files, but any absolute path is readable:

```
~/.claude/plans/<repo-name>/<YYYY-MM-DD>-<slug>.prompt.md   the contract
~/.claude/plans/<repo-name>/<YYYY-MM-DD>-<slug>.steps.md    how to work — copied
~/.claude/plans/<repo-name>/<YYYY-MM-DD>-<slug>.gate.md     the gate prompt — copied
```

`<repo-name>` is the **primary checkout's folder name** — not the cwd basename
and not the GitHub repo name, so it matches where `/pod:plan` wrote the plan:

```bash
basename "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
```

**Copy the steps and the gate prompt; write only the contract.**

```bash
cp "${CLAUDE_SKILL_DIR}/references/executor-steps.md" <abs path>.steps.md
cp "${CLAUDE_SKILL_DIR}/references/gate-prompt.md"    <abs path>.gate.md
```

(`${CLAUDE_SKILL_DIR}` is this skill's base directory; if it appears here
unexpanded, use the base directory shown when the skill loaded.)

The steps file binds the executor to implement, run one cold-reader review,
have a **separate** agent gate the branch, rework a `FAIL` once, and open a
normal PR carrying the verdict comment. It is identical for every lane, so it
is never retyped — a paraphrase drops rules without anyone noticing.

The contract is the part that is specific to this lane. Fill in
[`references/contract-template.md`](references/contract-template.md): the work,
the issue, the `## Files` section naming the two copied files and the base
branch, context, decisions already made, the plan, the acceptance criteria
**verbatim**, and what is out of scope.

**Base branch** for the contract's `## Files`: the branch the repo's own
instructions name for integrating work, else the default —
`gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`. The gate
computes its diff against it, so a wrong one gates the wrong diff.

Confirm all three files exist before launching. A contract whose `## Files`
points at a file that was never copied is a lane that improvises its own gate.

The three rules about these files — a snapshot not a link, never overwrite, the
launch prompt stays one sentence — are in the reference file.

## 4. Launch the lane

Per `../_shared/orca-lanes.md`:

```bash
orca worktree create --name <slug> --no-parent \
  --branch <type>/<slug> \
  --agent claude --surface terminal \
  --prompt "Read the file <absolute contract path> and execute its instructions exactly." \
  --issue <n> --json
```

Drop `--issue <n>` when the work has no issue. Everything else stays.

`--surface terminal` is not optional. Without it the user's Chat | CLI setting
picks, and a chat lane has no terminal — `/pod:status` and `/pod:tech-lead`
read lanes through theirs.

`--surface` rejected as an unknown flag ⇒ create without it; an Orca that old
has no chat surface, and returns the handle as `result.agentTerminalHandle`.

`--branch` rejected as an unknown flag (Orca before 1.4.258) ⇒ create without
it, then `git -C <path> branch -m <type>/<slug>` while the branch has no
commits, and read the name back with `git -C <path> branch --show-current`.

**Verify the response rather than assuming it worked.** Response shape,
confirmed live at 1.4.269:

| What | Where |
|---|---|
| The created worktree | `result.worktree` — with `path`, `branch`, `id` |
| What started | `result.launch.outcome.kind` — must be `terminal` |
| The agent's terminal handle | `result.launch.outcome.handle` |
| Whether the prompt arrived | `result.launch.prompt.outcome` — `handed-to-terminal` |
| Warnings | `result.warnings`, when present |

**`outcome.kind` is not `terminal` ⇒ report it, quoting
`result.launch.receipt.detail`, and say the lane is a chat.** The agent is
running and the work is real, so do not delete the lane — but `/pod:status`
will not see a terminal in it. No `result.launch` at all is the older-Orca
shape above, not a failure.

**`ok: false` with `agent_session_operation_unknown` ⇒ never launch again
afresh.** The agent may already be running with the prompt submitted. Re-issue
the identical command once with `--retry-launch <error.data.operationId>`
added. Still unknown ⇒ check `orca worktree ps --json` for the lane, report
what is there, and stop (`../_shared/orca-lanes.md`).

### Then verify the lane is actually isolated — this is not optional

`ok: true` does **not** mean a separate checkout exists. Against a repo Orca
registered as `kind: folder`, `worktree create` can return success having made
only a metadata entry that points at the **primary checkout** — empty `branch`,
`path` equal to the main repo, and `isMainWorktree: false` despite not being
isolated (`../_shared/orca-lanes.md`). §0's `kind` check catches this earlier;
this is the backstop for anything it misses.

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

**Say that this session can be closed.** Nothing about the lane depends on it —
the plan is on disk, the contract is a file the executor already read, the issue
link lives in Orca's worktree record, and the criteria are on the issue. That
independence is why the contract is written to a file rather than passed inline.

The one thing closing loses is the *conversation* that produced the plan. If the
plan's **Decisions already made** section captured the trade-offs and the
rejected options, it costs nothing. If it did not, say so — that reasoning exists
only in the transcript, and it is cheaper to add a line to the plan file now than
to reconstruct it later.

Point at what comes next: `/pod:status` to watch lanes. **Say that the lane
gates itself** — the PR will arrive carrying a verdict comment, so the next
decision the user makes is whether to merge, not whether to run a gate.
`/pod:verify <n>` stays available to re-gate on demand, and is the right call
when the base has moved a long way or a verdict looks wrong.

## Failure modes to avoid

- **Launching a second lane on an issue that already has one.** Check §1.
- **Assuming the branch name.** A taken name gets a suffix; read it back.
- **Writing the contract inside the repo.** The new checkout cannot see it.
- **Overwriting an existing contract file.** Suffix instead.
- **Cramming the contract into `--prompt`.** Quoting will eat it; the pointer
  sentence exists for this reason.
- **Substituting a different agent** when `claude` is rejected.
- **Monitoring the lane afterwards.** That is a full handoff turning into
  supervision — a different skill (`orchestration`) and a different request.
- **Retyping the steps or the gate prompt** instead of copying them, or
  launching before both copies exist. The gate is a *separate* agent reading a
  file; an executor left to improvise its own check is grading itself.
- **Editing the copied steps for one lane.** The one-pass rework bound and the
  verdict comment live there; a lane-specific exception goes in the contract.
