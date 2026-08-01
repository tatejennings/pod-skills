---
name: triage
description: Work through a batch of issues with you, one at a time, turning each into something plannable - asks what it actually means, what "done" looks like, how urgent it is, which milestone it belongs in, and what it depends on, then writes the "### Done when" checklist, sets the milestone and labels, and records real dependency edges. Given no arguments it audits the whole open backlog first, catching both never-triaged issues and ones that have drifted since - a stale blocked label whose blocker already closed, a dependency written only in prose, criteria under the wrong heading, an issue filed by hand on GitHub that never got a milestone. Use when the user says "/orca:triage", "triage the backlog", "audit the issues", "go through these issues", "check the backlog for drift", "let's prioritize", "clean up the backlog", "groom the backlog", "schedule these", "are the tickets up to date", "what's in the backlog", or hands over a pile of bugs, features, or research items to sort out. This grooms individual issues; migrating a repo's whole tracking model or auditing it structurally is /orca:migrate, and planning the implementation of one issue is /orca:plan.
---

# Triage

Turn raw issues into plannable ones, **one at a time, with you**.

An issue is plannable when someone else could pick it up and know what to build
and when to stop. Most captured issues are not: a title, a sentence, no
milestone, no acceptance criteria. This skill closes that gap by asking — never
by guessing.

Read `../_shared/issue-schema.md` for the target shape and
`../_shared/github-backlog.md` for every `gh` query. Do not restate them.

## What this skill is not for

- **Migrating a repo's whole tracking model** (files, conventions, the
  `AGENTS.md` block, the schema version) ⇒ `/orca:migrate`. Both skills audit,
  at different altitudes: `/orca:migrate` checks **repo-level structure** — is
  the tracking block intact, has a tracked file started regrowing progress rows,
  is the repo on the current schema. This skill checks **per-issue hygiene** —
  criteria, milestones, dependency edges, labels. Neither subsumes the other.
- **Planning how to implement an issue** ⇒ `/orca:plan`. Triage decides *whether
  and when*; planning decides *how*.
- **Deciding what to work on now** ⇒ `/orca:status`.

## 0. Preconditions

```bash
gh auth status
gh repo view --json nameWithOwner -q .nameWithOwner
```

Confirm the **active** account can write to the resolved repo before touching
anything. Wrong account ⇒ stop.

## 1. Assemble the batch — up front, in one pass

`$ARGUMENTS` may be issue numbers (`84 91 95`), a filter, or empty. Resolve to a
concrete list **before asking anything**, so the user knows the size of what they
are agreeing to.

Default when `$ARGUMENTS` is empty — everything that looks untriaged:

```bash
gh issue list --state open --limit 200 \
  --json number,title,body,milestone,labels,assignees,blockedBy
```

**With no arguments, audit the whole open backlog** — not just never-triaged
issues, but ones that have *drifted*. An issue triaged three weeks ago can be
wrong today, and an issue filed by hand on GitHub never passed through here at
all. Both are this skill's job.

Flag an issue when any of these hold:

**Never triaged**

- no milestone (and it is not obviously a tracking/meta issue);
- no `### Done when` checklist, or one that is empty;
- a body under ~2 lines — a captured thought, not a specification.

**Drifted since it was triaged**

- **A `blocked` label whose blockers have all closed** — the issue is ready and
  the label says otherwise. Read `blockedBy.nodes[].state`, never `totalCount`
  (`../_shared/github-backlog.md`).
- **A dependency written only in prose** — a `**Prereqs:**` line, "after X
  lands", "requires Y" — with no matching edge. Invisible to every readiness
  query, so the issue reports ready when it is not. This is the most consequential
  drift and the easiest to miss.
- **Criteria under the wrong heading** — acceptance criteria present as prose or
  under a heading that is not `### Done when`. The fix is a rename, **not**
  authoring new criteria.
- **A milestone that has closed** while the issue stayed open.
- **No scope label** — nothing saying which part of the system the work touches.
  Reuse an existing label or create one named for the area, per
  `../_shared/issue-schema.md`.
- **Labels the repo no longer uses**, or a missing one the convention expects
  (infer the convention from what the majority of issues carry; do not impose
  one).
- **Inconsistent label naming** — some multi-word labels with spaces, others
  with hyphens. Report it once for the repo rather than per issue; it is a
  label-set problem, and normalizing means recreating labels and moving every
  issue, which is the user's call.
- **An assignee but no activity for a long time** — worth one question: still
  yours, or hand it back?

Report drift and never-triaged separately in the batch summary — they need
different questions. A drifted issue usually needs one confirmation; a raw one
needs the full pass.

Also accept a **pasted list** — if the user drops in bullet points, bug reports,
or a wishlist that are not yet issues, treat each as a batch item and file it in
§3 as part of triaging it. Do not create every issue up front and then triage
them; an item the user drops mid-pass should never have been filed.

**Report the batch and get a go-ahead:**

```
17 open issues · 8 need attention

NEVER TRIAGED (5)
  #95  Post-1.0 ideas & deferrals         no milestone, no criteria
  #96  Verification debt: CI What-to-Test no milestone
  #101 crash on rotate                    1-line body, no criteria
  … 2 more

DRIFTED (3)
  #88  K2 · Live-run handoff              `blocked` label, but #87 closed
  #92  W2 · Content model split            "Prereqs: W1" in prose, no edge
  #90  F2 · Ship ops                       criteria present, wrong heading

Work through these one at a time? (or name a subset)
```

**Mechanical drift can be fixed without asking**, if the user agrees once up
front: a stale `blocked` label whose blockers are all closed, or criteria under
the wrong heading, have exactly one correct fix. Offer them as a batch —
*"3 mechanical fixes, apply them all?"* — and reserve the one-at-a-time pass for
anything needing judgement. A prose dependency is **not** mechanical: resolving
which issue `W1` means is a guess unless the title matches exactly, and a wrong
edge hides available work.

Cap a single session at ~10 judgement items. Past that, say how many remain and
offer to continue — triage is judgment work and quality falls off long before
item 20. Mechanical fixes do not count against the cap.

## 2. One issue at a time

For each item in the batch, in order. **Never batch the questions across
issues** — the user answers for one issue, it gets written, then the next. That
is what keeps a long batch tolerable and lets them stop anywhere.

Read what is already there, then ask **only what is genuinely missing.** An
issue that already has a clear scope and criteria may need nothing but a
milestone; asking six questions about it wastes the user's attention and trains
them to skim.

**A drifted issue usually needs one question, not the full pass.** It was
triaged once; something changed underneath it. Ask about the drift and nothing
else — *"#88's blocker #87 closed. Drop the `blocked` label and treat it as
ready?"* Re-interrogating an issue that is already well-formed is exactly what
makes an audit feel like a chore.

The questions worth asking, in rough priority:

- **What does this actually mean?** For a one-line capture: what is the observed
  behavior, or the desired one? For a bug: what happens, what should happen, how
  do you reproduce it?
- **What would "done" look like?** The most important question, and the one that
  becomes the `### Done when` checklist. Push for something observable. "It
  works" is not a criterion; "the importer rejects a malformed header with an
  error instead of crashing" is.
- **When?** Which milestone — or explicitly none, meaning unscheduled backlog.
  Offer the open milestones by name; do not invent one.
- **How urgent, relative to its milestone?** Only worth asking when the milestone
  already has a priority convention. Priority ranks *within* a milestone; the
  milestone is what says when.
- **Does it depend on anything?** Name candidates from the batch and the
  milestone. Record answers as **real edges**, not labels (§3).
- **Which part of the system does it touch?** Offer the repo's existing scope
  labels; if none fits, propose a new one named for the area
  (`../_shared/issue-schema.md`). Never leave scope unlabelled because nothing
  matched — a new label costs nothing, and unlabelled work is invisible to any
  grouping.
- **Can an agent do this at all?** Ask when it is not obvious. Work behind
  credentials, store or console configuration, a physical device, a purchase, or
  a legal review is `manual` — the whole task, not just some criteria. Mark it
  so `/orca:launch` refuses to launch it and `/orca:status` lists it under YOUR
  TASKS (`../_shared/issue-schema.md`).
- **Is it already done, or no longer wanted?** Always worth offering — closing a
  stale issue is a legitimate and common triage outcome.

Use AskUserQuestion for anything with discrete options (milestone, priority,
kind). Ask open questions as prose. **Never invent an answer** — an unanswered
question means the field stays empty and the issue stays untriaged, which is an
honest outcome.

### Writing the `### Done when` checklist

This is the part that makes the issue gateable later, so it gets the care
`../_shared/issue-schema.md` demands:

- Turn the user's words into criteria; do not editorialize them into something
  they did not say.
- **Prefer checkable forms** — a command that must exit 0, a string that must
  appear in the diff, a file that must change.
- **Write prose for what genuinely cannot be checked**, and mark it as such. A
  research item's honest criterion is often "a written finding at
  `docs/specs/<slug>.md`" — that is legitimate, not a failure.
- **Never fabricate a criterion to look thorough.** A short honest checklist
  beats a long invented one, which would pass a gate that should have failed.
- Read the criteria back before writing them, in one line each. It is much
  cheaper to correct them now than after an executor has built the wrong thing.

## 3. Write it, then move on

Per issue, once the questions are answered:

```bash
# body: preserve everything, add or replace only the ### Done when section
gh issue edit <n> --body-file - <<'EOF'
<full body>
EOF

gh issue edit <n> --milestone "<name>"          # or --remove-milestone
gh issue edit <n> --add-label "<label>"
gh issue edit <n> --add-blocked-by <blocker>    # real edge, never a label alone
```

For a batch item that is not yet an issue:

```bash
gh issue create --title "<t>" --body-file - <<'EOF'
<body with ### Done when>
EOF
```

Rules that matter:

- **Preserve the existing body.** Read it, add or replace only the checklist
  section, write it back through stdin. Never `--body "…"` — quoting eats it.
- **Blocking is an edge, not a label.** A `blocked` label may mirror it for the
  issue list, but the edge is what readiness reads
  (`../_shared/github-backlog.md`).
- **No milestone is a valid answer** and means unscheduled backlog. Do not
  invent a "Backlog" milestone.
- **Confirm each write in one line** (`#101 → v1.1, 3 criteria, blocked by #99`)
  and move to the next issue. No summary essay per item.

## 4. Close out

When the batch is done — or the user stops early:

- **What changed**: a compact table of issue, milestone, criteria count,
  dependencies recorded.
- **What was skipped**, and why — deferred, or a question went unanswered. These
  stay untriaged, which is correct rather than a failure.
- **How many untriaged issues remain**, if the batch was capped.
- **What is now ready to plan** — anything that came out of triage with a
  milestone, criteria, and no open blockers is `/orca:plan` input, and saying so
  closes the loop.

**A clean audit still reports what it checked**, in one line — *"17 open issues:
all have milestones, criteria, and dependency edges matching their labels."*
"Nothing to do" alone is indistinguishable from a run that failed to look, and
this skill is meant to be re-run periodically.

## Failure modes to avoid

- **Batching questions across issues.** One issue at a time, always.
- **Asking what the issue already answers.** Read first; ask only the gaps.
- **Fabricating acceptance criteria** because the user's answer was vague. Ask
  again, or leave it and say so.
- **Guessing a milestone.** Offer the real ones; accept "none".
- **Recording a dependency as a label only.** The edge is the mechanism.
- **Rewriting the user's issue body** beyond the checklist section.
- **Grinding through 30 issues in one pass.** Cap it and offer to continue.
- **Re-interrogating a drifted issue.** It was triaged once — ask about the
  drift, not everything.
- **Treating a prose dependency as mechanical.** Resolving which issue `W1`
  means is a judgement call, and a wrong edge hides available work.
- **Reporting a clean backlog as "nothing to do" without saying what was
  checked.** An audit that finds nothing should say what it looked for.
- **Treating bugs, features, and research as different workflows.** They are
  not — the questions are the same, and only the label differs. A research
  item's "done" is a written finding.
