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

**Where the gate runs does not change that discipline.** A lane runs this
procedure on itself before opening its PR (`../launch/SKILL.md`), and
`/orca:verify` runs it again on demand. Both are bound by every rule here — in
particular, the lane's gate is performed by a **fresh agent that did not write
the code**, because an executor checking its own work is precisely the report
this file refuses to accept. A gate is defined by what it checks and what it
refuses to assume, not by who invoked it.

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

### 3. Human criteria — report, or have an independent agent judge them

Prose that is neither of the above. A machine cannot check these, so the default
is to surface them verbatim, marked as requiring human judgement, and **never**
count them as passed or failed.

This is the rule that keeps the gate honest, so it gets stated plainly:

> **Never guess at a human criterion.** Do not infer it from the diff, do not
> ask the executor whether it holds, do not mark it passed because the
> surrounding work looks good. A gate that quietly passes what it cannot check
> is worse than no gate — it launders an unverified claim into a verified one.

A verdict is never `pass` while human criteria are outstanding; it is
`pass-with-review`, which is a different thing and must be reported as such.

#### The one sanctioned exception — an independent agent's judgement

A gate that returns `pass-with-review` on every branch stops being read. The
outstanding criteria are the point of that verdict, and a verdict nobody opens is
the same as no gate at all — which is the failure this whole file exists to
prevent, arriving by a slower route.

So prose criteria **may** be judged, under three conditions that are not
negotiable:

1. **By a context that did not write the code.** A fresh agent, not the executor
   and not a fork of it. An implementer judging whether its own work satisfies a
   criterion is the executor's report wearing a different hat.
2. **Against the criterion verbatim and the branch diff** — the same inputs a
   human reviewer would get, and nothing the executor summarised for it.
3. **Recorded as judgement, never as evidence.** It is labelled as an opinion
   everywhere it appears, and it never produces a plain `pass`. That is what
   `pass-agent-judged` is for.

**The asymmetry is the safety property, and it only works in one direction:**

| The agent says | Weight | Effect |
|---|---|---|
| *criterion met* | An **opinion**. It never becomes evidence. | `pass-agent-judged` — merge-able, but visibly judged |
| *criterion not met* | **Actionable** — it read the diff and found a gap | `fail`, exactly as a failed command |
| *unsure* | Not a judgement at all | `pass-with-review` — hand it to a human |

A judging agent can therefore only ever make the gate **stricter** than the
machine checks alone, never more permissive: its `fail` blocks, and its `pass` is
still flagged as unproven. **Uncertainty resolves to `pass-with-review`, never to
`pass-agent-judged`** — an agent that is unsure and says "met" has laundered the
claim, and the label is the only thing standing between this exception and the
failure mode above.

Judging is **optional**. A gate that skips it and reports `pass-with-review` is
behaving correctly and always has been.

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

Exactly four, and the distinctions between the first three are load-bearing:

| Verdict | Meaning |
|---|---|
| `pass` | Every criterion checkable by machine passed, and there were **no** human criteria |
| `pass-agent-judged` | Every checkable criterion passed, and ≥1 human criterion was **judged met by an independent agent** — opinion, not evidence. **List what was judged** |
| `pass-with-review` | Every checkable criterion passed, but ≥1 human criterion is **unjudged** and needs a person — **list them** |
| `fail` | ≥1 checkable criterion failed, **or** an independent agent judged a human criterion unmet — **name which, with its evidence** |

The three passing verdicts are not interchangeable, and collapsing them is the
one change to this file that would break it. They say, in order: *proven*,
*someone competent looked and thinks so*, and *nobody has checked this yet*.
Reporting the second or third as the first launders an unverified claim into a
verified one.

**Every verdict comment must carry the literal `orca:verify` tag**, whatever the
verdict. That tag — not the verdict word — is how `/orca:status` tells a gated PR
from an ungated one (`../status/SKILL.md`). A verdict comment without it is
invisible to the dashboard, which is indistinguishable from never having gated.

**Verified**: matching on the verdict words instead is unsafe. `"CI FAILED on
this branch"`, `"the tests PASS now"`, and `"I will PASS on reviewing this
today"` all match a `PASS|FAIL`-style pattern, and any of them would make an
ungated PR read as gated. Ordinary English in a PR thread contains these words;
the `orca:verify` tag does not occur by accident.

What the gate does with a verdict:

- Any passing verdict ⇒ report it, **and post the verdict as a PR comment** —
  that comment is the only durable record that the branch was gated, and the only
  thing distinguishing a gated PR from an ungated one. Under `pass-with-review`
  the human criteria go first; under `pass-agent-judged` the judged criteria go
  first, each with the agent's reasoning, so a reviewer can disagree with it.
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

## The verdict comment — one format, two producers

Both the in-lane gate and `/orca:verify` post this, so the shape is defined once,
here. The first line is what `/orca:status` matches on; everything below it is
for the human deciding whether to merge.

```markdown
<!-- orca:verify -->
**orca:verify — PASS-AGENT-JUDGED** · #84 · `feat/audio-enum` · gated in-lane before PR

⊙ Importing a malformed file surfaces an error instead of crashing
    AGENT JUDGEMENT — not machine evidence
    `import.go:112` returns a wrapped error on a short header; the caller at
    `cmd/load.go:44` surfaces it. No panic path found for this input.

✓ `./scripts/test.sh` exits 0
✓ `docs/api.md` is modified
✓ `Closes #84` present in the PR body
```

Rules that make it work:

- **The literal `orca:verify` tag on line 1**, always, whatever the verdict. It
  is the only thing distinguishing a gated PR from an ungated one, and the regex
  looks for it.
- **The verdict in caps**: `PASS`, `PASS-AGENT-JUDGED`, `PASS-WITH-REVIEW`, `FAIL`.
  **Case is part of the contract**, and the two casings are not interchangeable:
  UPPERCASE is the literal string on the wire — what a producer writes and what
  `/orca:status` and `/orca:tech-lead` match against. The lowercase forms used in
  the tables above and in prose elsewhere are the *names* of the verdicts, never
  a string to emit or grep. A skill that "tidies" a wire string to lowercase
  breaks the match silently, and a broken match reports a gated PR as ungated.
- **Say where it ran** — `gated in-lane before PR` or `re-gated on demand`. A
  reviewer should not have to guess whether a human asked for this.
- **Markers**: `✓` verified, `✗` failed, `⊙` agent-judged, `?` awaiting human.
  `⊙` and `?` are different claims and must not share a glyph.
- **Judged and failed criteria go first**, with reasoning. A reviewer who reads
  only the top of the comment must see the parts that are not proven.
- **Re-gating adds a new comment; it never edits the old one.** The history of
  what a branch was gated against is worth more than a tidy PR thread.
