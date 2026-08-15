# Review fix — reading PR review comments and dispatching the fix

§3.2 of `../SKILL.md`. Nothing in the `orca` plugin reads review comments; this file is where that
lives. It has three parts: **read** the review surface, **triage** it, **dispatch** a fix into the
lane and close the loop on the threads.

The fix is done by an agent in the lane's worktree, bound by a contract modelled on `/orca:launch`
§1a (rework). **The tech lead never edits code.**

## Read

Three surfaces, all with `gh`. `<o>/<r>` from `gh repo view --json nameWithOwner`; the owner login
from `gh repo view --json owner --jq .owner.login`.

**Inline review comments** — where Codex puts its findings, and where owner line comments land:

```bash
gh api repos/<o>/<r>/pulls/<n>/comments --paginate \
  --jq '.[] | {id, path, line, user: .user.login, in_reply_to_id, created_at,
              prio: (.body | capture("(?<p>P[123]) Badge")? // {p:null} | .p), body}'
```

- `in_reply_to_id == null` ⇒ a thread root; replies carry the root's id. Only roots are findings.
- Codex is `chatgpt-codex-connector[bot]`; its priority is the badge in the body —
  `![P2 Badge](https://img.shields.io/badge/P2-yellow…)`. The regex above pulls `P1`/`P2`/`P3`.
  No badge ⇒ treat as `P2`.
- **New** = `id` greater than the ledger's `last-seen` for this PR. Store the max id seen after
  each read.

**Review bodies and PR-level comments** — owner prose, and Codex's summary review:

```bash
gh pr view <n> --json reviews,comments \
  --jq '{reviews: [.reviews[] | {author: .author.login, state, body, submittedAt}],
         comments: [.comments[] | {author: .author.login, body, createdAt}]}'
```

An owner review with `state == "CHANGES_REQUESTED"`, or an owner comment that reads as a request,
is a finding even without a line. Ignore your own `<!-- orca:verify -->` comments and your own
replies.

**Thread ids for resolving** (GraphQL; REST cannot resolve threads):

```bash
gh api graphql -f query='query { repository(owner:"<o>", name:"<r>") {
  pullRequest(number:<n>) { reviewThreads(first:100) { nodes {
    id isResolved comments(first:1) { nodes { databaseId } } } } } } }' \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[]
        | {thread: .id, resolved: .isResolved, root: .comments.nodes[0].databaseId}'
```

`root` joins to the REST comment `id`.

## Triage

| Source | Priority | Action |
|---|---|---|
| Owner (the human), any form | **P1** | fix |
| Codex `P1` | P1 | fix |
| Codex `P2` | P2 | fix |
| Codex `P3` | P3 | **judge**: fix if it is a real defect or a one-line improvement inside the diff; otherwise reply *won't fix* with the reason |
| Any bot other than Codex, or CI annotations | judge as P3 | same rule |

Judging a `P3` is a tech-lead call, not a fix agent's — decide before writing the contract, and
put the *won't fix* replies in the contract's reply list so they go out with the fixes.

**Bounds.** Fix rounds are counted per PR in the ledger. Round 1 and 2 dispatch. If findings keep
arriving after round 2 — same thread reopened, or a new batch of the same shape — **stop fixing
and escalate**: put the PR under *Waiting on you* with the open threads and your read on why the
loop is not converging (reviewer and criteria disagree; the change is bigger than the issue; the
finding is wrong). A third fix round is the user's decision.

**Precondition on the lane.** Find it by `linkedIssue`:

```bash
orca worktree ps --limit 200 --json     # filter repoId + linkedIssue == n + isMainWorktree == false
```

- Lane present ⇒ `git -C <path> status --porcelain` must be empty, and the lane's agent must be idle
  (`orca terminal list --worktree id:<exact-id> --json`, then `terminal wait --for tui-idle
  --timeout-ms 60000` on its agent terminal, or no agent terminal at all). Busy or dirty ⇒ skip this
  tick, note it, try next tick.
- Lane gone (reaped) ⇒ the branch still exists on the remote. The fix agent checks out **that
  branch** in a fresh worktree — never a new branch. Use `orca worktree create --name <slug>-fix
  --no-parent --base-branch <branch> --issue <n> --json` and let the contract say the branch is
  already the PR's head. Prove isolation exactly as `/orca:launch` does
  (`git -C <path> rev-parse --git-dir --git-common-dir` must differ).

## Dispatch — the review-fix contract

Write to `~/.claude/plans/<repo-name>/<YYYY-MM-DD>-<slug>-review-fix-<k>.prompt.md`, `<k>` = the
fix round. Never overwrite an earlier one. Then start the agent in the lane and hand it the pointer:

```bash
orca terminal create --worktree id:<exact-id> --title "fix #<n> r<k>" --command "claude" --json
orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json
orca terminal send --terminal <handle> --text "Read the file <absolute contract path> and execute its instructions exactly." --enter --json
```

The template. Fill every section; the fenced pieces are copied, not paraphrased.

```markdown
# Review fixes for PR #<pr> — issue #<n>, round <k>

Address the review findings below on the existing PR. Read this entire file before starting.

## The situation

- Worktree: `<path>` — the branch `<branch>` is already checked out. **Do not create a branch.**
- PR: <url> — **push to this PR. Do not open another.**
- Issue: #<n> — <url>. Its `### Done when` checklist is what the gate will re-check in full.
- Follow the repository's CLAUDE.md / AGENTS.md. <paste the repo's non-negotiables that touch code>

## Findings to address

<one block per finding, verbatim, in priority order>

### F1 · <P1|P2|P3> · `<path>:<line>` · <author>
> <the comment body, quoted verbatim>

Reply to post when done (thread root id <id>): "<one or two sentences: what changed and where>"

### F2 · P3 · `<path>:<line>` · <author> — **won't fix, reply only**
> <body>

Reply to post: "<the reason, plainly>"

## What already passed

<the criteria the last gate marked ✓ / ⊙, verbatim — so they are not re-litigated or broken>

## How to work

1. Fix only the findings above. A review comment is not permission to reopen the diff:
   no refactors, no adjacent improvements, nothing outside the lines the findings name unless a
   fix genuinely requires it. If a finding is wrong or would violate the issue's criteria, do not
   apply it — say so in your final summary and in that thread's reply.
2. Commit in logical increments. Run the repository's test command after the last fix.
3. **Cold-reader review**, once. Spawn a fresh subagent (not a fork) with the findings, the
   `### Done when` criteria, and `git diff <base>...HEAD` for *this round's commits only*, and ask
   two questions: (1) does this diff address each finding without touching what already passed?
   (2) is anything in this round's lines likely to cause a bug or be hard to change? Judge only
   lines this round changed — the rest of the branch passed a gate and is not yours to relitigate.
   Fix real blockers; report the rest. Run it once; do not re-review after fixing.
4. **Gate**, by an agent that did not write it, against the issue's **full** `### Done when` —
   a fix can break what previously passed. <paste the gate prompt here in full, exactly as the
   lane's original contract carried it — it is under "step 7" in
   `~/.claude/plans/<repo-name>/<original-contract>.prompt.md`>. Give it only the criteria, the
   worktree path, the base branch, and the issue number. Do not tell it what you believe passes.
   `fail` ⇒ one narrow fix, one fresh gate. A second `fail` ends it: push anyway and report blocked.
5. Rebase onto the latest default branch if the PR shows conflicts, push to the existing branch,
   then post the gate verdict as a **new** PR comment: `gh pr comment <pr> --body-file <verdict>`.
   Never edit an earlier verdict comment.
6. Post the replies listed above, one per thread root:
   `gh api repos/<o>/<r>/pulls/<pr>/comments/<root-id>/replies -f body="<reply>"`.
7. **Never merge, never mark ready, never close the issue, never resolve threads** — the tech lead
   resolves them after checking the push. Never write progress into a tracked file.

## Finish with

The commits pushed, each finding → fixed / won't fix (with the reason), the gate verdict quoted,
test results, and anything you disagreed with. If the branch ended on a second `fail`, lead with that.
```

## Close the loop

Next tick, when the PR shows new commits from the fix agent and the agent is idle:

1. Confirm each reply landed (re-read the thread roots; a root with no reply from the fix agent is
   an unaddressed finding — leave it open, note it).
2. Resolve the threads that were **fixed** (not the *won't fix* ones — the reviewer should see
   those and push back if they want):

   ```bash
   gh api graphql -f query='mutation { resolveReviewThread(input:{threadId:"<thread>"}) { thread { isResolved } } }'
   ```

3. Re-trigger the reviewer so the fixed commit gets reviewed: `gh pr comment <pr> --body "@codex review"`.
   Codex reviews on open, on ready, and on that comment; a push alone may not re-run it.
4. Bump `last-seen` and the fix-round counter in the ledger. If the gate verdict comment on the PR
   says `fail`, this PR goes under *Waiting on you* — the fix round spent its rework.
