# Changelog

Notable changes to the `pod` plugin (named `orca` before 2.0.0). Versions track
`plugins/pod/.claude-plugin/plugin.json`. Entries below 2.0.0 use the old
`/orca:` invocations — they were true when written and are left as history.

## 2.1.0 — 2026-08-15

**Seats: the specialists the tech lead convenes.** The plugin now has personas —
product, requirements, architecture, test, UX & design, security, domain — and
none of them is a skill.

The question that started this was whether to add persona skills next to the
tech lead: a project manager, a QA person, an art director. The repo already had
most of them by *function* — `/pod:verify` is QA, `/pod:triage` is grooming, the
expert panel was three unnamed reviewers — and the missing ones would each have
been a second composer with its own bounds and its own ledger, colliding in
routing with `triage`, `status`, `verify` and `tech-lead`. So a persona is a
**seat**: a fresh agent the tech lead convenes for one question with one lens,
whose text the tech lead reads and then decides on itself under the decision
bar. Seats advise; the tech lead acts; the user merges. That is the hierarchy —
you → tech lead → seats / lanes / skills — and it is now written down.

### `tech-lead/references/seats.md` — new, load-bearing

The one place a persona is defined: standing rules for every seat (fresh agent,
never a fork; same inputs plus its lens and nothing else; the fenced-issue-body
rule; the "only findings that would change what happens" bar; **never edits,
comments, launches, or writes the ledger**), the roster with each seat's lens,
what it reports on, and when it is convened, and the two convening points below.
A consuming repo overrides the roster in its own `CLAUDE.md`; the file is never
edited for one repo.

Three seats are new:

- **Product** — convened **once, at slate time**, before the proposal prints.
  Order, dependency edges inside the scope, milestone coherence, issues that are
  one pretending to be several or the reverse, skips it would not skip. It may
  reorder *within* the scope the user named and never widen it; merge/split
  suggestions go under *Waiting on you*, because they restructure the backlog.
  Not re-convened on `resume` — an approved or edited slate is the user's.
- **UX & design** — a plan-panel domain seat when the repo names it or the issue
  is user-facing: flows, states, copy, accessibility, and visual direction where
  the repo says it cares.
- **Security** — a plan-panel domain seat when the issue touches auth, payments,
  permissions, migrations, or anything run under a credential.

**Bounds, which are design, not tuning:** one product-seat round on the slate;
three core seats always, never fewer, including `scope:s`; **five seats per plan
round at most** (three core + two domain) — more cold readers produce
overlapping findings that read as convergence, which is exactly what the
decision bar must not mistake for independence.

**Deliberately not a seat:** a PR-time UX / "art director" review of what a
lane produced. Its findings would be review comments authored by the tech lead's
own agent and then dispatched by the tech lead — a self-loop outside the trust
model in `review-fix.md`, where only the owner and an adopted reviewer generate
dispatched work. A repo wanting design review of output adopts a reviewer for
it, and the comments come in through the same door as everyone else's.

### `expert-panel.md`

The roster table and "choosing the fourth seat" moved to `seats.md`; the panel
file keeps inputs, the reviewer prompt, rounds, and the decision bar, and says
which seats a plan round convenes and the five-seat cap.

### `tech-lead/SKILL.md`

§2 convenes the product seat on the draft slate and prints one `Product seat:`
line in the proposal; §3.3 convenes the plan panel per `seats.md`; *not for*
gains "a persona you can invoke directly"; two failure modes added — *convening
a seat to act* and *adding a persona as a skill*. The description names the seats
as advisors, never actors; no trigger phrase changed, so the `/pod:status`
boundary is where it was. The ledger header records `Slate reviewed <time>`.

### Docs

README and the guide gain a *Who it calls in* block with the hierarchy under
`/pod:tech-lead`, and *not a cast of persona skills* under what this is not.
CLAUDE.md records the seats-not-skills rule so it is not re-litigated.

## 2.0.0 — 2026-08-15

**The plugin is now `pod`, and its skills are `/pod:<skill>`.**

A pod is what a group of orcas is called. The old name, `orca`, said two false
things at once: that these skills were made by the Orca team, and — because
`/orca:*` sat right next to Orca's own bundled `orca-cli` and `orchestration`
skills — that "use orca to hand this off" had one obvious meaning. It did not.
Every SKILL.md carried a paragraph fighting that routing collision per case;
the name was the root cause. `pod` keeps the ocean, drops the claim, and reads
as what it is: a team of agents on top of Orca, not Orca.

This is a **name change only.** No skill's behaviour, flags, or trigger phrases
changed except the namespace prefix. Nothing was rewritten to be smarter under
cover of the rename.

### What changed

- `plugins/orca/` → `plugins/pod/`; `plugin.json` name `orca` → `pod`.
- Marketplace `orca-skills` → `pod-skills`; installs are `pod@pod-skills`.
- Every `/orca:<skill>` invocation in skills, `_shared/`, `references/`, README,
  the guide, CLAUDE.md, CONTRIBUTING.md, TRACKING.md, and this repo's own
  `/ship` and `/audit-orca` skills → `/pod:<skill>`.
- The "collides with Orca's bundled skills" prose in CLAUDE.md and
  CONTRIBUTING.md now says what is still true after the rename: the *subject*
  overlaps, so every skill still names the bundled skill that owns what it
  declines. The namespace no longer collides.
- README and the guide state up front that the plugin is not Orca's, and gain
  an *Upgrading from `orca@orca-skills`* section.

### What deliberately did not change

- **Every reference to the Orca app and CLI.** `orca status`, `orca terminal …`,
  `orca-cli`, `orchestration`, `_shared/orca-lanes.md`, `$ORCA_CLI_COMMAND`,
  `orca-dev` / `orca-ide`, and this repo's `/audit-orca` — those name Orca, which
  did not move.
- **The verdict tag on the wire, `<!-- orca:verify head=… -->`.** It is a
  durable record identifier already sitting in consuming repos' PR comments;
  renaming it would orphan every existing verdict and force every consumer to
  grep an alternation forever. `_shared/evidence-gates.md` now says so beside its
  definition: it names the record format, not the plugin, and never follows a
  rename.
- **The `AGENTS.md` block and its `<!-- orca-skills tracking model v2 -->`
  marker.** The block written into consuming repos names no skills, so nothing
  in it changes and there is no schema bump — `/pod:migrate`'s version table is
  untouched. The marker prefix stays for the same reason as the tag.
- Changelog history below this entry.

### Migrating

There is no in-place upgrade across a name change:

```bash
claude plugin uninstall orca@orca-skills
claude plugin marketplace remove orca-skills
claude plugin marketplace add tatejennings/pod-skills
claude plugin install pod@pod-skills
```

Consuming repos need nothing. Prose in a repo's own `CLAUDE.md` that spells out
`/orca:<skill>` needs a hand edit; that is the only trace.

The GitHub repository and local checkout are renamed `pod-skills` separately;
the old GitHub URL redirects.

## 1.20.0 — 2026-08-15

**Schema v2: `### Done when` is now `### Acceptance criteria`.**

"Done when" was a personal convention. *Acceptance criteria* is what the rest of
the industry calls this, and a repo's issue template should not need a glossary.
The section is unchanged in every other respect — same items, same three forms,
same meaning, same gate.

### Nothing breaks, by design

**Every skill reads both headings** and treats them as the same section. A repo
written before this release keeps working untouched, whether or not it ever
re-runs `/orca:migrate`.

That tolerance is a safety property, not politeness. A heading a skill cannot
find does not raise an error — **it reads as *no criteria at all***, which is the
one state that disables the gate and makes `/orca:launch` refuse the issue. A
rename must never be able to produce that silently, so `issue-schema.md` gains a
*Finding the checklist* section stating the rule once, and every consumer points
at it rather than implementing strictness of its own.

An issue carrying **both** headings is a conflict, not a choice: report it and
gate nothing. Two checklists means nobody knows which one binds.

### `/orca:migrate` gains the v1 → v2 step

The schema-version machinery existed for exactly this and had never been used.
The upgrade finds issues still on the old heading and rewrites **only that
heading line**, leaving the body otherwise byte-identical — because an acceptance
criterion is an executable contract, and a migration that edits one is changing
what a branch will be gated against. It matches the heading anchored to its own
line at any depth, skips closed issues unless asked, refuses issues carrying both
headings, and reports counts of what it rewrote and what it skipped.

The drift audit learned the difference too: an issue on the old heading is **not**
a defect and is never reported as missing criteria — it is offered the rename.

### Everywhere else

The rename reached the executor contract's `## Acceptance criteria` section, the
self-gate prompt, the `AGENTS.md` fragment written into consuming repos (now
stamped `tracking model v2`), all eight skill descriptions, the README, and the
guide. Ordinary English uses of "done when" — *"you are done when `/orca:status`
shows…"* — were left alone; only the heading and prose naming it changed.

## 1.19.0 — 2026-08-15

**A verdict now says which commit it checked, and who wrote it.** From an
external top-down review of 1.18.0, which asked a sharper question than the
previous round: not *can the loop misbehave* but **are the artifacts the loop
trusts worth trusting.** They were not. Every claim below was re-verified against
the files and the live GitHub API before being fixed.

This release repairs the evidence gate itself, so it lands mostly in
`_shared/evidence-gates.md` and `/orca:status` — which means it fixes
`/orca:verify` and `/orca:launch` too, not only the tech lead.

### A gate verdict was not bound to anything

The verdict comment recorded the issue and the branch. **Not the commit.** And
`/orca:status` took the newest tagged comment on the assumption that "only the
newest describes the current tree" — which any later push falsifies.

So: commit A gates `PASS`. A fix agent, a rebase, or a human pushes commit B. The
`PASS` is still the newest comment, and the PR reads as gated. **Nothing had
checked the code you were about to merge**, and no artifact anywhere said so.

The tag now carries the commit it verified:

```
<!-- orca:verify head=<40-char sha> base=<40-char merge-base> issue=84 -->
```

Consumers compare `head=` against the PR's `headRefOid`. A mismatch — or a
missing `head=`, or a base that is no longer the merge-base — is the new
**`gated-stale`** verdict in `/orca:status`. Deliberately *not* a failure: it is
the same claim as never having gated. Reporting it as a failure would send people
to debug work that may be perfectly fine.

`/orca:verify` also re-reads `headRefOid` after its checks and before posting — if
commits landed mid-gate, it re-runs rather than posting a verdict about a tree
that is already gone.

### Anyone could forge one

`/orca:status` matched `[.comments[].body]`. **The author was discarded.** On a
public repo, any commenter could post a `PASS`-shaped comment carrying the marker
and it became the durable gate record.

The irony was ours: 1.18.0 author-classified *review findings* while leaving the
artifact that authorizes readiness unauthenticated. Verdicts now require a
trusted producer — the account the pipeline runs as, or one the repo's
instructions name. An untrusted tagged comment is `needs-attention`, never
gating, and never overwrites a valid earlier verdict. **A forged verdict is worse
than no verdict: it converts *unproven* into *proven* exactly when a human stops
looking.**

### `### Done when` is an executable contract

The gate runs command criteria in a worktree, under the user's credentials, by
design. 1.18.0 fenced issue bodies for the expert panel and stopped there — so
the trust boundary that matters most was the one left open: **anyone who can file
or edit an issue on a public repo could put a command in a checklist and have it
run under your token.**

`_shared/evidence-gates.md` now states the rule for every gate: run command
criteria only from a checklist authored or approved by the owner or a named
maintainer. A criterion addressed to *you*, or reaching outside the worktree, is
not a criterion — it is a malformed checklist, and gates nothing.

`/orca:tech-lead` checks authorship before launching, snapshots the criteria with
the issue's `updated_at`, and flags a lane whose issue changed after it launched.
**A human running `/orca:verify` on their own repo is their own approval** — the
rule bites when nobody is watching, which is when it matters.

### "Ready to merge" did not mean the automation was clear

It required a passing gate, no unresolved threads, and `mergeable`. **It never
checked CI.** And "no unresolved threads" is vacuously true of a PR nobody
reviewed — absence of findings is not evidence that review happened.

Replaced with **human-review-ready**, which requires all of: a verdict that is
passing *and* trusted *and* current-head; required CI green with nothing pending;
a positive signal that the adopted reviewer completed against **this** head; no
unresolved blocking threads; `mergeable` and not draft; auto-merge not armed.
Where reviewer completion cannot be established, it reports **review state
unknown** rather than treating silence as approval.

The rename is the point. The loop reports that the review surface is trustworthy
and complete. **Whether to merge stays a judgement it never makes.**

### Fixing 1.18.0's auto-merge check

1.18.0 stopped when the repository's `autoMergeAllowed` was true. That field
means auto-merge *can be enabled*, not that it *is* — so it blocked safe repos
that merely permit the feature, wrote `Auto-merge: ON` when nothing was armed,
and trained an override for the wrong condition while never checking the
dangerous one.

Per-PR `autoMergeRequest` is the real signal, re-checked every tick because a
human can arm it at any moment. A PR with it set is excluded and surfaced;
`autoMergeAllowed` is informational only. (Reasoning from a field name instead of
reading the schema — the exact failure this repo's verify-against-live rule
exists to prevent, applied to an API that looked too obvious to check.)

### The ledger is memory, never evidence

Stated explicitly, because this release added ledger fields that could be
misread as cached truth. The ledger holds what only the loop knows: grants,
steering, counters, decisions, notification history. Everything about the world —
PR state, CI, verdicts and their freshness, head SHAs, threads, auto-merge — is
re-derived every tick. **When a row and the world disagree, the world wins and
the row was stale.** A remembered `PASS` defeats every freshness rule above.

### Criteria-less launch, narrowed rather than removed

The review wanted `/orca:launch` to refuse criteria-less work outright. It keeps
the hatch: a *present* user who declines planning and accepts an ungated branch
has made a real choice. **`/orca:tech-lead` may not take that path** — under an
autonomy grant nobody sees the offer, so the choice cannot be made, and inventing
criteria to unblock a launch means gating against your own invention.

### Deferred, and why

Two items from the review are deliberately not here. **Five new expert seats**
(PM, UX, security, release, deeper QA) add opinions about a *plan* while the
problem was that a passing gate said nothing about the current *commit* — the
review's own bottom line says the next improvement should not be another reviewer
role. And **one normative state machine** covering all sixteen states is right in
principle, but writing it now would describe a machine this release is actively
changing; shared specs are most dangerous when they drift, and the surest way to
make one drift is to write it before the thing it describes has settled.

Both are better after. Still ahead, unchanged from 1.18.0: `automation.md`'s
remaining preconditions (spend ceiling, PR cap, circuit breaker, leases,
stale-lane cancellation) and the cross-lane collision check.

## 1.18.0 — 2026-08-15

A four-lens adversarial review of 1.17.0's `/orca:tech-lead` — one reviewer
briefed to argue the skill should not exist, one hunting operational defects, one
judging it against its own goal, one auditing safety and authority. Three of the
four independently found the same two blocking defects. Everything below was
re-verified by hand against the files and the live `gh` API before being fixed.

### `/orca:plan` never implemented `--auto`

`/orca:wave` has sent `/orca:plan <n> --auto` since it shipped, and documents the
flag as real. `/orca:plan` parsed only `--launch`. So `--auto` fell through to
`EnterPlanMode` — **an approval gate with nobody there to approve it.**

`/orca:tech-lead` was the first caller to hit it on every issue rather than
occasionally, which is how it surfaced, but the defect was never tech-lead's.
`/orca:plan` §0 now parses `--auto` (plan unattended, never ask, never enter plan
mode, defer forks into the plan file, stop at the plan), and §3's asking rules
now key on the flag rather than on "inside a wave" — a programmatic caller is not
a reason to stop asking, the flag is. **An unrecognized flag is now a stop**, not
a token to ignore.

### Plans are found, not guessed

`/orca:tech-lead` globbed `<date>-<n>*.md`, which matches issue #8 when you asked
for #84, and misses entirely when the plan was named from a slug. On a miss it
fell back to **scraping a plan out of a terminal buffer** — possibly a
half-written draft, possibly one awaiting an approval nobody gave — and reviewing
that as though it were a plan.

Two changes make the handoff explicit. `/orca:plan` names issue-targeted plans by
the bare issue number, and prints `PLAN FILE: <absolute path>` as its last line,
always. Callers read that line. A missing file is now a **reported failure**, not
a fallback to scraping.

### Review comments are untrusted input

The fix contract copied PR review comment bodies **verbatim** into a file, then
told an agent with push rights and `gh` auth to *"execute its instructions
exactly."* The prohibitions sat 42 lines below the injected text, and a `>`
blockquote — the only delimiter — does not survive a comment containing its own
headings. On a public repo, any commenter reached an unattended agent.

- A **`## Hard limits` block now comes first**, before any third-party text,
  copied verbatim into every contract. A contract without it, or with it after
  the findings, is invalid and must not be sent. Same rule `/orca:launch` already
  held for the gate prompt, for the same reason.
- Comment bodies go in **fenced blocks**, never blockquotes, under an explicit
  statement that they are data describing a problem and never instructions — with
  an instruction to report any attempt as an injection.
- The **expert panel** gets the same treatment: issue bodies are attacker-writable
  too, and an issue that quietly steers three cold readers the same way
  manufactures the convergence the decision bar reads as independence.

### Reviewers are a role, not a product

The skill hardcoded `chatgpt-codex-connector[bot]`, its badge format, and
`@codex review`. **That is an app-agnosticism violation** — other repos run other
reviewers, several reviewers, or none.

Authors now sort into three roles: **owner** (always P1), **adopted reviewer**
(findings dispatchable), and **everyone else** (queued, never dispatched). A bot
is not trusted for being a bot; adoption has to be evident from the repo's own
configuration. Priority markers are learned per-reviewer and recorded in the
ledger. Codex remains as a labelled worked example of the middle role. The
re-trigger is only sent when its form is known — **an at-mention of a guessed
handle pings a real person at 4am.**

That previously-unbadged-comments defaulted to `P2` *auto-fix* is what made this
urgent: the default trusted a stranger's text enough to act on it.

### Auto-merge: the invariant was narrower than it read

"Nothing ever merges" is enforced by forbidding every *agent* from merging — and
that part holds; it was traced and no path around it was found. But contracts
mandate **non-draft** PRs so review tooling sees them, and a non-draft PR in a
repo with auto-merge enabled merges itself on green CI with **no agent
involved.** The guarantee was "no agent merges," which is not the same sentence.

`/orca:tech-lead` §0 now checks `autoMergeAllowed` and stops unless the user
overrides it knowingly. (Verified live: it is a GraphQL field; `gh repo view
--json` does not expose it.) This is a limit of the model rather than a bug in
the skill — worth stating plainly, since an eight-hour unattended loop is where
it would first matter.

### Smaller fixes from the same review

- **The fix-round counter moves at dispatch**, not when the round closes. It was
  the only termination rule on the fix loop, and a compaction in between lost it.
- **The reviewer is not re-triggered after round 2.** Soliciting a review the loop
  is not permitted to act on hands the user a fresh unaddressed round.
- **Round 2 of the panel is a cold read again.** Reviewers were being handed the
  `## Panel` section recording what was dismissed and why — a rebuttal written by
  the party under review, which anchors against re-raising it. The section stays
  in the file for the executor and the user; it is withheld from the panel.
- **A split has a path.** A panel round recommending one is not a fork the
  decision bar can take (it restructures the backlog), and `/orca:launch` would
  refuse it — so the issue used to vanish silently from the tick. It now goes to
  *Waiting on you* naming `/orca:plan` §5a.
- **Planning terminals are closed on every path**, and swept at the top of each
  tick. They live in the *active* worktree, where `/orca:status` cannot see them
  (it filters `isMainWorktree == false`), so leaks were invisible to the loop's
  own dashboard. Handles are re-resolved rather than cached across the block.
- **The ledger row is written before the planning terminal starts**, mirroring the
  rule already held for the mode.
- **Verdict casing is documented as part of the contract** in
  `_shared/evidence-gates.md`: UPPERCASE is the literal string on the wire that
  `/orca:status` and `/orca:tech-lead` grep for; lowercase is only the verdict's
  name in prose. Tidying one into the other breaks the match silently, and a
  broken match reports a gated PR as ungated.

### Still open, and deliberately so

The review's strongest structural finding stands: `_shared/automation.md` records
an adversarial review concluding **unattended issue → PR is not responsible to
ship**, and lists eight preconditions. `/orca:tech-lead` currently meets three —
no spend ceiling, no PR cap, no circuit breaker across issues, no leases on
shared files, no stale-lane cancellation — and does not reference that file. It
also lacks the cross-lane collision check `/orca:wave --review` exists to
provide, so the composed skill is weaker there than the skills it composes.

Those are the next change, not this one. This release makes the skill *work* and
makes it *safe to point at a repo*; it does not yet earn its way past the bar the
plugin set for itself.

## 1.17.0 — 2026-08-15

### `/orca:tech-lead` — the seat the pipeline leaves empty

Every skill in this plugin stops on purpose. `/orca:plan` stops at a plan,
`/orca:launch` stops at a running lane and explicitly says *do not monitor it*,
`/orca:status` only reads. That is deliberate — but it means the human is the
thing connecting them, and the connecting work is not the interesting part:
noticing a lane finished, reading the Codex comments on its PR, deciding which
issue goes next, resolving a fork planning surfaced.

This skill takes all of that **except the merge**. It composes the existing
skills rather than reimplementing them — it invokes `/orca:status` for the lane
× backlog join, `/orca:plan` for planning, `/orca:launch` for lanes — and never
edits code itself. What it adds on top is the part none of them own: a panel of
independent expert reviewers over each plan, PR review-comment triage and fix
dispatch, and a decision bar for forks.

**Ask it and it proposes; tell it and it goes.** A question prints a slate and
waits. An imperative prints the same slate — so the choice is always visible and
steerable — then starts.

**Every loop in it is bounded**, which is the same lesson as 1.13.1 and 1.16.0:
three plan-review rounds, two fix rounds per PR, one rework per gate, two
owner-only ticks before it idles out, and an eight-hour hard cap on any autonomy
grant. When a bound is hit it escalates rather than trying once more.

**It never merges a PR and never closes an issue.** That is the one decision the
whole pipeline exists to keep human, and no wording from the user unlocks it.

State lives in a ledger outside the repo (`~/.claude/plans/<repo>/tech-lead-<scope>.md`)
so a compaction or restart resumes rather than re-plans.

The skill was developed as a personal global skill and moved here because it is
useless without this plugin — its own preconditions stop if `/orca:*` is not
invocable. Moving it made three changes necessary:

- **Its two `TODO(user)` blocks are gone.** A shipped skill cannot ask the
  installer to edit files inside a plugin directory that the next update
  overwrites. The conservative fallbacks became the stated defaults, and a
  consuming repo now overrides them the way every other skill here takes repo
  conventions — by saying so in its own `CLAUDE.md`.
- **It no longer names a specific skill or file.** The expert panel's Domain
  seat described an iOS/SwiftUI reviewer by name and assumed a decisions file
  exists; both are now described by how they are *chosen*, per the
  app-agnostic rule.
- **Its description de-collides with `/orca:status`.** Both wanted "what should
  I work on next". `/orca:status` keeps the read-only reading; this skill claims
  it only when the user wants it acted on.

### Re-verified against `orca` 1.4.182

Every command and flag the skills reference was re-checked against live `--help`
after the CLI upgrade from 1.4.162. **No breaks** — all 26 commands still exist,
and the load-bearing facts hold: `worktree create` still has no branch-name
flag, `worktree ps` still returns `worktreeId` where `worktree list` returns
`id`, and `project setup-update --kind git` still fixes the `kind: folder` trap.

Three notes added from new surface:

- **`--setup run` over `--run-hooks`** on `worktree create`: `--run-hooks` is
  documented as a legacy alias that *also reveals the worktree*, so it does two
  things where one was wanted. (On `worktree rm`, `--run-hooks` remains the real
  flag — there is no `--setup` there.) `orca-lanes.md` now says why the handoff
  invocation omits both it and `--activate`.
- **`--reuse-session` is not for the automation**, and `automation.md` now says
  so. It applies only to `--workspace-mode existing`; adopting it would mean
  each scheduled run inheriting the previous run's context, which is exactly the
  independence an unattended launcher needs.
- **Linear is out of scope, explicitly.** Orca now ships a full `orca linear`
  surface and `worktree create --linear-issue`. These skills read a `### Done
  when` checklist out of a GitHub issue body and nothing else; `orca-lanes.md`
  now warns against adding a `--linear-issue` fallback, because a lane whose
  criteria live where the gate cannot read them silently loses the gate.

## 1.16.0 — 2026-08-06

**The gate never ran.** Reported from real use, and it is the most consequential
gap found so far because nothing about it looks broken:

> "I find myself never running the verify command. I just assumed with how
> detailed the plan is and the implementation and the code review that it's done
> correctly… I always just merge the PR and delete the workspace. I don't have
> time to verify."

`/orca:verify` was not defective. It was **positional**. The pipeline has three
gates, and two of them are on the path the user already walks — approving a plan,
merging a PR. The third asked them to stop, open a different session, and type a
command at the exact moment the work already felt finished. So it never happened,
and every `### Done when` checklist this plugin exists to write ended in nothing.

### Lanes now gate themselves

The gate moved onto the path instead of waiting beside it. `/orca:launch`'s
executor contract gains **step 7**: before opening a PR, the executor spawns a
**fresh agent that did not write the code** and has it run the evidence gate
against the branch.

That independence is the whole design, not a detail. `_shared/evidence-gates.md`
has always said evidence comes from the branch and the commands, *never from the
executor's report of them* — so "have the executor check its own work" would have
been the failure this gate exists to catch, wearing a gate's uniform. The
executor spawns the gate; it does not perform it, and it does not overrule it.

**On `FAIL`, the lane reworks itself once** (step 7a), fixing only the failed
criteria with the gate's own evidence — no refactors, no adjacent improvements.
Then it re-gates once. **A second `FAIL` ends it**: the PR opens anyway carrying
the failing verdict, and the executor reports the branch blocked. That bound is
deliberate and is the same lesson as 1.13.1 — a reviewer loop with no termination
rule always finds one more thing.

The PR now arrives **already gated**, with the verdict as a comment, so the
evidence is in front of the user at the moment they decide to merge.

### A fourth verdict, and why it is a trade-off

Prose criteria may now be **judged by that independent agent** rather than always
deferred to a human. This is a real relaxation of a rule stated in four places,
so it is worth being explicit about the reasoning: a gate that returns
`pass-with-review` on every branch stops being read, and a verdict nobody opens
is the same as no gate — the original failure, arriving by a slower route.

What keeps it honest is the label. The verdicts are now four:

| Verdict | Means |
|---|---|
| `pass` | proven by machine |
| `pass-agent-judged` | an independent agent read the diff and thinks it holds — **opinion, not evidence** |
| `pass-with-review` | nobody has checked this yet |
| `fail` | a criterion failed, or an agent judged one unmet |

**The asymmetry is the safety property.** A judging agent's *"met"* is an opinion
and can never produce a plain `pass`; its *"not met"* is actionable and blocks;
**unsure is `pass-with-review`, never `pass-agent-judged`.** It can only ever make
the gate stricter. Collapsing those three passing verdicts into one is the single
change to `evidence-gates.md` that would break it.

### Everything downstream learned the new vocabulary

- **`/orca:status`** gains `gate-failed` — a PR whose own gate rejected it twice
  and needs the user. It outranks every other open-PR state. `awaiting-gate` now
  means *the self-gate did not run*, which is an anomaly rather than a routine
  next step, and the table's gate column shows the verdict rather than a
  checkmark, because "gated" alone erases the distinction that matters at merge
  time.
- **`/orca:verify`** stays, reframed as the **re-gate**: for when the base moved,
  new commits landed, a verdict looks wrong, or a PR shows up ungated. It must
  never read a previous verdict as input — a verdict computed against an older
  tree is not evidence about this one.
- **The verdict comment format is now specified once**, in
  `_shared/evidence-gates.md`, because three producers must emit a string a
  fourth consumer greps for. A verdict the gate emits but `/orca:status` cannot
  match reports a gated PR as ungated — indistinguishable from never gating it.
- **`_shared/automation.md`** notes that a self-gate does not weaken any
  precondition for unattended runs. A pipeline whose only gate is one it spawns
  for itself is still a closed loop.

### `launch/SKILL.md` split into references

It hit 613 lines. The contract template moved to
`references/contract-template.md` and the gate procedure to
`references/self-gate.md`, bringing the skill back to 427.

`self-gate.md` carries a constraint worth knowing if you edit it: **its prompt
must stay self-contained.** It is pasted into a contract and read by an agent in
another worktree that cannot see this plugin, so every rule is written out inline
and nothing points at a path only this repo resolves. A shared-spec change has to
be carried into that prompt by hand.

### If you have lanes in flight

Per 1.13.2: **a contract is a file written at launch time.** Existing
`.prompt.md` files under `~/.claude/plans/<repo>/` do not have step 7 and will
keep opening ungated PRs. Either let those lanes finish and gate them by hand
with `/orca:verify <n>`, or edit the contracts directly.

### Before trusting this

`automation.md`'s first precondition still applies and now applies here: **a gate
that has only ever returned `pass` is untested.** Give a lane an issue whose
criteria the work cannot meet, and confirm it reworks once, fails again, opens
the PR anyway, posts `FAIL`, and stops. A lane that loops, or opens a green PR,
is the finding.

## 1.15.0 — 2026-08-04

**Two lanes could share one worktree, and merging one destroyed the other.**
Reported from real use, and it is the most damaging bug found so far because the
user does nothing wrong to trigger it: a PR is finished, they merge it, the
worktree is freed — and the other work living in that same checkout loses the
ground under it.

### The invariant, now stated

**One lane is one issue, one worktree, one branch, one PR.** Every skill depends
on it and all of them break together when it does not hold:

- `/orca:status` maps a lane to its work through `linkedIssue`, a single integer
- `/orca:verify` gates a branch against **one** issue's criteria
- `Closes #<n>` is the only completion record, and merging frees the worktree
- `--reap` deletes a worktree once its PR merges

`_shared/orca-lanes.md` now carries this as a named invariant with the failure
spelled out.

### Where it came from

`/orca:plan` said a split produces *"ordered sub-plans, each independently
handoff-able"* — one line, and it never said each part needs **its own issue**.
The natural reading is "three plans, one lane", which is exactly what happened.

Now (§5a): a split is **not done until each part is its own issue**, with its own
`### Done when`, real `--add-blocked-by` edges recording the order, and an
explicit decision about what happens to the original issue — one left carrying
the *whole* criteria set will fail its gate forever, since no single part
satisfies it.

**`/orca:launch` refuses to launch part of an issue.** A contract saying "part 1
of 3", or one whose PR would say `Refs #<n>` rather than `Closes #<n>`, stops
with what is needed instead.

**`/orca:status` reports the broken state** — two lanes on one worktree path, two
open PRs from one branch, or an open PR whose body says `Refs` — under
`needs-attention`, because that is the state that turns a routine merge into lost
work.

### And the splitting bar goes up again

The deeper fix: this only bites when work is split that did not need splitting.
1.14.0 raised the bar; this raises it further now that each part costs a whole
issue and lane.

- **Repetitive same-shape edits: "hundreds, not dozens"**, and **try to script it
  first** — a mechanical transformation applied uniformly is one step, not a
  hundred. (Was `>~40`, which is what justified splitting a 112-edit task into
  three lanes.)
- **Volume is explicitly not a reason to split.** Step, file, and line counts are
  weak signals usable only to support a split already justified — never to cause
  one. *"Thirty files implementing one decision is easier than five files
  implementing four."*
- **More than one architectural decision is named as the strongest reason**, and
  often the only real one.
- The reviewer is told a split is *"the strongest claim you can make, and usually
  the wrong one"*, that parts cannot share a lane, and that **size alone is never
  sufficient** — agents handle large coherent efforts well.

**If parts genuinely cannot be separated** — shared uncommitted state, or part B
unverifiable without part A in the same tree — **that is not a split.** It is one
lane doing one larger piece of work, and "three parts in one worktree" is not an
available shape.

## 1.14.0 — 2026-08-04

**`/orca:plan` split far too eagerly.** Reported from real use, and the rule was
wrong in three compounding ways.

**1. "One limit badly broken, or any two at once ⇒ split" was the main culprit.**
Seven soft limits, and a moderately-sized feature trips two almost by
construction — 12 files *and* 1,200 lines is one normal feature, not two contexts
of work.

**2. The numbers were inherited, not measured.** `~15 files` and `~1,500 lines`
came from an older suite predating current context windows, and were never
re-derived.

**3. The reviewer had no reason to say no.** Asked to *attack* a plan on four
axes, "split it" always sounds like the careful answer — and nothing told the
reviewer that a wrong split has a cost.

### The rule now

**Default to one lane; splitting is the exception and must be argued for.** A
split costs a lane, a PR, and a review each time, forces sequencing, and makes
every later lane re-read context the earlier one already had. A plan that is
merely *large* is still one plan.

Split only on a **named structural reason**, not a count:

- repetitive same-shape edits beyond **~40** by hand (was ~25)
- **more than one** new subsystem or major architectural decision
- an open-ended tuning or measurement loop, where the cycle count is unknowable
- a persisted-format migration alongside feature work
- a hard sequencing dependency — step 7 unverifiable until step 4 has merged

Steps, files, and line counts are **demoted to signals**: usable to support a
split already justified, never to trigger one. *"Twenty files implementing one
decision is easier than five files implementing four."*

**A recommended split must now state its cost** — how many lanes, what merges
before what — and confirm each part is independently **verifiable**, not merely
smaller. A part nobody can gate on its own has made things worse. **Failure to
name a clean seam is evidence it is one lane.**

### The reviewer is told the bar

> Report only findings that would change what the executor does. A plan you would
> let run as-is is a valid outcome and the common one. **"Split it" is a strong
> claim** — it is wrong far more often than it is right.

An adversarial reviewer with no stated bar manufactures concerns to justify
itself; this is the same lesson as 1.13.1's fix to the executor's code reviewer.

## 1.13.2 — 2026-08-02

**Agents were still opening draft PRs after 1.10.0, and the skill was not the
bug.** An executor contract is a **file written at launch time** — the skill
change reached future launches, but every lane already running was still reading
a `.prompt.md` that said "open a **draft** PR".

That is correct behavior in the general case: a running executor should not have
its instructions change underneath it. But it means **a behavioral change here
applies only to future launches**, and anything in flight has to be updated on
disk or it keeps following the old rule.

`/orca:launch` now says this explicitly, so the next such change is reported with
its migration rather than looking like it took effect everywhere.

*(Repaired in passing: eight contracts under `~/.claude/plans/` were rewritten to
the current rule, and two draft PRs marked ready.)*

## 1.13.1 — 2026-08-01

**Raised the bar on the cold-reader review, at both ends.** A reviewer that
reports twenty small findings produces a rewrite loop, which costs more than the
defects it prevents.

- **The reviewer is told to report only what it would block a PR over**, and that
  **"no blockers" is the expected answer on most diffs.** A long list of small
  findings is worse than a short list of real ones, because it buries the real
  ones.
- **The executor's default is to leave working code alone.** Naming, formatting,
  and preferences between two reasonable structures are notes, never fixes.
- **The reviewer runs once.** No re-review after fixing — a fresh read of a
  changed diff will always find something new, and that loop has no natural end.
  A fix large enough to genuinely doubt is a reason to stop and report, not to
  start another round.

## 1.13.0 — 2026-08-01

**The cold-reader review gained a second question: durability.** Alongside scope,
it now asks whether the diff will be hard to change later or is likely to cause a
bug — duplicated logic that will drift, a function doing several unrelated jobs, a
hard-coded dependency where the surrounding code injects, a change that forces
edits in several places whenever one thing changes, swallowed errors, unhandled
boundaries the diff introduces.

**Judged against the conventions the codebase already uses, not a style guide.**
A principle applied against a codebase's grain produces churn, not quality.

### The bar on what gets fixed is the real design

Without one, a reviewer's opinion becomes a mandate to rewrite — which is scope
creep wearing a nicer hat, and precisely what question 1 exists to catch. So:

- **Fix** real defects and genuine blockers: a bug, a swallowed error, an
  unhandled boundary, logic duplicated in a way that will silently drift.
- **Fix** a structural problem *your own diff introduced*, where the fix is local
  and obvious — extracting a second responsibility you just created, injecting a
  dependency you just hard-coded.
- **Report, never fix**, anything that would refactor code you did not write or
  trade working code for a principle. It goes in the PR body or a follow-up
  issue.

Severity is judged by consequence, not by rule: *would this cause a bug, or make
the next change to this area meaningfully harder?* If neither, it is a note.

### On the overlap with PR review tooling

This does duplicate what a PR reviewer covers, and that is deliberate:
**pre-push is cheaper than post-push.** Fixing a defect before the PR exists
beats a review comment, a rework cycle, and a force-push — and "this will be hard
to change later" is exactly the finding that rarely survives a review round-trip,
because nobody wants to relitigate structure on a PR that otherwise works.

**On a rework, the durability question applies only to lines that rework
changed.** Pre-existing structure is out of bounds — it passed the gate once and
is not that run's to relitigate. The executor is reading a whole branch it did
not write, so this bound matters more there than on a fresh build.

## 1.12.0 — 2026-08-01

**The executor now runs a cold-reader scope check before pushing.** One fresh
subagent — not a fork — gets the `### Done when` criteria, the contract's Steps,
and the branch diff, and answers one question:

> Does this diff implement what was asked — no more, no less? Name anything in
> the diff that no criterion or step called for, and anything called for that the
> diff does not do.

**This is the one check the executor cannot do itself.** Its own review shares
every assumption that produced the code, so it catches typos and regressions but
not *"I built something coherent that is not what was asked"* — the author is the
last person who would notice that. A cold reader comparing the diff against the
criteria catches exactly that class.

Deliberately **one reviewer on one axis**, not a panel. Several agents reading
the same diff with the same question is redundancy without diversity — they share
blind spots and mostly re-find each other's findings. Scope is the axis chosen
because the other two are already covered: the self-review handles bugs and
regressions, and code quality is reviewed on the PR by whatever tooling the repo
runs (which is why PRs now open ready rather than draft, in 1.10.0).

Findings are acted on rather than reported: missing work gets done, scope creep
gets removed or called out in the PR body as deliberate. An unresolvable
off-plan finding **stops the run** instead of producing a PR the executor would
have to defend.

**The rework contract carries it too**, with the question narrowed — *does this
diff address the failed criteria without touching what already passed?* Scope
creep is a bigger risk on a rework than a fresh build: the executor is reading a
whole branch it did not write, and the temptation to improve things nobody asked
about is real.

## 1.11.0 — 2026-08-01

**`/orca:wave --auto`** — each planning context runs unattended and stops only if
a genuine fork comes up.

The default wave has one speed: every context waits for you, including the ones
with nothing to ask. A small bug with an obvious fix does not need a
conversation, and making you visit its tab anyway is pure cost.

**Nothing pre-filters which issues are eligible — the plan decides.** An issue
with an obvious fix plans clean; one with a real trade-off stops and asks,
regardless of size or labels. The mechanism already existed: the wave sends
`/orca:plan <n> --auto`, which proceeds alone only when the codebase's
conventions, the requirements, and standard practice all agree *and* being wrong
would be cheap to reverse. Otherwise it defers and names the question.

```
4 planned · 3 clean, 1 needs you

  #84  planned clean
  #85  planned clean
  #87  planned clean
  #86  QUESTION — which overlay owns the marker tray after G1?
       tab: #86 overlay fixes
```

**`--auto` never launches.** Clean plans finish and wait; the cross-plan
collision check still gates every lane. That check is the only thing that can
catch two independently-ready issues editing the same file, and skipping it is
the mistake this skill exists to prevent — so the fast path stops exactly where
the slow one does.

A context that stopped is reported as a **question, not a failure**, with the tab
to visit — the answer should be one click away rather than a hunt.

**Reconciled a rule that would otherwise have contradicted itself.**
`/orca:plan` says "inside a wave, ask normally" (1.6.0) because a plain wave is
built around the user answering questions. That is now qualified: with `--auto`
also present, defer with a named question instead. The wave collects those and
says which tabs to visit, so a deferral costs one visit — while a wrong guess
still costs a whole executor run.

## 1.10.0 — 2026-08-01

**Lanes now open normal PRs, not drafts, and the executor opens them on its own.**
Automated review tooling skips draft PRs — so a draft meant *no review happened
at all*, which is a worse failure than the one draft-mode was guarding against.

Draft status was load-bearing in exactly one way, and it is worth naming rather
than quietly dropping: it was the mechanism that made merge-before-gate
structurally impossible. With PRs opening ready, **the gate is advisory rather
than structural** — nothing but the user's own sequencing stands between an open
PR and a merge. That is an acceptable trade when the alternative is unreviewed
code, but it is a real change in what the pipeline guarantees.

- **The executor opens the PR unprompted** once the criteria are met, the tests
  pass, and its own diff review is clean — and **stops and says so if they are
  not**. An honest "blocked on X" beats a PR it would not defend, and the gate
  would find the gap anyway.
- **It still never merges.** That was always the one prohibition that mattered.

### The verdict is now a PR comment, on pass as well as fail

This follows directly. `isDraft` used to tell `/orca:status` whether the gate had
run; with every PR opening ready, that signal is gone. So `/orca:verify` now
**posts its verdict as a PR comment on every outcome**, not only on failure.

Three things that buys:

- **`/orca:status` can distinguish a gated PR from an ungated one** — the new
  `awaiting-gate` (PR open, no verdict) vs `pr-open` (verdict posted) split.
- **A reviewer on GitHub sees the evidence** at the moment they decide to merge,
  which is where they actually are.
- **The verdict outlives its session.** Previously a `pass` existed only in a
  transcript.

Under `pass-with-review`, the human criteria are listed **first** in the comment —
burying them under a green verdict is how an unverified claim gets read as a
verified one.

### Everywhere else

`_shared/evidence-gates.md` and `_shared/automation.md` updated to match. The
automation's precondition 3 changes from "draft PRs only" to "no merge authority
anywhere", and says plainly that with the gate now advisory, only the precheck
and a human stand between an opened PR and a merge under an automation.

README, `GUIDE.html`, and the pipeline diagram no longer say DRAFT.

## 1.9.1 — 2026-08-01

**Fixed: a second wave re-proposed the first wave's issues.** Found in real use.

`/orca:wave --review` read plan files from `~/.claude/plans/<repo-name>/` and
treated every one it found as a candidate. That directory **accumulates every
plan ever written for the repo**, including ones that already became lanes — so
after launching four lanes, starting a fresh wave in a new context offered those
same four plans back for launching.

Two defects, one symptom:

- **"the files for the issues in this wave" was never defined across sessions.**
  A fresh context has no memory of which issues it planned, so it globbed the
  directory. `--review` now scopes in a stated order: issue numbers in
  `$ARGUMENTS` first (the unambiguous form, and it now asks for them), then the
  wave started in this conversation, and only then an inferred set it **presents
  and confirms** rather than silently adopting.
- **`--review` and `--launch` had no in-flight check**, though bare `/orca:wave`
  has had one since 1.6.0. So the *selection* step would correctly exclude a
  launched issue while the *review* step picked it straight back off disk. Both
  now exclude any plan whose issue has a live lane, an open PR, or an assignee —
  and say which were excluded and why, so "excluded" is distinguishable from
  "never found".

`--launch` additionally **re-checks immediately before each launch** rather than
trusting §4's exclusion, which may be minutes old. `/orca:launch` refuses
in-flight work itself, so this is a second net — worth having, because a
duplicate lane means two agents opening two competing PRs for one issue.

The handback text now tells you to run `--review 84 85 86 87` with the numbers,
which is what would have prevented this. Docs and `GUIDE.html` show the numbered
form throughout.

**Nothing left after exclusion is a normal outcome**, not an error — it means
every plan on disk is already in flight, which is exactly the state that produced
this report.

## 1.9.0 — 2026-08-01

**Lane branches get a type prefix instead of your username.** Orca names a new
branch `<gitUsername>/<name>` — `tatejennings/caption-crossfade`. That says *who*
made the branch, which nobody needs (the author is in every commit) and which
tells a branch list, a PR list, and a changelog generator nothing.

`worktree create` has **no branch-name flag** — verified: `--base-branch` sets
what you branch *from*, not what the new branch is called. So `/orca:launch` now
renames immediately after creating, while the branch is fresh and has no commits:

```bash
git -C <worktree-path> branch -m <type>/<slug>
```

`<type>` comes from the issue's labels and title — `fix`, `feat`, `docs`,
`chore`, `spike` — but **the repo's own convention wins**: read recent branch
names first, since a repo using `feature/` should not suddenly get `feat/`.

**Verified safe, and the verification found a quirk worth knowing.**
`orca worktree ps` reports the renamed branch correctly, so `/orca:status` and
every other skill keep working — but **`orca worktree show` caches the original
and goes stale.** Two rules follow, now in `_shared/orca-lanes.md`: prefer `ps`
over `show` where a rename is possible, and resolve worktrees by `path:` or
`id:` rather than `branch:` afterwards.

A failed rename never stops a launch — a branch name is cosmetic, the lane is the
point.

*(The prefix is also settable per repo via `orca project setup-update
--git-username`, but that is one fixed string for every branch in the repo and
cannot express a per-issue type. Renaming is the finer instrument.)*

**`/orca:launch` now says the planning session can be closed.** Nothing about a
lane depends on it: the plan is on disk, the contract is a file the executor
already read, the issue link is in Orca's worktree record, and the criteria are
on the issue — which is exactly why the contract is written to a file rather than
passed inline. The one thing closing loses is the conversation that produced the
plan, so the skill flags it when **Decisions already made** looks thin: that
reasoning exists only in the transcript, and adding a line to the plan file now
is cheaper than reconstructing it later.

## 1.8.2 — 2026-08-01

**Wave tabs carry a topic, not just a number.** `plan #84` said which ticket but
not what it was, and a tab bar is scanned rather than read. Tabs are now
`#84 balance tuning`, `#85 overlay fixes`, `#87 cloud sync`.

The rules matter more than the format, because an Orca tab truncates at roughly
20–25 characters and a title that clips mid-word is worse than a short one:
two or three words, take the *distinctive* ones rather than the first (drop a
leading task id, drop everything after a colon — that is usually the qualifier,
not the subject), reuse the scope label where it fits since it is already the
short name for that area, and lowercase, which reads better at tab size.

**The number always survives truncation** — that is the one part that must never
be lost.

`/orca:launch`'s worktree naming is deliberately unchanged: a sidebar entry has
different constraints from a tab, and kebab-case under ~30 characters already
suits it.

## 1.8.1 — 2026-08-01

**Install docs lead with the GitHub form.** `claude plugin marketplace add
tatejennings/orca-skills` installs directly — no clone needed — but that was
buried in a parenthetical after a three-command clone-first recipe, so the
simplest path read as the advanced one. Both README and `GUIDE.html` now show
GitHub first, the local clone second (for reading or modifying the skills), the
in-session slash-command form for each, and the two-command update that a
GitHub-sourced marketplace needs.

The update step is worth its space: refreshing the catalog does **not** update
the installed copy, and running only the first command is a quiet no-op.

## 1.8.0 — 2026-08-01

**Four independent reviewers audited the suite** — correctness, triggering,
workflow gaps, and internal consistency. Everything below came from that pass.

### A real bug: `worktree ps` spans every repo

`orca worktree ps` returns **every worktree Orca knows about, across all repos**,
and has no `--repo` flag. `/orca:launch` and `/orca:wave` filtered only on
`linkedIssue` — a bare integer with no repo qualifier — so **a lane on issue #84
in an unrelated repo would falsely block a launch here.** Verified live: one
response, five repos. All three call sites now filter on `repoId` +
`linkedIssue` + `isMainWorktree`, and `_shared/orca-lanes.md` states the scope.

Two related fixes: `--limit 200` is now passed explicitly (the default cap is
unspecified, and a truncation would silently under-report lanes), and
`/orca:status` records the primary checkout's path **before** the lane filter
removes it — the non-isolation guard was comparing against a value it could never
have read when run from inside a lane.

### The rework loop had no owner

The most common event in this system is `/orca:verify` returning `fail` — and
nothing handled it. The gate's fail path terminated in *"comment the criteria so
the next session can act"* without saying how that session comes to exist, while
`/orca:launch` **actively refused** to start one ("already in flight"). The one
skill that starts agents blocked the most common reason to start one.

`/orca:launch` gains a **rework path**: an existing lane or draft PR is no longer
a refusal when coming back from a failed gate. It reuses the lane rather than
creating one, carries the failed criteria *and their evidence* into a rework
contract, and tells the executor to push to the existing draft PR — the four ways
a rework contract differs from a fresh one are tabulated, because getting them
wrong produces an executor that opens a second PR against its own branch.

### A passing gate silently expired

`/orca:verify` noted a moved base and did nothing with it. So: lane passes Monday
night, another lane merges Tuesday, the evidence was computed against a tree that
no longer exists — and `/orca:status` still showed a healthy `pr-open` lane ready
to merge. The plugin's central claim quietly stopped holding for every lane that
was not merged first.

Now a moved base **annotates the verdict** ("evidence computed against a base N
commits behind; re-run after rebasing"), and a branch that no longer merges
cleanly is a **fail** — no criterion about it is meaningful until it can land.
`/orca:status` reads `mergeable`, `mergeStateStatus`, `statusCheckRollup`, and
`updatedAt` from the PR call it already makes, so a conflicted or CI-failing lane
stops reading as healthy. **The gate is not CI**, and the two are now shown side
by side rather than leaving the wrong inference available.

### The dead zone after a pass

`pr-open` was the one lane state with no next-action line — gated, ready, blocked
on a human, and silent. It now says so, with the PR's age, and flags one that has
sat past about a week.

### Lane recovery, and the malformed-merge repair

`stalled` said "reopen a session or remove it" and both halves were dead ends.
Now: **resume** names the contract file that survives at
`~/.claude/plans/…prompt.md` and is exactly what a resumed session reads;
**abandon** names the full pre-deletion checklist, especially the dirty-tree
check, since unmerged work is what is at risk.

A merged PR that closed no issue now states the remedy: **the human closes it
with a comment naming the PR.** "Never close an issue by hand" binds skills and
executors, not a person repairing a malformed merge — without that, the lane is
reported forever and the backlog stays wrong.

### Triggering

- **`/orca:launch` was conceding phrases it should win.** `orca-cli` claims "hand
  off"/"handover", and the disambiguation lived in the body — invisible before
  routing. It now claims those phrases *when the work is a GitHub issue or an
  agreed plan*, and names `orca-cli` for a handover with neither behind it.
- **`/orca:plan` matched only phrasings containing the word "plan."** Added the
  ones people actually type: "how should we approach #84", "what would it take to
  add X", "scope out #84", "think this through before we build it".
- **`/orca:verify` now names `/code-review`** rather than gesturing at "a code
  review", and says it is not CI.
- **`/orca:triage` vs `/orca:migrate`** were separated by one word each ("clean up
  the backlog" vs "clean up how we track tasks"). Triage now states the altitude
  test in its description and **guards on it**: an unmigrated repo gets pointed at
  `/orca:migrate` instead of a confusing "nothing to do" over an empty backlog.
- **`/orca:wave`'s description never mentioned `--launch`** while the body
  implements it. Both flags are now trigger surface.

### Two data-integrity guards

- **`/orca:plan` no longer overwrites an existing `### Done when` checklist.**
  Criteria written earlier — by `/orca:triage`, with the user — are the stronger
  gate. It shows both and asks.
- **`/orca:triage` refuses to edit criteria on an issue with a live lane or open
  PR.** The executor is bound to those criteria and the gate will apply them;
  changing them mid-flight invalidates both silently.

### Consistency

Stale counts ("six consumers", "five skills", "Five files"), a surviving "chunk"
in `/orca:plan`, a pre-rename "plan → handoff → verify" in `CONTRIBUTING.md`, and
a **factual error in `_shared/automation.md`** — `show`/`edit`/`run` accept a
positional id *or* `--id`; only `runs` is `--id`-only.

The `--reap` pre-delete re-check list now includes check 5 (`HEAD ==
headRefOid`). It guards against losing post-merge commits, and a commit landing
between scan and delete is exactly as plausible as the dirty file check 3
already re-runs for.

**README and `GUIDE.html`**: the `--launch` flag table listed **four**
disqualifiers where the skill defines five — the adopted-plan case was missing
from both, and 1.6.1's changelog entry then asserted "four", laundering the
undercount into the record. Also added to the guide: the schema-version
mechanism, the `gh` multi-account warning, the path to `automation.md`, and the
`CONTRIBUTING.md` link.

### New: `/audit-orca`

A repo-maintenance skill in `.claude/skills/`, not shipped. Every `orca` CLI fact
here was verified against one version on one day; Orca updates independently and
nothing would notice a vanished flag until a user hit it. It re-checks every
referenced command and flag against live `--help`, compares Orca's bundled skill
triggers against ours for new collisions, reports new CLI surface worth adopting,
and updates the version stamp — **only on a run that found no breaks**, since the
stamp asserts the facts were verified.

Orca was already at 1.4.163 while the stamp said 1.4.162, which is the drift it
exists to catch.

## 1.7.0 — 2026-08-01

**`/orca:triage` now leads with its primary input: a pasted list of raw items
that are not yet issues.** Filing them is the skill's job — the user should not
have to create GitHub issues by hand before triaging, since that is the work
being delegated.

The capability was technically present in 1.3.0 but buried: one sentence in §1,
every example showing issue numbers, and a description that opened with "a batch
of issues". A skill that supports a case but presents as if it does not will not
trigger on it, which is the same as not supporting it.

- **Three input shapes, stated in order of how often they are used:** a pasted
  list of raw items (§1a), specific issue numbers (§1b), nothing at all for a
  full backlog audit (§1c).
- **Raw items are filed one at a time, as each is triaged** — not created up
  front and groomed after. An item abandoned mid-pass was never filed, and the
  questions shape the body rather than patching it afterwards.
- **Duplicate check before filing.** A backlog dump usually repeats something
  already open; the skill searches and asks rather than creating a second copy.
- **A raw item and an existing issue get different passes.** There is no body to
  read for a raw item, so it plays back what it understood and proposes a title
  first — the cheapest error to catch and the most expensive to leave. For a bug
  the missing piece is usually the reproduction; for a research item it is what a
  *finding* would look like, since that is its acceptance criterion.
- **The user's phrasing is the requirement.** Sharpen the title, keep the
  meaning.

`README.md` and `GUIDE.html` both lead with the paste-a-list form, and the
"capturing work mid-flight" workflow is rewritten as **"emptying your head into
the backlog"**. The claim that filing needs no skill is corrected: triage *is*
the capture step, and a capture skill that only created thin issues would just
hand more work to triage.

## 1.6.2 — 2026-08-01

**`GUIDE.html`** — the README's content laid out visually: the three-gate pipeline
as an actual diagram, every skill as a card carrying its own invocation, the
verdicts colour-coded, and the six workflows as expandable panels.

Generated and **gitignored**, for the same reason `ROADMAP.md` is: it is derived
from the README, so committing it would create a second copy to keep in step and
a diff to review on every docs change.

That gitignoring has one cost worth naming — **nothing in a diff will remind
anyone it exists**, so it can rot silently. Both `CLAUDE.md` and
`CONTRIBUTING.md`'s after-edit checklists now carry an explicit step:
regenerate it whenever `README.md` changes, and create it if it is missing. A
guide that lags the README reads as current, which is worse than not having one.

Verified at build: the HTML parses with no unclosed or mismatched tags, and all
seven skills, five flags, and six workflows appear in both files.

## 1.6.1 — 2026-08-01

**README rewritten** as usable documentation rather than a description of the
design.

- **Every skill gets its own section** with a plain statement of what it does and
  copy-pasteable invocations, grouped by intent: getting a repo ready, deciding
  how to do the work, doing it, proving it was done.
- **A complete flag table.** Five flags across three skills — `--launch`,
  `--review`, `--reap`, `--no-roadmap` — each with what it actually does,
  including `/orca:plan --launch`'s four disqualifiers.
- **Six workflows** end to end: onboarding a repo, one issue start to finish,
  several in parallel, fire-and-forget, keeping the backlog honest, and capturing
  work mid-flight (which needs no skill).
- **"The conventions the skills read"** — milestones, no-milestone as the
  unscheduled backlog, dependency edges over labels, the `### Done when`
  checklist with its three criterion buckets, and the two labels the skills
  understand (`manual` and scope labels). Previously these were scattered across
  `TRACKING.md` and individual skills; a user had no single place to learn what
  the skills expect of their repo.
- `/orca:verify`'s three verdicts are stated in the README, since
  `pass-with-review` is the distinction most likely to be misread as a weaker
  `pass`.

Also corrects `/orca:plan`'s description, which still described `--launch` in
pre-rename terms and did not mention that it saves a plan file or that
`/orca:wave` exists for planning several issues at once.

## 1.6.0 — 2026-08-01

**New skill: `/orca:wave`** — plan several issues at once, one terminal each,
then check the finished plans against each other before anything launches.

The original review panel cut a fan-out skill on the grounds that it duplicated
an automation and that Orca's `orchestration` doctrine forbids worktrees created
merely for parallelism. **The second objection does not apply here**: planning
writes no repo files, so every context shares the current checkout and no
worktree is created. Only `/orca:launch` makes a lane.

The value is not throughput. **Two issues that are independently ready can still
edit the same file**, and `/orca:status` cannot see that — it knows dependency
edges, not file overlap. Comparing finished plans is the only place a collision
is detectable *before* work starts, which is why the skill stops after review
rather than launching.

- **Contexts are interactive by design.** Each runs `/orca:plan <n>` in its own
  titled tab (`plan #84`), asks its own questions, and waits. The user visits
  each and answers. `/orca:plan` now states this explicitly: inside a wave, ask
  normally — do **not** adopt `--launch`'s defer-instead-of-asking posture just
  because the context was started programmatically.
- **The skill does not supervise.** It starts the contexts, reports the tab
  titles, and stops. Polling them would waste context and risk acting on a
  half-finished plan; they are talking to the user, not to it.
- **`--review` then `--launch`**, as two deliberate steps. A collision is
  reported as a *sequencing* problem — launch one, let it merge, re-plan the
  other — not as a verdict that a plan is wrong.
- Capped at ~4 per wave: past that the contexts sit idle waiting on a user who
  cannot hold four planning conversations at once.
- Excludes work already in flight, blocked, or `manual`, and flags issues with no
  `### Done when` checklist as cheaper to fix in `/orca:triage` first.

**Fixed a real gap this exposed:** `/orca:plan` never wrote a plan file — the
plan lived in conversation, and only `/orca:launch` wrote anything to disk. That
made a plan unreadable outside its own context, so `--review` would have had
nothing to compare. `/orca:plan` now saves to
`~/.claude/plans/<repo-name>/<date>-<issue>.md` before presenting, which also
means a plan survives its session and can be handed to `/orca:launch` later.

## 1.5.0 — 2026-08-01

**`/orca:handoff` is now `/orca:launch`.** Breaking, and worth it: the old name
collided with vocabulary Orca's own bundled skills already claim.

`orca-cli`'s description lists **"full handoff", "handover", "give this to
another agent"** as its triggers, and `orchestration`'s spends a sentence
redirecting *"hand off", "handoff", "handover"* to `orca-cli`. So "handoff" was
claimed twice by skills shipped with the binary — and this plugin's description
used the same phrases, competing for them. That is precisely the semantic
collision this plugin's own authoring rules warn about, and the old name walked
into it.

`launch` names the outcome rather than the gesture: the skill produces a **lane**
— a worktree with an agent already working. It does not perform the CLI-level
handover; `orca-cli` owns that, and the skill body now says so explicitly.

- The description no longer uses "hand off"/"handover" as triggers at all,
  leaving those to `orca-cli`. It leads with "launch a lane for #84", "start work
  on issue 84", "spin up a session to build this".
- `/orca:plan --launch` now invokes a skill of the same name, which reads more
  obviously than `--launch` invoking `handoff` did.
- Prose across the suite reworded from "handing work off" to "starting it in a
  lane" where the change reads better; the mechanical sense of "handoff" is kept
  where it is still accurate (`_shared/orca-lanes.md`'s "handoff invocation" is
  the CLI command, and correctly named).

Earlier changelog entries keep the old name — they describe releases where that
is what it was called.

## 1.4.0 — 2026-08-01

**The `manual` label** — work no agent can do: account access, store or console
configuration, a physical device, a purchase, a legal review. A convention the
skills understand, not a project-specific label.

The distinction that makes it useful:

| Situation | Where it belongs |
|---|---|
| The **whole task** needs a human | the `manual` **label** |
| **Some acceptance criteria** need human judgement | the `### Done when` **checklist** |

An issue with a few `*(human)*` criteria is still agent work — an agent
implements and a person judges the rest at review. Labelling that `manual` would
hide real available work. Conversely, an issue that is *only* human should never
reach a lane, because an agent will either stall or fake its way to a PR.

- **`/orca:status`** lists them under **`YOUR TASKS`**, a section of their own
  directly after `READY NEXT`. Not hidden (they are real work) and not mixed in
  (they cannot be launched). Blocked/ready is computed the same way, and the
  section is omitted entirely when empty.
- **`/orca:handoff`** refuses to launch a lane for one and says what the issue
  needs from the user instead. This is the payoff — it stops an agent being
  handed something it structurally cannot finish. An explicit override still
  works, with a warning.
- **`/orca:triage`** asks when it is not obvious from the issue.

Recognition is loose: a repo may spell it `human`, `human only`, or `needs
human`, so the skills match on meaning and report which label they matched
rather than requiring the exact string. As with scope labels, they never rename a
repo's existing label.

## 1.3.1 — 2026-08-01

**Scope labels get a documented rule**, from noticing in the field that a
grouping label is only useful if a reader can understand it without a legend.

`../_shared/issue-schema.md` gains a section: when filing or triaging, list the
repo's existing labels and **reuse** one; if none fits, **create one named for
the area of the work**; never leave scope unlabelled because nothing matched.

What makes a good scope label:

- **Named for the area, not a letter.** `sound` beats `workstream:E` — these
  surface in `/orca:status`, where a code means nothing.
- **No prefix.** `sound` reads better than `area:sound` on a chip.
- **One concern each.** A label covering two unrelated areas should be two
  labels.
- **Consistent separator.** Spaces or hyphens, but not both — mixing them means
  nobody can guess a label's exact name. GitHub's own defaults (`good first
  issue`, `help wanted`) use spaces, so a repo that has not chosen should follow
  them.

**`/orca:triage` now flags a missing scope label** as a triage gap, asks which
part of the system an issue touches, and reports mixed separators **once for the
repo** rather than per issue — normalizing means recreating labels and moving
every issue, which is the user's call.

**Neither skill renames existing labels to match a convention.** Vocabulary
belongs to the project; the skills reuse and add.

## 1.3.0 — 2026-08-01

**New skill: `/orca:triage`** — the sixth, and the one that closes the loop
between filing an issue and planning it.

Every other skill assumes a well-formed issue: `/orca:plan` wants requirements,
`/orca:handoff` copies the `### Done when` checklist into the executor contract,
`/orca:verify` gates on it. `/orca:migrate` retrofits that shape across a whole
backlog **once**. Nothing handled the ongoing case — the issue filed last week
with a one-line body and no milestone.

**Batch in, one at a time out.** Takes a list of issue numbers, a filter, or a
pasted pile of bugs/features/research items, reports the whole batch up front so
the size is known, then works through them individually. Questions are chosen per
issue rather than run from a script — an issue that already has clear scope may
need only a milestone, and asking six questions about it trains the user to skim.

**With no arguments it audits the entire open backlog**, and distinguishes two
kinds of problem because they need different questions:

- **Never triaged** — no milestone, no criteria, or a body too thin to act on.
  Gets the full pass.
- **Drifted since triage** — a `blocked` label whose blockers have all closed, a
  dependency written only in prose with no edge, criteria under the wrong
  heading, a closed milestone, an assignee gone quiet. Usually needs one
  confirmation, not a re-interrogation.

**Mechanical drift is batched, not asked one by one.** A stale `blocked` label or
a wrong heading has exactly one correct fix; those are offered as a group and do
not count against the ~10-item judgement cap. **A prose dependency is explicitly
not mechanical** — resolving which issue `W1` names is a guess unless the title
matches, and a wrong edge hides available work.

Design decisions worth recording:

- **Audit lives here, not in a separate skill.** An audit that finds "#101 has no
  criteria" and then fixes it *is* triage; splitting them would produce one skill
  that finds problems and hands them to the one that does the work.
- **It does not overlap `/orca:migrate`.** Both audit, at different altitudes:
  migrate checks repo-level structure (tracking block, tracked files regrowing
  progress, schema version); triage checks per-issue hygiene (criteria,
  milestones, edges, labels). Neither subsumes the other.
- **No `/orca:capture`.** Filing an issue is `gh issue create`, which needs no
  skill.
- **Bugs, features, and research are one workflow**, not three. The questions are
  identical and only the label differs; a research item's honest "done" is a
  written finding, which the schema's prose bucket already covers.
- **A clean audit reports what it checked**, not just "nothing to do" — the
  latter is indistinguishable from a run that failed to look.

## 1.2.0 — 2026-08-01

Three findings from running the suite against a real, partially-migrated repo,
folded back into the skills. **No schema bump** — none of these change what a
migrated repo must look like; they make `/orca:migrate` better at *finding*
problems, which is detection, not contract.

**Dependencies hide in prose, and that is usually where the real ones are.**
`/orca:migrate` now greps issue bodies for `**Prereqs:**` lines, "after X lands",
"requires Y" and similar, then proposes real edges. In the repo this was tested
against, three issues carried precise ordering in prose with **no** GitHub edge —
invisible to every readiness query, so all three reported ready. Converting only
`blocked` *labels* would have missed all of it. Prose that names work by a
project-local id (`W1`, `E2`) is resolved by title, and anything unresolvable is
listed rather than guessed: a wrong edge hides available work, which is worse
than a missing one. The prose stays in place — it carries reasoning the edge
cannot ("W1, parallel-safe with W2").

**Two dateless milestones mean nothing resolves as active.** Previously a note;
now a proposed fix, because the consequence is concrete — `/orca:status` has to
ask on every run, which makes it interactive and breaks `/loop`. Later milestones
stay deliberately dateless so they cannot win the nearest-due-date rule.

**Two things get called "the roadmap".** `TRACKING.md` gains a table separating
the **plan** (narrative, tracked, changes when a decision changes) from the
**tracker** (`ROADMAP.md`, generated, changes every run). A planning doc that
carries no status is the narrative half working correctly, **not** a violation —
so `/orca:migrate` proposes only a header line naming the distinction, never a
migration of the doc. The test is whether it records *progress*: "F2 depends on
E1" is a plan; "F2 — in progress" is state.

**Also**

- `/orca:migrate` checks for acceptance *criteria*, not the literal `### Done
  when` heading. An issue may state them in prose or under another heading, in
  which case the fix is a rename — not authoring new criteria, which would risk
  fabricating a gate.
- "No milestone" is documented as the **unscheduled backlog** and a valid state.
  `/orca:migrate` explicitly does not propose a "Backlog" milestone: a permanent
  bucket makes its progress count meaningless and adds another candidate for
  "active".
- The `AGENTS.md` fragment gains three rules — planning docs are not status
  boards, blocking is an edge rather than a label, and no-milestone means
  unscheduled.

## 1.1.0 — 2026-08-01

**`ROADMAP.md` is now regenerated on every `/orca:status` run**, not only behind
a flag. `--roadmap` is replaced by `--no-roadmap`, which suppresses it.

The reasoning: an opt-in write means the file goes stale the moment you forget
the flag, and **a stale generated file is worse than no file** — it still looks
current. "Truth is rebuilt, never stored" does not hold if the rendering is only
sometimes rebuilt. Since the file is derived and gitignored, regenerating it
destroys nothing and cannot conflict, so the usual reason to withhold a write
does not apply.

This does cost the skill its unqualified "read-only" claim, so that is stated
honestly rather than quietly dropped: the roadmap file is the one thing a bare
run writes, and three guards bound it. **Any guard failing skips the write and
reports one line — it never fails the run:**

- **Never write a tracked `ROADMAP.md`** — that is the conflict surface the whole
  model exists to avoid. This guard carries more weight now that the write is
  unprompted.
- **Never create the file in a repo with no backlog** — pointing the skill at an
  unrelated repo must not litter it. An existing file is still refreshed.
- **Never write outside the primary checkout.**

`--reap` is unchanged and still opt-in; deleting worktrees is a different class
of action from refreshing a derived file.

## 1.0.3 — 2026-07-31

**`/orca:verify`'s failure path is now exercised.** A gate that has only ever
returned `pass` is untested, and this was precondition #1 for ever enabling the
automation. Run against a throwaway issue and two constructed branches in this
repo; issue closed and branches deleted afterward.

What the probe confirmed:

- **`fail` reports every unmet criterion, not just the first** — three failures,
  each with its own evidence (exit code, match count, changed-file list).
- **`pass-with-review`, never `pass`**, once the checkable criteria were
  satisfied but a prose criterion remained. That distinction is the difference
  between a gate and a rubber stamp, and it holds.
- **Prose criteria are deferred, never guessed at.**

Two frauds the gate claims to catch were reproduced deliberately, and **both
would have passed a naive implementation**:

- **Pre-existing artifact.** For a criterion demanding a *new* file, "does it
  exist" passed while the correct check — `--diff-filter=A` plus a merge-base
  probe — failed. The exact commands are now in `_shared/evidence-gates.md`
  rather than left as prose.
- **Removed-line match.** On a branch that *deleted* the required token, a
  whole-diff `grep` returned 1 match and would have passed; the added-lines-only
  grep returned 0 and correctly failed. A branch removing the thing the criterion
  demanded would have been waved through.

Both are documented as verified, with the commands that distinguish them.

## 1.0.2 — 2026-07-31

**`orca worktree create` does not always create a checkout.** Found by probing a
real create response; it invalidates an assumption inherited from the planning
document and fixes a defect that could have committed to the wrong repository.

Against a repo Orca registered as **`kind: folder`** rather than `kind: git`,
`worktree create --agent claude --json` returned `ok: true` with `path` equal to
the **primary checkout**, `branch: ""`, `head: ""`, and a three-segment id
(`<repoId>::<path>::workspace:<uuid>`). `git worktree list` showed one checkout:
Orca had created a metadata-only workspace entry pointing at the primary
checkout, not an isolated worktree.

**Why a repo ends up `kind: folder`:** this one was registered with Orca while
its `HEAD` was still unborn — a fresh `git init` with zero commits, so there was
no git repo to detect. **The classification is sticky**: it stayed `folder` after
the repo had five commits, a GitHub remote, and a working tree `git` was entirely
happy with. A repo can look healthy to `git` and still be unable to produce
worktrees, which is why the check is worth its one call.

An earlier draft of this entry blamed the `projectId` prefix
(`github:<owner>/<repo>` vs `repo:<uuid>`). **That was wrong** — a `kind: git`
repo carries the `github:` form too. `kind` is the discriminator.

**The fix, verified end to end:**

```bash
orca project setups --json                                  # find the setup id
orca project setup-update --setup <id> --kind git --json
```

After reclassifying, `worktree create` produced a real isolated checkout at
`~/orca/workspaces/<repo>/<name>/`, with a two-segment id, a derived branch
(`refs/heads/<git-username>/<name>`), and `--git-dir` ≠ `--git-common-dir`.
`orca repo add --path` is **idempotent and does not re-detect**, so it is not a
fix.

This also **restores the branch-derivation claim** that 1.0.2's first draft had
weakened: Orca does derive `refs/heads/<git-username>/<name>` on a `kind: git`
repo. The username comes from Orca's per-repo `gitUsername` and is not
necessarily the GitHub account you would guess, so the branch is still read back
from the response rather than predicted.

Why that mattered:

- **`/orca:handoff` would have launched an agent into the primary checkout** —
  the user's real working directory — while reporting it as an isolated lane.
  The executor would have committed onto whatever branch was checked out there.
- **`/orca:status` would have rendered it as a lane**, since the filter was
  `repoId` + `isMainWorktree: false` and the entry reports `false`.
- **`--reap` was already safe.** Its `--git-dir` vs `--git-common-dir` proof
  would have found them equal and refused to delete. The one check written to be
  paranoid is the one that held.

Fixes:

- **`/orca:handoff` now verifies isolation before reporting success**, with the
  git proof, and stops with an explanation if the worktree shares the primary
  checkout's path. `ok: true` is explicitly not sufficient.
- **`/orca:status` drops entries whose `path` equals the primary checkout's** and
  reports them separately as non-isolated, rather than as lanes.
  `isMainWorktree: false` is documented as necessary but not sufficient.
- **Branch is never predicted or reported empty.** `result.worktree.branch` came
  back `""` — as it does for the primary worktree in `worktree list` — so the
  skills fall back to `git branch --show-current` and, failing that, say the
  branch could not be determined.
- **Worktree IDs may have three segments.** The shared spec no longer implies
  exactly two.

Also confirms the response shape that was previously unverified:
`result.worktree.{path,branch,id}` and `result.agentTerminalHandle` (with
`result.startupTerminal.handle` as an alias), closing the honest gap recorded in
0.3.0.

## 1.0.1 — 2026-07-31

**`blockedBy.nodes` carries `state` — verified on live data**, closing the one
open question in `_shared/github-backlog.md`. Nodes also carry `number`,
`title`, `url`, and `id`.

Two corrections follow, and both make the readiness logic simpler *and* more
correct:

- **Readiness is one pass over the list output, with no follow-up calls.** The
  spec previously told callers to resolve each blocker's state with a per-issue
  `gh issue view`. That fan-out is now deleted.
- **`totalCount > 0` never meant "blocked", and the old wording risked implying
  it.** GitHub keeps the relationship after a blocker closes, so an issue whose
  blockers have all closed still reports a non-zero count while being perfectly
  ready. The rule is now stated as: ready ⇔ every node's `state` is `CLOSED`
  (vacuously true at count 0). An implementation that read the count would have
  reported ready work as permanently blocked.

`/orca:status` now reports blockers **by number and title** (`blocked by #87 (K1
· CloudSyncService)`), which `nodes` provides for free. `/orca:handoff` and
`/orca:plan` read `state` rather than the count when deciding whether work is
blocked.

`/orca:migrate`'s decorative-blocking check is unchanged in substance — a
blocking *label* with `totalCount == 0` is still exactly the defect it looks for
— but the condition is spelled out rather than left as "compare".

## 1.0.0 — 2026-07-31

The suite is complete: five skills and one disabled-by-default automation.

**`/orca:status`** — the read-only dashboard, and the join this plugin exists for.
Orca knows lanes; GitHub knows the backlog; neither is complete alone.

- **The lane half is one call.** `orca worktree ps --json` already returns branch,
  `linkedIssue`, `linkedPR`, `workspaceStatus`, `liveTerminalCount`, and live
  `agents[].state`. Per-lane fan-out is explicitly forbidden — only `git status`
  and `rev-parse HEAD` are fetched per lane, and only for lanes that might be
  reapable.
- **`linkedPR` is a number, not a state**, so PR state comes from one repo-wide
  `gh pr list` joined locally by branch.
- **New verdict `awaiting-gate`** — a draft PR with no agent running. That is a
  lane asking for `/orca:verify`, and it is the state this pipeline is built
  around. A draft PR is the expected shape, never a problem to report.
- **Degrades honestly**: Orca down ⇒ backlog half only; `gh` down ⇒ lane half
  only; both ⇒ stop. Never presents a partial run as complete.
- **Reports decorative blocking**: issues with a `blocked` label but no
  dependency edge are called ready, and the report says so rather than silently
  trusting either signal.
- **`--roadmap`** regenerates the gitignored `ROADMAP.md`, and **refuses to write
  it if it is tracked** — pointing at `/orca:migrate`, which proposes untracking
  with consent.
- **`--reap`** deletes only `merged-reapable` lanes, re-running the
  primary-checkout proof immediately before each delete. Ambiguity is always a
  skip, never a prompt.

**`/orca:verify`** — the evidence gate, and the one genuinely new thing here.

- Checks the branch against the issue's own `### Done when` checklist: runs the
  command criteria, greps **added lines only** for diff assertions, and **refuses
  to guess** at prose criteria.
- **No checklist ⇒ stop.** Inventing criteria and then passing them is the exact
  failure the gate exists to prevent.
- **Checkbox state is never evidence.** `- [x]` means someone typed an `x`.
- Catches two subtle frauds by construction: a **pre-existing** artifact offered
  for a criterion demanding a new one, and **stale evidence** produced before the
  change it supposedly validates.
- Three verdicts, and `pass` vs `pass-with-review` is load-bearing — `pass` is
  impossible while any human criterion is outstanding.
- Reports **every** failed criterion, so an executor does not burn a cycle per
  failure.
- Never merges, never closes an issue, never marks a PR ready unprompted.

**`/orca:plan`** — adversarial planning: parallel research agents, a drafted plan,
then a cold-reader agent attacking completeness, holes, single-context
feasibility, and blast radius.

- **Writes the `### Done when` checklist onto the issue.** This is what makes the
  work gateable later, and it is part of planning rather than an afterthought.
  Fabricating criteria is called out as worse than a short honest list.
- Adopts a pre-written plan verbatim rather than re-planning it, while still
  reviewing it.
- **`--launch`** hands the approved plan to `/orca:handoff`. Five disqualifiers
  stop an auto-launch — a split verdict, an unresolved fork, a review finding
  against an adopted plan, work already in flight, or Orca unavailable.

**The automation** (`_shared/automation.md`) — a config artifact, not a skill,
and **shipped disabled**.

- The precheck is where safety lives: it fails closed, and carries readiness,
  concurrency caps, daily PR caps, issue-collision checks, and the circuit
  breaker.
- Eight preconditions before enabling, the first being that `/orca:verify` has
  been seen to **fail** on incomplete work — a gate that has only ever passed is
  untested.
- **Verified**: automation subcommands take a positional `<id>` (`show`, `edit`,
  `run`) except `runs`, which takes `--id`. The CLI is genuinely inconsistent
  here, so the file says so rather than assuming symmetry.

## 0.3.0 — 2026-07-31

**`/orca:handoff`** — hands a GitHub issue or an agreed plan to a fresh agent in
its own Orca worktree, then stops. Reads the issue and its `### Done when`
criteria, refuses to launch over work already in flight, derives the worktree
name, writes an executor contract outside the repo, creates the lane with the
issue linked natively, and reports the branch Orca actually derived.

The launch command itself lives in `_shared/orca-lanes.md`; this skill owns the
layer around it — what gets handed off, and what binds the executor.

Load-bearing details:

- **The contract goes outside the repo.** A new checkout cannot see another
  checkout's untracked files, but any absolute path is readable. The launch
  prompt stays a single pointer sentence so nothing multi-line has to survive
  shell quoting.
- **The issue's `### Done when` checklist is copied into the contract verbatim**,
  so the executor sees exactly the criteria `/orca:verify` will later apply. No
  checklist ⇒ the contract says so explicitly rather than letting the executor
  assume.
- **Never launch a second lane on an issue that already has one.** Checked
  against live worktrees (`linkedIssue`) and open PRs before creating anything.
- **The branch is read back, never predicted.** Orca derives
  `refs/heads/<user>/<name>` itself.
- **Draft PRs only**, and the executor is told never to mark its own PR ready —
  that waits on the evidence gate and a human.
- **A rejected `--agent claude` stops the run.** Silently substituting another
  agent is worse than failing.
- **The skill never monitors the lane it launches.** A full handoff that starts
  supervising is a different request, and Orca's bundled `orchestration` skill
  owns it.

**Honest gap:** the exact nesting of the worktree object inside the create
response is not documented by `orca agent-context`, which covers commands and
flags but not response shapes. Rather than assert a path verified only against a
transcript from an older Orca build, the skill reads the response defensively and
falls back to `orca worktree show`. Worth pinning down on the first real launch.

## 0.2.0 — 2026-07-31

First skill: **`/orca:migrate`**.

**Tracking model schema: v1.** This release establishes the versioned contract a
consuming repo is migrated *to*. The version is recorded in the repo's
`AGENTS.md` block as `<!-- orca-skills tracking model v1 -->`, and
`/orca:migrate` reads it to decide what a later run needs to do. **A schema bump
is not a plugin version bump** — most releases change no repo-side convention and
leave the schema alone.

**`/orca:migrate`** — brings a repo's tracking up to the model: inventories every
tracking file, classifies each *section* as live state / finished state /
narrative / reference, proposes milestones, issues with a `### Done when`
checklist, real dependency edges, spec files, file edits, and the `AGENTS.md`
block — then applies only what is approved. Nothing is written before approval,
and nothing is committed at all: file changes are left in the working tree so the
diff remains rejectable.

It handles three conditions, which **compose** rather than exclude each other:

| Condition | Cause |
|---|---|
| Never migrated | The model was never applied here |
| **Schema lag** | *The model moved* — a plugin release now expects something new |
| **Drift** | *The repo moved* — practice slipped away from the model |

A repo that is a version behind has usually also drifted, so both are always
evaluated and reported as one proposal with the two halves separated.

Design decisions worth recording:

- **Named `migrate`, not `adopt`.** "Adopt" implies a one-time onboarding. The
  model itself changes across releases, so a conforming repo can fall behind
  through no fault of its own — that is a migration, and it recurs.
- **The schema marker is a claim, not proof.** It records what a past run
  applied, not what is true now. A current marker never skips the drift audit.
- **Severe drift is not a fix-list.** When live work has moved back outside
  GitHub Issues, per-issue patching cannot restore the model; the skill re-runs
  its full inventory over the regressed parts instead.
- **Order is not negotiable**: labels and milestones, then issues, then
  dependencies, then specs, and only then file deletions. Never delete the only
  copy of something before its replacement exists.
- **Never fabricate acceptance criteria.** A thin issue honestly marked thin
  beats an invented checklist that would pass a gate which should have failed.
- **Gitignoring a tracked file is a no-op.** Untracking `ROADMAP.md` requires
  `git rm --cached` and therefore explicit consent; a tracked narrative roadmap
  is legitimate and stays if the user wants it.

**Also**

- `agents-fragment.md` now carries the schema marker in the fenced block, and
  documents why it is not decoration.

## 0.1.0 — 2026-07-31

Initial scaffold. No skills yet — this release is the plugin skeleton and the
shared specs every skill will read.

**Plugin**

- `.claude-plugin/marketplace.json` — the `orca-skills` catalog, one plugin.
- `plugins/orca/.claude-plugin/plugin.json` — plugin identity at `0.1.0`.

**Shared specs** (`plugins/orca/skills/_shared/`)

| File | What it fixes in place |
|---|---|
| `github-backlog.md` | Milestone resolution, the one-call readiness query, `gh` constraints and gotchas. App-agnostic — GitHub only. |
| `agents-fragment.md` | The block `/orca:migrate` appends to a consuming repo's `AGENTS.md`, including the issue-schema and generated-roadmap rules. |
| `issue-schema.md` | **New.** The `### Done when` contract all five skills read — and the three buckets (command / diff assertion / human) that make a criterion checkable. |
| `orca-lanes.md` | **New.** Orca's identity and selector model, native lane fields, deletion safety, degraded mode, and the proven handoff invocation. |
| `evidence-gates.md` | **New.** How `/orca:verify` checks a criterion: evidence rules, verdicts, and the prohibition on guessing at human criteria. |

**Docs** — `README.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `TRACKING.md`.

**Two facts verified live against `orca` 1.4.162** that would otherwise have
shipped as defects:

- **Repo `displayName` does not track the directory name.** `--repo
  name:<dir-name>` returns a hard `repo_not_found`, not an empty result. Every
  skill resolves repos by `path:` or `id:`. Found by checking rather than
  trusting a planning document — the rule that requires this caught it.
- **The worktree ID key differs between commands.** `worktree list --json`
  returns it as `id`; `worktree ps --json` returns the same value as
  `worktreeId`. Reading the wrong key yields `undefined` and degrades silently.

**Design notes**

- Scope is five skills — `migrate`, `handoff`, `status`, `verify`, `plan` — plus
  one disabled-by-default automation. An adversarial review panel cut an earlier
  8-skill proposal on the grounds that most were wrappers over capability Orca
  already has; `migrate` was added back because the other four consume a tracking
  convention that nothing else establishes.
- **Skills are app- and project-agnostic.** No skill names a project, milestone,
  label, or acceptance criterion. Project-specific conventions live in the
  consuming repo.
- **The roadmap is generated and gitignored** — a rendering of GitHub state, so
  it cannot conflict and cannot drift.
