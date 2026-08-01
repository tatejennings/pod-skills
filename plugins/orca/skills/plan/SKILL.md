---
name: plan
description: Plan a piece of work end-to-end - a GitHub issue number, a milestone, or a free-form feature/bug description. Researches docs and codebase with parallel agents, drafts an execution-ready plan, then has a cold-reader agent adversarially review it for completeness, holes, single-context feasibility, and blast radius. Writes the "### Done when" acceptance checklist onto the issue, since that is what gates the work later. With --launch it hands the approved plan straight to a fresh agent in its own worktree via /orca:launch. Use when the user says "/orca:plan", "/orca:plan 84", "/orca:plan fix the vent double-tap bug", "plan issue N", "plan this feature", "plan milestone X", "help me plan this", or "plan and launch this". This plans; it does not implement. Handing work to a worktree agent is /orca:launch, and driving the Orca app directly is Orca's bundled orca-cli skill.
---

# Plan

Produce an execution-ready plan for the work in `$ARGUMENTS` — a GitHub issue, a
milestone, or a free-form description of a feature or bug. **You plan; you do not
implement.**

The plan will likely be handed to a fresh agent in its own worktree
(`/orca:launch`), so it must be self-contained: an executor sees the plan and
the issue, not this conversation.

Scale to the work. A milestone-sized chunk gets the full treatment; a small bug
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
`linkedIssue`), recent commits. Prefer those signals over any status file.

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
- Preserve the rest of the body. Read it, add or replace only the checklist
  section, and write it back through stdin.
- No issue (free-form work) ⇒ put the criteria in the plan's Verification
  section instead, and say the work has no issue to gate against.

## 4. Adversarial review

Spawn a **fresh** general-purpose agent — a cold reader, not a fork, so it does
not inherit your drafting bias. Give it the full plan and the requirements
source, and have it attack on four axes:

1. **Completeness** — is every requirement covered by a step? Does every step
   have a verification? Is every `### Done when` criterion actually produced by
   some step?
2. **Holes** — unstated assumptions, missing edge cases, migrations or format
   changes glossed over, test debt, doc obligations skipped.
3. **Single-context feasibility** — can ONE agent execute this end to end? One
   limit badly broken, or any two at once ⇒ split:
   - ≤ ~10 ordered steps
   - ≤ ~15 modified files (reads unlimited)
   - ≤ ~1,500 lines of new/changed code
   - at most ONE new subsystem or major architectural decision
   - repetitive same-shape edits: > ~25 by hand ⇒ script it or split it
   - expensive verify loops (> ~5 min/cycle): ≤ ~3 cycles; open-ended tuning
     always gets its own context
   - migrations of persisted formats count DOUBLE their file count

   The limits measure decisions held simultaneously, not raw file count. Failing
   ⇒ the finding is "split it", with proposed seams.
4. **Blast radius** — shared types, data formats, serialized content, test
   baselines, in-flight parallel work that could collide. Flag anything that
   makes the change hard to revert.

Fold real findings into the plan. Note what you dismissed and why — that is
ammunition against re-litigation later.

## 5. Present

- Present the final plan via `ExitPlanMode` for approval.
- If the review said split, **present the split as the plan**: ordered sub-plans,
  each independently handoff-able.
- Close by noting `/orca:launch` can start it in its own lane — but do
  not run it unasked; the user may execute inline.

## 6. `--launch` — hand off directly

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
