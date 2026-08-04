---
name: plan
description: Plan a piece of work end-to-end - a GitHub issue number, a milestone, or a free-form feature/bug description. Researches docs and codebase with parallel agents, drafts an execution-ready plan, then has a cold-reader agent adversarially review it for completeness, holes, single-context feasibility, and blast radius. Writes the "### Done when" acceptance checklist onto the issue, since that is what gates the work later, and saves the plan to a file so it survives the session. With --launch it continues straight into /orca:launch, starting the work as a lane instead of stopping for approval. Use when the user says "/orca:plan", "/orca:plan 84", "/orca:plan fix the vent double-tap bug", "plan issue N", "plan this feature", "plan milestone X", "help me plan this", "plan and launch this", "how should we approach #84", "what is the best way to fix X", "figure out how to do issue 84", "scope out #84", "break down what needs to happen for X", "think this through before we build it", "design the approach for X", or "what would it take to add X" - any request to work out HOW to do something before implementing it. This plans one piece of work; it does not implement. Planning several issues at once is /orca:wave, starting the work in a lane is /orca:launch, and driving the Orca app directly is Orca's bundled orca-cli skill.
---

# Plan

Produce an execution-ready plan for the work in `$ARGUMENTS` — a GitHub issue, a
milestone, or a free-form description of a feature or bug. **You plan; you do not
implement.**

The plan will likely be handed to a fresh agent in its own worktree
(`/orca:launch`), so it must be self-contained: an executor sees the plan and
the issue, not this conversation.

Scale to the work. A milestone-sized piece of work gets the full treatment; a small bug
gets the same *structure* with lighter research and a quicker review — **never
skip the review**.

## What this skill is not for

- **Starting the work in a lane** ⇒ `/orca:launch` (or `--launch` here, which
  invokes it).
- **Driving the Orca app** ⇒ Orca's bundled `orca-cli` skill.
- **Checking finished work** ⇒ `/orca:verify`.

## 0. Preconditions

- `$ARGUMENTS` empty ⇒ ask what to plan.
- Check for `--launch`: plan, review, then launch the lane via `/orca:launch` (§6).
- The rest of `$ARGUMENTS` is the target — a leading `#` or an all-digits token
  means an issue; anything else is a milestone name or a description.
- If not already in plan mode, call `EnterPlanMode` and stay there for the whole
  skill. **Under `--launch`, do not enter plan mode** — its approval gate cannot
  be auto-approved. Hold the same discipline manually: research and plan only,
  and touch no repo files.

## 1. Pin down the requirements

**Issue number** — the issue *is* the requirement:

```bash
gh issue view <n> --json number,title,body,labels,milestone,state,assignees,blockedBy,url
```

Quote the body in Context. Follow any `docs/specs/<slug>.md` link as requirements
input. Any blocker still `OPEN` in `blockedBy.nodes[].state` ⇒ planning blocked
work is usually a mistake worth surfacing first. (A non-zero `totalCount` with
every blocker `CLOSED` is ready — the relationship outlives the blocker.)

**Milestone name** — prefer GitHub, per `../_shared/github-backlog.md`; fall back
to in-repo docs only when no matching milestone exists. Quote the real
requirements; do not paraphrase from memory.

**Free-form** — the user's words are the requirement. Restate them as concrete
acceptance criteria: what behavior changes, and how you would observe it.

**Any input:** check whether the work is already in flight before planning it
from scratch — an assignee, an open PR, a live lane (`orca worktree ps --json`,
filtered on `repoId` **and** `linkedIssue` — it spans all repos), recent commits. Prefer those signals over any status file.

### 1a. A pre-written plan? Adopt it rather than re-planning

If the issue or milestone **links to a markdown file that contains ordered
implementation steps**, the user already planned this. Adopt it:

- Announce which file, then **skip §2 and the drafting half of §3.**
- Carry their words across. Restructure into §3's sections and fill genuinely
  missing ones, but never reword, reorder, or "improve" steps they wrote.
- Cite the source in Context.
- **Still run §4's review** — feasibility and blast radius matter as much for a
  hand-written plan. Fold in only additive fixes. A finding that would change
  their chosen approach is a disqualifier (§6), not an edit you make.

**A `docs/specs/<slug>.md` link is not an adoption trigger.** Under this tracking
model, issues routinely link their spec — that is the normal shape. Specs hold
*why and what*; plans hold *how*. Read the spec as input and plan normally.

Ambiguous ⇒ plan normally and note it in one line. A wasted research pass costs
far less than an executor running someone's design doc as a build order.

## 2. Research with parallel agents

Launch research agents **in a single message** so they run concurrently. Give
each a specific question and tell it to return facts, paths, and constraints —
not file dumps:

- **Code agent** (Explore): the code this touches — architecture, the seams and
  tests it builds on, patterns to match. For a bug: the reproduction path and
  likely defect site.
- **Docs agent** (Explore): what the design docs say — requirements, prior
  decisions, naming conventions, related work. Skip for small fixes.
- **Architecture agent** (Plan): only when the approach is genuinely non-obvious
  — propose and compare strategies.

For a small bug, the code agent alone is usually enough. Read the reports; follow
up inline on anything load-bearing they left vague.

## 3. Draft the plan

Use exactly these sections — they are what `/orca:launch` packages:

- **Goal** — one paragraph; what "done" looks like.
- **Context** — requirements source with quotes, relevant background.
- **Decisions already made** — every locked choice with one-line rationale, so
  the executor does not re-litigate them.
- **Steps** — ordered, concrete, naming exact files and symbols.
- **Verification** — how each step is proven, and the whole thing overall.
- **Out of scope** — explicit non-goals, especially adjacent work.

Two rules on Steps:

- **Never add a step that writes progress to a tracked file** — no roadmap row,
  no status-board cell, no "mark done" edit. Completion is `Closes #<n>` and
  nothing else (`../_shared/github-backlog.md`). If the repo's own CLAUDE.md
  mandates such an edit, surface it in Context as a conflict for the user — do
  not quietly comply, and do not quietly ignore it.
- To mark work in flight, use the tracker, not a file:
  `gh issue edit <n> --add-assignee @me`.

Where a real trade-off needs the user's call, use AskUserQuestion **before**
finalizing. Where a conventional default exists, decide it and record it under
Decisions.

**Inside a wave** (`/orca:wave` started this context in its own terminal): **ask
normally** — unless `--auto` was also passed. The point of a plain wave is that
the user moves between contexts answering questions, so asking and waiting is
correct there; do not adopt a defer-instead-of-asking posture just because the
context was started programmatically.

**With `--auto` in a wave**, hold the bar below: plan alone where the choice is
overwhelming, and **defer with a named question where it is not.** The wave
collects those questions and tells the user which tabs to visit, so a deferral
is one visit rather than a blocked wave — and a wrong guess is still a whole
executor run.

**Under `--launch`, do not ask** — and hold a high bar for deciding alone.
Proceed on a fork only when one option is *overwhelmingly* recommended: the
codebase's conventions, the requirements, and standard practice all agree, and
being wrong would be cheap to reverse. Anything less is a fork you do not own —
defer (§6). Deferring on honest uncertainty is a correct outcome, not a failure:
a wrong guess costs a whole executor run, a deferral costs one question.

### 3a. The `### Done when` checklist — write it onto the issue

**This is what makes the work gateable, and it is part of planning, not an
afterthought.** Per `../_shared/issue-schema.md`, derive acceptance criteria and
write them onto the issue:

```bash
gh issue edit <n> --body-file - <<'EOF'
<existing body, with the ### Done when section added or updated>
EOF
```

Rules that matter more than completeness:

- **Prefer checkable forms** — a command that must exit 0, a string that must
  appear in the diff, a file that must change.
- **Write prose for what is genuinely not checkable.** Do not contort a criterion
  into a fake command to make a future gate go green; `issue-schema.md`'s human
  bucket exists for exactly this.
- **Never fabricate criteria** to look thorough. A criterion nobody can verify,
  or one that does not follow from the requirements, is worse than a short list.
- **An existing `### Done when` section is not yours to replace.** It was written
  before this planning pass — by `/orca:triage` with the user, or by an earlier
  run — and criteria written earlier are the stronger gate. Show the existing
  criteria beside the ones you would have written and **ask**. Silently
  overwriting negotiated acceptance criteria is exactly the corruption this model
  exists to prevent.
- Preserve the rest of the body. Read it, add or replace only the checklist
  section, and write it back through stdin.
- No issue (free-form work) ⇒ put the criteria in the plan's Verification
  section instead, and say the work has no issue to gate against.

## 4. Adversarial review

Spawn a **fresh** general-purpose agent — a cold reader, not a fork, so it does
not inherit your drafting bias. Give it the full plan and the requirements
source, and have it attack on four axes.

**Tell it the bar explicitly**, or it will find fault to justify its existence:

> Report only findings that would change what the executor does. A plan you
> would let run as-is is a valid outcome and the common one — say so plainly
> rather than manufacturing concerns.
>
> **"Split it" is the strongest claim you can make, and usually the wrong one.**
> Each part needs its own issue, worktree, PR, and review; parts cannot share a
> lane. Size alone is never sufficient — agents handle large coherent efforts
> well. Recommend a split only against the criteria in axis 3, and when you do,
> name the seam, the cost in lanes, and why one context genuinely cannot hold
> the work.

1. **Completeness** — is every requirement covered by a step? Does every step
   have a verification? Is every `### Done when` criterion actually produced by
   some step?
2. **Holes** — unstated assumptions, missing edge cases, migrations or format
   changes glossed over, test debt, doc obligations skipped.
3. **Single-context feasibility** — can ONE agent execute this end to end?

   **Default to one lane. Splitting is the exception, and it must be argued
   for.** Agents handle large efforts well; what they handle badly is work
   fragmented across contexts that each have to rebuild the same understanding.

   **A split is expensive, and more expensive than it looks.** Each part needs
   its own issue, its own worktree, its own PR, and its own review (§5a — parts
   cannot share a lane). It forces sequencing, and every later part re-reads
   context the earlier one already had. **A plan that is merely large is still
   one plan** — prefer one substantial lane over three coordinated ones.

   **Split only when one of these is true** — not on a count of soft limits:

   - **Repetitive same-shape edits at a scale where one context would lose
     accuracy** — think hundreds, not dozens. First try to **script it**: a
     mechanical transformation applied uniformly is one step, not one hundred.
     Split by natural group only if it genuinely cannot be scripted.
   - **More than one new subsystem or major architectural decision.** Two
     irreversible choices in one lane means the second is made while the first is
     still unproven. This is the strongest reason to split, and often the only
     real one.
   - **An open-ended tuning or measurement loop.** Anything where "done" is found
     by iterating — balance passes, performance work — gets its own context,
     because the cycle count is unknowable up front.
   - **A migration of a persisted format** alongside feature work. The migration
     is irreversible and deserves to land and be verified alone.
   - **A hard sequencing dependency inside the work** — step 7 cannot be verified
     until step 4 is merged and observed in the real world.

   **Volume is not a reason to split.** Step counts, file counts, and line counts
   are weak signals at most — usable to support a split already justified above
   (*"and it is also 40 files"*), never as the reason for one. A feature touching
   30 files coherently is one lane.

   What matters is **decisions held simultaneously**, not volume. Thirty files
   implementing one decision is easier than five files implementing four — and
   the second case is the one worth splitting.

   **If you recommend a split, say what it costs** — how many lanes, what must
   merge before what — and confirm each part is independently *verifiable*, not
   merely smaller. A split that produces a part nobody can gate on its own has
   made things worse. If you cannot name a clean seam, that is evidence it is one
   lane.
4. **Blast radius** — shared types, data formats, serialized content, test
   baselines, in-flight parallel work that could collide. Flag anything that
   makes the change hard to revert.

Fold real findings into the plan. Note what you dismissed and why — that is
ammunition against re-litigation later.

## 5. Present

**Save the plan to a file first**, so it outlives this context:

```
~/.claude/plans/<repo-name>/<YYYY-MM-DD>-<issue-or-slug>.md
```

`<repo-name>` comes from the primary checkout, not the cwd basename. The path is
deliberately **outside the repo** — a plan is not repo content, and a lane's new
checkout cannot see another checkout's untracked files anyway.

This matters beyond tidiness: a plan that exists only in conversation cannot be
compared against another plan, handed to a later session, or re-read after this
context closes. `/orca:wave --review` reads these files to check plans against
each other, and `/orca:launch` can be pointed at one directly. **Never overwrite
an existing plan file** — suffix the slug instead.

Then:

- Present the final plan via `ExitPlanMode` for approval.
- If the review said split, **present the split as the plan** — and see §5a,
  because a split is not done until each part is its own issue.
- Close by noting `/orca:launch` can start it in its own lane — but do
  not run it unasked; the user may execute inline.

### 5a. A split means new issues — not sub-plans of one issue

**One lane is one issue, one worktree, one branch, one PR**
(`../_shared/orca-lanes.md`). A split that leaves three parts pointing at *one*
issue violates that, and the failure is expensive and delayed: part A merges,
its PR closes, its worktree becomes reapable — and parts B and C, sharing that
checkout, lose the ground under them. The user did nothing wrong by merging a
finished PR.

So before any part is launched:

1. **File an issue per part.** Each gets its own `### Done when` checklist,
   covering only that part. `/orca:triage <n>` is the natural way, or file them
   directly per `../_shared/issue-schema.md`.
2. **Record the order as real dependency edges** — part B blocked by part A:

   ```bash
   gh issue edit <part-B> --add-blocked-by <part-A>
   ```

   This is what makes `/orca:status` show B as blocked and stops
   `/orca:launch` starting it early. Prose ordering in a plan is invisible to
   every readiness query.
3. **Decide what happens to the original issue.** Either it becomes the first
   part (keep it, narrow its criteria) or it stays as a tracking issue with the
   parts blocking it. Say which — an original issue left with the *whole* set of
   criteria will fail its gate forever, since no single part satisfies it.
4. **One plan file per part**, so each lane's contract carries only its own work.

Then each part launches as an ordinary lane when its blockers close.

**If the parts cannot be separated this way** — they share uncommitted state, or
part B is unverifiable without part A in the same tree — **it is not a split.**
Say so and plan it as one lane. "Three parts in one worktree" is not an
available shape.

After folding in review findings, invoke the `orca:launch` skill via the Skill
tool. It writes the executor contract, creates the worktree, launches the agent,
and stops. Then report: work planned, plan summary, review verdict, worktree,
branch, and contract path.

**Launch is DISQUALIFIED — stop and present instead — when any of these hold:**

- the review says split (never auto-launch a multi-context chain);
- a fork lacked an overwhelming recommendation (§3's bar) — state the open
  question as the reason, so an interactive session resumes exactly there;
- an **adopted** plan (§1a) drew a finding that would change its approach — the
  user wrote it, so rewriting it is theirs to decide;
- the work is already in flight (assignee, open PR, or live lane);
- Orca is unavailable — there is nowhere to launch. Present the plan instead and
  say why.

A disqualified launch is a successful plan, not a failure. Say which
disqualifier fired and what would clear it.
