# Evidence gates — how a criterion gets checked

The mechanics behind `/orca:verify`. `issue-schema.md` defines how a criterion is
**written**; this file defines how one is **checked**, what counts as evidence,
and the rules that keep a gate honest.

This file is **project-agnostic by construction**. It contains no project's
acceptance criteria and never should — those live in the consuming repo's own
issues. What is general is the machinery: the three buckets, the evidence rules,
and the failure modes below.

## Why this exists

A PR existing proves nothing about whether the work is right. The specific
failure this guards against: an agent optimizes a proxy for the real goal,
carries forward numbers measured before its own change, trims an inconvenient
test, and opens a polished, confident PR that closes an issue it did not
satisfy. Every artifact looks correct. The only thing that would have caught it
is checking the issue's own criteria against the branch — mechanically, without
asking the author.

So the gate's core discipline: **evidence comes from the branch and the
commands, never from the executor's report of them.**

## The three buckets

Every `### Done when` item lands in exactly one (see `issue-schema.md` for the
forms):

### 1. Command criteria — run them

The item names a command. Run it **in the worktree under test**, capture exit
code and output.

- Exit 0 ⇒ pass. Non-zero ⇒ fail, and quote the last ~20 lines of output.
- A command that does not exist ⇒ **fail**, not skip. "The test script is
  missing" is a real finding, not an absent criterion.
- Never substitute a different command because the named one failed to run.
  Never "fix" the command and re-run. Report what happened.
- Respect a timeout; a hanging command is a fail with that reason stated.

### 2. Diff assertions — grep the branch

The item asserts something about what changed. Compute the branch diff against
its merge base and search it:

```bash
git -C <path> merge-base HEAD <base>
git -C <path> diff <merge-base>...HEAD
```

- `` `<string>` appears in the diff`` ⇒ search **added lines**, not the whole
  diff. A string appearing in a *removed* line is the opposite of the claim.

  ```bash
  git -C <path> diff <merge-base>...HEAD | grep '^+' | grep -c '<string>'
  ```

  **Verified**: on a branch that *deleted* the required token, a whole-diff grep
  returned 1 match and would have passed; the added-lines grep returned 0 and
  correctly failed. This is not a hypothetical distinction.
- `` `<path>` is modified`` ⇒ check the changed-file list
  (`git diff --name-only <merge-base>...HEAD`).
- **Novelty matters when the criterion says it does.** If a criterion requires a
  *new* artifact — a new report, a new entry, a new id — then finding a
  pre-existing one is a **fail**. An unchanged file that already satisfied the
  string never satisfies a criterion about producing it.

  For a new *file*, the check is the added-files list plus a merge-base probe —
  existence alone proves nothing:

  ```bash
  git -C <path> diff --name-only --diff-filter=A <merge-base>...HEAD   # added on this branch?
  git -C <path> cat-file -e <merge-base>:<path> 2>/dev/null            # existed before? ⇒ not new
  ```

  **Verified**: against a branch that touched neither, a naive "does the file
  exist" check passed while the correct check failed.

### 3. Human criteria — report, never assert

Prose that is neither of the above. These are surfaced verbatim, marked as
requiring human judgement, and **never** counted as passed or failed.

This is the rule that keeps the gate honest, so it gets stated plainly:

> **Never guess at a human criterion.** Do not infer it from the diff, do not
> ask the executor whether it holds, do not mark it passed because the
> surrounding work looks good. A gate that quietly passes what it cannot check
> is worse than no gate — it launders an unverified claim into a verified one.

A verdict is never `pass` while human criteria are outstanding; it is
`pass-with-review`, which is a different thing and must be reported as such.

## Evidence rules

**Check the branch, not the report.** The executor's summary is a claim about
the work; it is not evidence of the work. Read the diff and run the commands.

**Never trust a checkbox.** `- [x]` in an issue body means a human or an agent
typed an `x`. It carries no information about the world. Compute every criterion
from scratch, every run.

**Stale evidence is not evidence.** If a criterion depends on a measurement
(benchmark output, a generated report, a captured metric), that measurement must
postdate the last commit that could have changed it. Evidence produced before
the change it supposedly validates is a **fail**, and one of the easiest failure
modes to miss on a fast read.

**Re-derive on every run.** No caching between runs. The whole design of the gate
is that it rebuilds truth; a cached pass is exactly the stored state this model
exists to avoid.

## Universal criteria

These apply to any repo using this plugin's tracking model and are checked in
addition to the issue's own checklist:

- **`Closes #<n>` in the PR body**, naming the issue under verification.
  Missing ⇒ fail: the merge will not close the issue, and completion is recorded
  by nothing else.
- **No progress written to a tracked file.** If the diff modifies a tracked
  roadmap, status board, or TODO to record completion, that is a fail — see the
  guard in `github-backlog.md`. A *generated, gitignored* roadmap appearing in
  the diff is likewise a fail: it should not be committable at all.
- **The branch is not behind its base in a way that invalidates the evidence.**
  If the base has moved substantially, say so — the commands passed against an
  older tree.

## Verdicts

Exactly three, and the distinction between the first two is load-bearing:

| Verdict | Meaning |
|---|---|
| `pass` | Every criterion checkable by machine passed, and there were **no** human criteria |
| `pass-with-review` | Every checkable criterion passed, but ≥1 human criterion needs judgement — **list them** |
| `fail` | ≥1 checkable criterion failed — **name which, with its evidence** |

What the gate does with a verdict:

- `pass` / `pass-with-review` ⇒ report it, **and post the verdict as a PR
  comment** — that comment is the only durable record that the branch was gated,
  and the only thing distinguishing a gated PR from an ungated one. The human
  criteria in `pass-with-review` go first; they are what a reviewer should look
  at.
- `fail` ⇒ comment the unmet criterion and its evidence on
  the PR so the executor (or the next session) can act on it.

**The gate never merges, and never closes an issue by hand.** Merging is the
human's decision, always; closing happens via `Closes #<n>` when they merge.
A gate with merge authority is no longer a gate.

## Reporting a failure

A failing gate must be *actionable*. For each failed criterion give: the
criterion verbatim, what was checked, what was found, and the raw evidence
(command output, the missing string, the absent file). "Criterion 3 failed" is
useless; "`./scripts/test.sh` exited 1 — 2 failing tests, output below" is a
next action.

Report **every** failed criterion, not just the first. An executor that fixes one
failure at a time because the gate reported one at a time wastes an entire cycle
per criterion.
