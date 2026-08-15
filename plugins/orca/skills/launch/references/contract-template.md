# The executor contract — the template `/orca:launch` writes

§3 of `../SKILL.md` writes this file. It is the whole reason that skill exists
rather than a raw CLI call: it is what binds an executor to one issue, one
branch, one PR, and the criteria it will be gated against.

Fill in every section; omit one only when it genuinely has no content.

**Write it to an absolute path outside the repo** — a new checkout cannot see
another checkout's untracked files, but any absolute path is readable:

```
~/.claude/plans/<repo-name>/<YYYY-MM-DD>-<slug>.prompt.md
```

`<repo-name>` comes from the primary checkout, not the cwd basename.

## Three rules about the file

- **A contract is a snapshot, not a link.** It is written once and read by the
  executor; **updating this skill does not reach a lane already launched.** A
  contract written last week still binds its lane to last week's rules — which
  is correct (a running executor should not have the ground shift under it) but
  means a behavioral change here applies only to *future* launches.

  When a rule changes in a way that matters for work already in flight — the
  draft-PR change in 1.10.0 and the in-lane gate in 1.16.0 were both — the
  existing `.prompt.md` files under `~/.claude/plans/<repo>/` have to be edited
  directly, or their lanes will keep following the old instruction. Say so when
  reporting such a change.
- **Never overwrite an existing contract** — suffix the slug instead. An
  overwritten contract silently changes what a running lane was told to do.
- The launch prompt stays a **single short pointer sentence**. Everything
  multi-line lives here, so nothing has to survive shell quoting.

## The template

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

## Acceptance criteria

<The issue's ### Acceptance criteria checklist, VERBATIM. These are the acceptance
criteria. A cold agent will check this exact list against your branch at step 7,
before your PR opens, and /orca:verify re-checks it on demand afterwards.

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
5. Verify against the acceptance criteria above before considering the work
   done. Criteria that are prose rather than commands still need satisfying —
   they will be surfaced to a human reviewer.
6. Review your own full branch diff for bugs and regressions before pushing.
   Fix what is real, commit the fixes, re-run the tests.

   Then **spawn one fresh subagent to review the diff** — a cold reader, not a
   fork, so it does not inherit your assumptions. Give it three things: the
   acceptance criteria above, the Steps from this contract, and the branch diff
   (`git diff <merge-base>...HEAD`). Ask it two questions:

   > **1. Scope.** Does this diff implement what was asked — no more, no less?
   > Name anything in the diff that no criterion or step called for, and anything
   > called for that the diff does not do.
   >
   > **2. Durability.** Will this be hard to change later, or is it likely to
   > cause a bug? Judge against the conventions *this codebase already uses* —
   > not a style guide. Specifically: duplicated logic that will drift, a
   > function or type doing several unrelated jobs, a new hard-coded dependency
   > where the surrounding code injects, a change that forces edits in several
   > places whenever one thing changes, swallowed errors, missing edge cases at a
   > boundary the diff introduces.
   >
   > **Report only what you would block a PR over.** Skip naming, formatting,
   > and preferences between two reasonable structures. If you find nothing that
   > meets that bar, say so plainly — "no blockers" is a useful answer and the
   > expected one on most diffs. A long list of small findings is worse than a
   > short list of real ones, because it buries the real ones.

   Question 1 is the one you cannot do yourself: your own review shares every
   assumption that produced the code, so it catches typos but **not "I built
   something coherent that is not what was asked."**

   **Then act on the findings, with a hard bar on what you change:**

   - **Fix** anything that is a real defect or a genuine blocker — a bug, a
     swallowed error, an unhandled boundary, logic duplicated in a way that will
     silently drift.
   - **Fix** a structural problem *your own diff introduced* where the fix is
     local and obvious — extracting a second responsibility you just created,
     injecting a dependency you just hard-coded.
   - **Report, do not fix**, anything that would refactor code you did not write,
     or that trades working code for a principle. Put it in the PR body as a
     note, or file it as a follow-up issue. **A reviewer's opinion is not a
     mandate to rewrite** — scope creep justified by "best practice" is still
     scope creep, and it is exactly what question 1 exists to catch.

   Judge severity by consequence, not by rule: *would this cause a bug, or make
   the next change to this area meaningfully harder?* **If neither, it is a
   note.** Naming, formatting, a preference between two reasonable structures, a
   principle applied for its own sake — all notes. The default is to leave
   working code alone.

   **Run the reviewer once.** Do not re-review after fixing: a fresh read of the
   changed diff will always find something new, and that loop has no natural end.
   Fix what the one pass found, re-run the tests, and push. If a fix was large
   enough that you genuinely doubt it, that is a reason to **stop and report**,
   not to start another round.

   If the diff is off-plan in a way you cannot resolve, **stop and report**
   rather than opening a PR you would have to defend.
7. **Gate your branch — with an agent that did not write it.**

   Spawn **one fresh subagent** (a cold reader, not a fork) and have it run the
   evidence gate against your branch. Give it exactly four things:

   - the **`## Acceptance criteria` above, verbatim**
   - the **worktree path**, so it runs commands where the work is
   - the **base branch**, so it computes its own merge-base diff
   - the issue number, for the `Closes #<n>` check

   **Do not summarise your work for it, and do not tell it what you believe
   passes.** Its whole value is that it checks the branch instead of your account
   of the branch.

   <The gate procedure, pasted in full from `self-gate.md` at launch time. The
   executor cannot see this plugin, so a file path here would be unresolvable —
   inline the whole prompt.>

   It returns one of four verdicts — `PASS`, `PASS-AGENT-JUDGED`,
   `PASS-WITH-REVIEW`, or `FAIL` — with per-criterion evidence.

   **You do not grade your own work.** Act on what it reports, even where you
   disagree; if you think a `FAIL` is wrong, that is a thing to say in your final
   summary, not a thing to overrule.

7a. **If the verdict is `FAIL`, rework it — once, and narrowly.**

   - Fix **only the failed criteria**, using the evidence the gate gave you.
     Nothing else: no refactors, no adjacent improvements, no restructuring you
     have been meaning to do. A gate failure is not permission to reopen the
     diff. Scope creep justified by "while I was in there" is still scope creep.
   - Commit the fixes and **re-run the gate agent once** — a fresh one, given the
     same four inputs.
   - **A second `FAIL` ends it.** Do not fix again. Do not run a third gate.
     Go to step 8, open the PR anyway, post the failing verdict on it, and say
     plainly in your summary that the branch is **blocked**, which criteria are
     unmet, and what you tried. An honest blocked PR is useful; a lane silently
     grinding on the same criterion is not, and that loop has no natural end.
   - If the failure is something you cannot fix within the contract at all — the
     criterion contradicts the plan, or satisfying it needs a decision above your
     pay grade — **stop at the first `FAIL`** and report. Do not burn the rework
     pass on work you already know will not clear it.

8. Save durable learnings to memory BEFORE opening the PR — conventions or traps
   the next session would otherwise rediscover. Once this lane is finished it
   becomes eligible for cleanup, and anything unsaved goes with it.
9. Then, **on your own — do not wait to be told**: fetch and rebase onto the
   latest default branch, push, and open a PR. **A normal PR, not a draft**, so
   automated review tooling picks it up. The body MUST contain `Closes #<n>` —
   that line is what records completion when it merges; nothing else does, and
   nobody closes the issue by hand. (Omit if this work has no issue.)

   Open it when steps 5, 6 and 7 are genuinely satisfied: the criteria are met,
   the tests pass, your own review of the diff is clean, and the gate did not end
   on a second `FAIL`. **If the work is not done, say so and stop** — an honest
   "blocked on X" beats a PR you would not defend.

   **Then post the gate verdict as a comment on the PR you just opened**,
   exactly as the gate agent returned it — its first line carries the
   `orca:verify` tag that marks this branch as gated:

   ```bash
   gh pr comment <pr> --body-file <verdict file>
   ```

   Rebased since the gate ran? **Re-run the gate agent once** before commenting —
   evidence computed against a different base is stale, and a stale `PASS` is
   what someone merges on. (That re-run is not a rework pass; it re-checks
   unchanged work against a moved base.)

   **This comment is not optional and not a formality.** It is the only durable
   record that the branch was gated: without it `/orca:status` cannot tell a
   gated PR from an ungated one, and the person deciding to merge sees no
   evidence at the moment they decide.
10. **Never merge the PR.** A merge is the user's decision, always. Your gate
    verdict is evidence for that decision, never a substitute for it — state in
    your final summary that the PR is gated and awaiting human review, and quote
    the verdict. `/orca:verify <n>` re-gates on demand if anyone wants it checked
    again. Never write progress into a tracked file — no roadmap row, no
    status-board cell, no "mark done".

## Out of scope

<Explicit non-goals, especially adjacent work that looks related.>

## Finish with

Branch name, PR link, what was implemented, deviations and why, test results,
review findings and how they were resolved, and anything left for follow-up.

**The gate verdict, quoted** — which of the four it was, which criteria were
judged rather than proven, and whether a rework pass was used. If the branch
ended blocked on a second `FAIL`, lead with that: it is the most important thing
in the summary and must not be buried under a list of what went well.
```
