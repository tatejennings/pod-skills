---
name: verify
description: The evidence gate, run on demand - check a finished branch or PR against its issue's own "### Acceptance criteria" acceptance checklist, mechanically. Runs the criteria that are commands, greps the branch diff for the criteria that are diff assertions, and handles the ones only a human can judge, then reports pass / pass-agent-judged / pass-with-review / fail with the evidence for each. Verifies the branch and the commands, never the executor's report of them. Posts the verdict as a PR comment, which is the durable record that a branch was gated. Never merges and never closes an issue. Lanes already gate themselves before opening a PR, so this is usually a RE-gate - use it when the base has moved, when new commits landed after the verdict, when a verdict looks wrong, or when /orca:status shows a PR as ungated (awaiting-gate). Use when the user says "/orca:verify", "/orca:verify 84", "verify this branch", "re-verify", "check the acceptance criteria", "did this actually satisfy the issue", "gate this PR", "is this PR ready", "this PR was never gated", or "the gate verdict looks wrong". Also use for "did the agent actually finish this", "check the lane's work", "prove this is done", or "does this meet the criteria". Not for reviewing code quality or finding bugs - that is a code review, use /code-review or /review instead; this checks only whether the issue's stated criteria are met, and it is not CI.
---

# Verify — the evidence gate

Check a branch against **the acceptance criteria its issue already declared**,
and report what is actually true. A PR existing proves nothing about whether the
work is right; this is the step that asks.

Read `../_shared/evidence-gates.md` for the checking mechanics and
`../_shared/issue-schema.md` for the criterion forms. **Do not restate them
here** — this file is the procedure, those are the rules.

The discipline that makes this worth running, stated once:

> **Evidence comes from the branch and the commands, never from the executor's
> report of them.** Read the diff. Run the commands. A summary claiming the work
> is done is the thing being checked, not the check.

## Usually a re-gate, not the first gate

Lanes gate themselves before opening a PR (`../launch/SKILL.md` step 7), so most
PRs already carry a verdict comment. Running this skill is then a **re-gate**,
and it is worth doing when:

- **the base has moved** since the verdict was posted — the evidence was computed
  against a different tree, and a stale `pass` is what someone merges on;
- **a verdict looks wrong**, or rests on a judged criterion a reviewer doubts;
- **new commits landed** on the branch after the gate ran;
- the PR is **ungated** (`/orca:status` shows `awaiting-gate`) — the lane skipped
  its gate or died before reaching it.

Two rules for a re-gate, both consequences of "re-derive on every run"
(`../_shared/evidence-gates.md`):

- **Never read the existing verdict as input.** Do not confirm it, do not start
  from it, do not skip a criterion it already passed. A cached pass is exactly
  the stored state this model exists to avoid, and a verdict inherited from a
  previous tree is indistinguishable from one that was never checked.
- **Add a comment; never edit the old one.** The sequence of verdicts is the
  record of what the branch has been through, and it is worth more than a tidy
  thread.

## What this skill is not for

- **Finding bugs / reviewing code quality** ⇒ a code review. This asks a narrower
  question: were the stated criteria met?
- **Merging, or marking a PR ready** ⇒ never. `pass` is a report; a human acts on
  it. See §6.
- **Deciding what the criteria should be** ⇒ `/orca:plan` writes them,
  `/orca:migrate` retrofits them. This skill only checks.

## 0. Resolve the target

`$ARGUMENTS` may be an issue number, a PR number, a branch, or empty.

Resolve to **three things — issue, branch, PR** — since the gate needs all of
them:

- **Issue number** ⇒ find its lane (`orca worktree ps --json`, `linkedIssue`) or
  its PR (`gh pr list --json number,headRefName,closingIssuesReferences`).
- **PR number** ⇒ `gh pr view <n> --json number,headRefName,headRefOid,isDraft,state,body,url,closingIssuesReferences`;
  the issue comes from `closingIssuesReferences`.
- **Branch** ⇒ match it against the PR list.
- **Empty** ⇒ use the current worktree (`orca worktree current --json`); its
  `linkedIssue` and branch are the target.

**No issue ⇒ stop.** The criteria live on the issue; with no issue there is no
gate. Say that plainly rather than inventing something to check.

**No PR yet** is fine — verify the branch directly and say the PR does not exist.

## 1. Read the criteria

```bash
gh issue view <n> --json number,title,body,state,url
```

Extract the `### Acceptance criteria` checklist verbatim.

**No `### Acceptance criteria` section ⇒ STOP.** Report that the issue declares no
acceptance criteria and therefore cannot be gated. Do **not** infer criteria from
the title, the diff, or the PR description — inventing criteria and then passing
them is the exact failure this gate exists to prevent. Point at `/orca:plan` or
`/orca:migrate` to establish them.

**Never read the checkbox state.** `- [x]` means someone typed an `x`; it is not
evidence. Every criterion is computed from the world, every run.

Sort each item into a bucket per `../_shared/issue-schema.md`: **command**,
**diff assertion**, or **human**. When the form is ambiguous, classify it
**human** — deferring to a person is always safer than running an arbitrary
sentence or asserting something you guessed at.

## 2. Establish the branch under test

```bash
git -C <path> merge-base HEAD <base>
git -C <path> diff --name-only <merge-base>...HEAD
git -C <path> diff <merge-base>...HEAD
```

`<base>` is the PR's `baseRefName`, or the repo default branch.

Two things to check before trusting any result:

- **Uncommitted changes** (`git status --porcelain` non-empty) ⇒ say so. The
  commands may pass against work that is not in the PR, which would make the
  whole run misleading.
- **A base that has moved** ⇒ this is not a footnote; it bounds how long the
  verdict is worth anything.

  ```bash
  git -C <path> rev-list --count HEAD..<base>     # commits the branch is behind
  ```

  Behind by anything ⇒ **say so on the verdict itself**: *"evidence computed
  against a base N commits behind; re-run after rebasing."* A gate whose result
  silently expires is worse than one that never ran, because the stale `pass` is
  what a human merges on.

  Behind **and no longer merging cleanly** ⇒ that is a **fail**, not a note. The
  branch cannot land as-is, so no criterion about it is meaningful yet:

  ```bash
  gh pr view <n> --json mergeable,mergeStateStatus
  ```

## 3. Run the checkable criteria

**Command criteria** — run each in the worktree, capture exit code and output:

- Exit 0 ⇒ pass. Non-zero ⇒ fail, quoting the last ~20 lines.
- Command missing ⇒ **fail**, not skip. "The test script is gone" is a finding.
- Never substitute a different command, never fix the command and re-run.
- Timeout ⇒ fail, saying so.

**Diff assertions** — search the diff computed in §2:

- `` `<string>` appears in the diff`` ⇒ search **added lines only**. A string in
  a removed line is the opposite of the claim.
- `` `<path>` is modified`` ⇒ check the changed-file list.
- **Novelty:** if the criterion demands something *new*, confirm it is in the
  added lines and did **not** exist at the merge base. A pre-existing artifact
  never satisfies a criterion about producing one.
- **Staleness:** if a criterion rests on a measurement (a benchmark, a generated
  report, a captured metric), that measurement must postdate the last commit that
  could have changed it. Evidence produced before the change it supposedly
  validates is a **fail**, and it is the easiest failure to miss.

**Human criteria** — do not check them. Collect them verbatim for §5.

## 4. Universal criteria

Checked on every run, in addition to the issue's own list
(`../_shared/evidence-gates.md`):

- **`Closes #<n>` in the PR body**, naming this issue. Missing ⇒ **fail**: the
  merge will not close the issue and nothing else records completion. (Skip if
  there is no PR yet; say so.)
- **No progress written to a tracked file.** A tracked roadmap, status board, or
  TODO modified to record completion ⇒ fail. A generated `ROADMAP.md` appearing
  in the diff ⇒ fail; it should not be committable.
- **Base not stale** — from §2.

## 5. Verdict

Four, and the three passing ones are genuinely different
(`../_shared/evidence-gates.md` defines them; this is the summary):

| Verdict | Meaning |
|---|---|
| `pass` | Every checkable criterion passed, and there were **no** human criteria |
| `pass-agent-judged` | Every checkable criterion passed, and ≥1 human criterion was **judged met by an independent agent** — opinion, not evidence |
| `pass-with-review` | Every checkable criterion passed, but ≥1 human criterion is **unjudged** and needs a person |
| `fail` | ≥1 checkable criterion failed, **or** an agent judged a human criterion unmet |

**Never report `pass` while human criteria are outstanding.** That is
`pass-with-review`, and the outstanding items must be listed — they are exactly
what a reviewer should look at first. A gate that quietly passes what it could
not check launders an unverified claim into a verified one.

**Judging is optional here.** Running this skill by hand usually means a human is
already in the loop, so leaving prose criteria for them and reporting
`pass-with-review` is the right default. Judge them when asked to, or when the
verdict is destined for a PR nobody will read before merging — and label it, per
the rules in `../_shared/evidence-gates.md`. **Unsure is never
`pass-agent-judged`.**

## 6. Report — and act only within limits

Lead with the verdict, then every criterion with its evidence:

```
FAIL — 2 of 5 criteria unmet          #84 · branch feat/audio-enum · PR #91

✗ `./scripts/test.sh` exits 0
    exited 1 — 2 failing tests:
      FAIL  audio/device_test.go:44  expected 2 devices, got 0
      …
✗ a new report id appears in the diff
    no added line matches; `reports/` unchanged since the merge base

✓ `docs/api.md` is modified
✓ `Closes #84` present in the PR body

? Importing a malformed file surfaces an error instead of crashing
    HUMAN JUDGEMENT — not checked
```

Markers: `✓` verified, `✗` failed, `⊙` agent-judged, `?` awaiting human. **`⊙`
and `?` are different claims** — one says an agent looked and thinks it holds,
the other says nobody has checked — so they never share a glyph. The PR comment
uses the same set (`../_shared/evidence-gates.md`, "The verdict comment").

**Report every failed criterion, not just the first.** An executor that fixes one
failure per cycle because the gate reported one per cycle wastes an entire round
trip each time.

What may be done with a verdict:

- **`fail`** ⇒ comment the unmet criteria and their evidence
  on the PR — that is the durable record. Never mark it ready.

  **Then name the next action, because a comment is not one.** Offer
  `/orca:launch <n>`, which has a rework path (§1a there): it reuses the existing
  lane, carries these failed criteria and their evidence into the contract, and
  tells the executor to push to the existing PR rather than opening a second. Say that explicitly — otherwise the user re-derives all of it by hand
  in a fresh session and loses every constraint the contract encodes.

  **If the lane already failed its own gate twice**, say so plainly rather than
  offering rework as though it were the first attempt. A branch that has now
  failed three times is evidence about the *criteria or the approach*, not about
  the executor, and another lap is unlikely to be the answer.
- **Any passing verdict** ⇒ report it, **and post the verdict as a PR comment.**
  Not just on fail: the comment is the only durable record that this branch was
  gated. Without it the verdict lives in a session transcript, a reviewer on
  GitHub cannot see the evidence at the moment they decide to merge, and
  `/orca:status` cannot tell a gated PR from an ungated one — they look
  identical.

**Every verdict you post carries the commit it checked** — the tag takes
`head=`, `base=`, and `issue=` (`../_shared/evidence-gates.md`, "The verdict
comment"). Read them in the worktree you gated, at gate time:

```bash
git -C <path> rev-parse HEAD                        # head=
git -C <path> merge-base HEAD origin/<base-ref>     # base=
```

This matters most here, because a re-gate is usually happening *precisely
because* the tree moved. A verdict without its head SHA cannot be distinguished
from one a later push invalidated, so `/orca:status` treats it as `gated-stale`
and the gate you just ran counts for nothing.

**Verify the head you gated is still the head.** Re-read `headRefOid` after the
checks finish and before posting: if it changed while you were running, commits
landed mid-gate. Say so and re-run rather than posting a verdict about a tree
that is already gone.

  Under `pass-with-review`, **list the human criteria first**, in the comment and
  in the report. They are what a reviewer should look at, and burying them under
  a green verdict is how an unverified claim gets read as a verified one. Under
  `pass-agent-judged`, do the same with the judged criteria **and give the
  reasoning**, so a reviewer can disagree with the judgement rather than having
  to take it on faith.

**Never merge. Never close an issue by hand. Never mark a PR ready
unprompted.** Merging is the human's decision; closing happens through
`Closes #<n>` when they merge. A gate with merge authority is not a gate.

## Failure modes to avoid

- **Inventing criteria** for an issue that declares none. Stop instead.
- **Trusting checkboxes**, or the executor's summary, as evidence.
- **Passing a human criterion** because the surrounding work looks good.
- **Reporting `pass` with human criteria outstanding** — that is
  `pass-with-review`, or `pass-agent-judged` if one was genuinely judged.
- **Reporting `pass-agent-judged` while unsure.** Uncertainty is
  `pass-with-review`. The whole value of the label is that it means an agent
  actually formed a view.
- **Reading a previous verdict comment as input** on a re-gate. Re-derive
  everything; a verdict computed against an older tree is not evidence about this
  one.
- **Searching the whole diff** for an "appears in the diff" criterion instead of
  added lines only.
- **Accepting a pre-existing artifact** for a criterion demanding a new one.
- **Accepting stale evidence** produced before the change it validates.
- **Reporting only the first failure.**
- **Marking a PR ready, merging, or closing an issue.**
