# Executor steps

<!-- Copied beside every executor contract by /pod:launch. Static: everything specific to one
     lane is in the contract that pointed here. -->

Your contract says what to build. This file says how to work, and it binds you
as fully as the contract does. "Your contract" below means the file that sent
you here.

## How to work

1. You are in a fresh worktree with a branch already checked out. Confirm with
   `git status` — do not create another branch.
2. Follow the repo's CLAUDE.md / AGENTS.md rules (naming, required doc updates,
   test commands).
3. Implement step by step. Commit in logical increments with clear messages.
4. If reality contradicts your contract on details, adapt and record the
   deviation for your final summary. **If the core approach turns out to be
   wrong, stop and report back** instead of improvising a new design.
5. Verify against the acceptance criteria in your contract before considering the work
   done. Criteria that are prose rather than commands still need satisfying —
   they will be surfaced to a human reviewer.
6. Review your own full branch diff for bugs and regressions before pushing.
   Fix what is real, commit the fixes, re-run the tests.

   Then **spawn one fresh subagent to review the diff** — a cold reader, not a
   fork, so it does not inherit your assumptions. Give it three things: the
   acceptance criteria and the plan from your contract, and the branch diff
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

   Spawn **one fresh subagent** (a cold reader, not a fork). Tell it to read the
   **gate prompt file** named under `## Files` in your contract and follow it
   exactly, and give it these inputs and nothing else:

   - **Criteria** — your contract's `## Acceptance criteria`, verbatim
   - **Worktree path** — this worktree's absolute path
   - **Base branch** — from your contract's `## Files`
   - **Issue number** — from your contract, or `none` if it names no issue
   - **Mode** — `gated in-lane before PR`
   - **Judge prose criteria** — `yes`

   **Do not summarise your work for it, and do not tell it what you believe
   passes.** Its whole value is that it checks the branch instead of your account
   of the branch.

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
     same six inputs.
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
   automated review tooling picks it up. The body MUST contain `Closes #<issue number>` —
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
   record that the branch was gated: without it `/pod:status` cannot tell a
   gated PR from an ungated one, and the person deciding to merge sees no
   evidence at the moment they decide.
10. **Never merge the PR.** A merge is the user's decision, always. Your gate
    verdict is evidence for that decision, never a substitute for it — state in
    your final summary that the PR is gated and awaiting human review, and quote
    the verdict. `/pod:verify` re-gates on demand if anyone wants it checked
    again. Never write progress into a tracked file — no roadmap row, no
    status-board cell, no "mark done".

## Finish with

Branch name, PR link, what was implemented, deviations and why, test results,
review findings and how they were resolved, and anything left for follow-up.

**The gate verdict, quoted** — which of the four it was, which criteria were
judged rather than proven, and whether a rework pass was used. If the branch
ended blocked on a second `FAIL`, lead with that: it is the most important thing
in the summary and must not be buried under a list of what went well.
