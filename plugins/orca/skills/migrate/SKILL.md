---
name: migrate
description: Bring this repo's tracking up to the model the orca skills expect, whether it has never been migrated or was migrated under an older version of these skills - inventories every tracking file, separates live work from finished and narrative from state, proposes milestones, issues, and a "### Done when" checklist on each, and applies only what you approve. Re-run it after upgrading the plugin to move a conforming repo onto the current schema, or any time to audit for drift. Use when the user says "/orca:migrate", "set this repo up for the orca skills", "set up tracking for this project", "migrate my roadmap to issues", "migrate this project to the new skills", "I updated the plugin, update my repo", "my roadmap is a mess", "clean up how we track tasks", "the roadmap keeps causing merge conflicts", "onboard this project", or "audit our tracking". This migrates tracking *files and conventions* - "what should I work on next" is /orca:status, and planning one piece of work is /orca:plan. Not for driving the Orca app: worktrees, terminals, and agents belong to Orca's bundled orca-cli skill.
---

# Migrate tracking

Bring this repo's tracking to the model every other skill in this plugin reads:
**state in GitHub Issues, narrative in `docs/specs/`, a `### Done when` checklist
on every issue, and a generated roadmap that is never a source of truth.**

A repo can be behind the model for three independent reasons, and a single run
often finds more than one:

| Condition | Cause | Handled in |
|---|---|---|
| **Never migrated** | The model was never applied here | §1–§4, full run |
| **Schema lag** | *The model moved* — these skills now expect something new | §5a |
| **Drift** | *The repo moved* — practice slipped away from the model | §5b |

These **compose**. A repo that is a version behind has usually also drifted, since
the same months produced both. Always evaluate schema lag and drift
independently, then present one combined proposal — never report a clean audit
because the schema matched, and never skip a drift check because an upgrade ran.

Schema lag is the reason this skill is not named "adopt" and not one-time. A repo
can be perfectly faithful to what these skills expected last release and still
need work today, through no fault of its own.

**Severe drift is not a fix-list.** When enough has slipped that the repo no
longer really follows the model — a status file is back and holding live work,
most issues lack criteria — stop treating it as an audit and re-run the full
inventory (§1) over what has regressed. §5b says how to tell the difference.

The model itself — and why a tracked progress file breaks under parallel lanes —
is the plugin's `TRACKING.md`. Read `../_shared/github-backlog.md` for every `gh`
query and constraint, and `../_shared/issue-schema.md` for the issue body shape.
Do not restate them here.

**This skill proposes before it writes.** Everything below produces a plan the
user approves in one pass. Nothing is created, edited, or deleted until then.
That is what makes it safe to run just to see the report.

## What this skill is not for

- **"What should I work on next"** ⇒ `/orca:status`. This skill migrates files;
  it does not report readiness.
- **Planning one piece of work** ⇒ `/orca:plan`.
- **Worktrees, terminals, agents** ⇒ Orca's bundled `orca-cli` skill
  (`orca skills get orca-cli`). This skill never touches the Orca CLI; it works
  on the repo and GitHub only, and runs fine with Orca closed.

## 0. Preconditions

```bash
gh auth status
gh repo view --json nameWithOwner -q .nameWithOwner
```

Confirm the **active** account can push to the resolved repo — `gh` holds several
accounts with only one active, and the active one is whichever was selected last.
Wrong account ⇒ stop and say so; never file issues under the wrong identity.

No GitHub remote ⇒ stop. This model needs one; say what the repo would need.

Run from the **primary checkout** where possible. Everything here works from a
worktree, but the audit reads the whole tree and a lane may not have all of it.

## 0a. Which schema is this repo on?

Before inventorying anything, find out whether this repo has been migrated
before and under **which version of the model**. Without this, a conforming repo
on an old schema is indistinguishable from a current one, and the skill either
does nothing when it should upgrade, or re-proposes a migration that already
happened.

The marker lives in the `AGENTS.md` (or `CLAUDE.md`) task-tracking block that
§3e writes:

```markdown
## Task tracking
<!-- orca-skills tracking model v1 -->
```

Three cases:

- **No block** ⇒ never migrated. Full run: §1 through §4.
- **Block with a version marker < current** ⇒ schema lag. Run §5a's upgrade,
  **then §5b's drift audit as well** — being a version behind says nothing about
  whether the repo also slipped. Do not re-run the full migration; the repo's
  issues, specs, and files are already in the model.
- **Block at the current version** ⇒ §5b drift audit.

**A block with no marker** predates versioning: treat it as v1, since v1 is what
the unmarked block described. Note it and add the marker as part of the run.

**The marker is a claim, not proof.** It records what a past run applied, not
what is true now — someone can edit the block and change nothing else, or change
everything else and leave the block alone. Never let a current marker skip the
drift audit, and never trust it over what §5b actually observes.

The current schema version is **v1**. It is recorded in `CHANGELOG.md` under the
plugin release that introduced it; when the model changes in a way that requires
repo-side work, that version increments and §5 gains a migration step for it.
**A schema bump is not the same as a plugin version bump** — most plugin releases
change no repo-side convention at all and leave the schema where it is.

## 1. Inventory — what is here today

Read before proposing anything. Three questions, answered from the repo and
GitHub together.

### 1a. Tracking files

Search the tree for anything that records what is done or what is next:

```bash
git ls-files | grep -iE 'roadmap|todo|task|backlog|status|plan|milestone|progress|changelog'
```

Also check `docs/`, `.github/`, and the repo root for files that *act* as
trackers without saying so — a `README.md` section with checkboxes, a
`docs/NN-*.md` series where the highest number is the live one, a status table in
a design doc.

For each candidate, read it and classify **every section** (not every file — one
file is usually both):

| Class | What it is | Where it goes |
|---|---|---|
| **Live state** | Open work: unchecked boxes, "in progress", "next up", numbered upcoming items | → GitHub Issues |
| **Finished state** | Checked boxes, "done", "shipped", completed rows | → deleted, or one archival line (see §3d) |
| **Narrative** | Why the work exists, design decisions, rationale, constraints | → `docs/specs/<slug>.md` |
| **Reference** | Conventions, architecture notes, how-to — not work items at all | → stays exactly where it is |

The fourth class matters as much as the others. **Not every tracked markdown file
is a tracker**, and proposing to migrate a genuine reference doc is how this skill
loses the user's trust in one step.

### 1b. Existing GitHub state

```bash
gh api "repos/{owner}/{repo}/milestones?state=open" --jq '.[] | "\(.number)\t\(.title)\t\(.due_on // "no due date")\t\(.open_issues) open"'
gh issue list --state open --limit 200 --json number,title,milestone,labels,blockedBy,body
gh label list --limit 100
```

**An empty `[]` is ambiguous** — it means "no milestones" *and* "query returned
nothing" identically, both with exit 0. Distinguish them: if `gh repo view`
succeeded in §0, the auth and repo resolution are good, so `[]` genuinely means
none exist. Never report "no backlog" on the strength of an empty array alone.

Note especially:

- Issues with no milestone — they will need one, or an explicit "unscheduled".
- Issues whose body has **no `### Done when` section** — the gap `/orca:verify`
  cares about.
- **`blocked` labels with no real dependency edge.** A label is decorative to
  every readiness query; only `blocked-by` edges are read. If the repo expresses
  blocking with labels or prose, say so plainly: *every readiness query currently
  reports all of these ready, which is the honest reading of the data.* This is
  a common and quiet defect.

### 1c. The instructions that maintain the problem

```bash
grep -rniE 'update (the )?(roadmap|status|todo|progress)|mark .* (complete|done)|check off' \
  CLAUDE.md AGENTS.md CONTRIBUTING.md .github/ docs/ 2>/dev/null
```

Instructions telling contributors to update a tracked progress file are why a
migration reverts: the file becomes a stub, the instruction survives, and the
next session helpfully refills it. Every hit is part of the proposal.

## 2. Decide the milestone structure

Do not invent milestones from nothing. In order of preference:

1. **Existing open GitHub milestones** — use them; propose renames only if asked.
2. **Structure already implied by the tracking files** — phases, versions,
   releases, or groupings the user already wrote. Their names, not yours.
3. **Ask.** With no existing structure and no implied one, use AskUserQuestion
   with 2–3 concrete options derived from the actual work you found.

A good milestone: you would finish it and close it; exactly one is clearly
active; under ~25 open issues. See `TRACKING.md`.

**Exactly one milestone should be resolvable as active** — the open one with the
nearest `due_on`. If the proposal would leave several open with no due dates,
say so and offer to set a date on the active one; otherwise every later skill run
has to ask.

## 3. Build the proposal

Present all of it before writing anything. Group by what happens, and make each
item individually rejectable — the user will disagree with some, and re-running
the whole skill to drop one issue is a bad trade.

### 3a. Issues to create

For each live-state item, propose an issue: title, milestone, labels, and a body
following `../_shared/issue-schema.md`.

**The `### Done when` checklist is the hard part, and the point.** Derive criteria
from what the source actually says. Where the source is vague, write the honest
prose criterion rather than inventing a checkable one — `issue-schema.md`'s three
buckets exist precisely so an unverifiable criterion has a legitimate home. Do not
contort a criterion into a fake command to make a future gate go green.

Where a criterion genuinely is checkable, use the checkable form:

```markdown
### Done when
- [ ] `./scripts/test.sh` exits 0
- [ ] `docs/api.md` is modified
- [ ] Importing a malformed file surfaces an error instead of crashing
```

If an item is too thin to write any criteria for, **say so and propose it
anyway** with a `### Done when` containing one line: `- [ ] <to be defined —
this issue needs triage before it can be planned>`. A thin issue that is honestly
marked thin is better than a fabricated checklist, and better than silently
dropping the work.

Set `spec:<slug>` on issues derived from a spec, so re-running is a no-op (see
§5).

### 3b. Dependencies to record

Where the source expresses ordering ("after X", "requires Y", "blocked by Z"),
propose a real edge:

```bash
gh issue edit <blocked> --add-blocked-by <blocker>
```

These run **after** creation, since they need both numbers. Propose them as a
distinct group so the user can see the shape of the dependency graph before it
exists — and so they can correct an edge you inferred wrongly from prose.

Where the repo has **`blocked` labels with no edges**, propose converting each
one you can resolve to a real edge, and list any you cannot resolve for the user
to fill in. Do not delete a `blocked` label you could not convert; a decorative
label is bad, but silently removing the only trace of a real dependency is worse.

### 3c. Narrative to move

For each narrative section: propose `docs/specs/<slug>.md` with the text moved
**verbatim**. Do not rewrite, summarize, or improve someone's design writing —
you are relocating it, not editing it. Issues then link to the spec rather than
restating it.

### 3d. Files to change, and how

This is where care is owed, because it is the destructive half.

- **Finished state** → propose deleting those rows. Offer one archival line
  (`See closed issues in <milestone>`) rather than keeping a graveyard.
- **A file that was *only* live state** → propose deleting the file, and name
  every place that links to it (`grep -rn '<filename>'`) so nothing is left
  pointing at a corpse.
- **A file that was mixed** → propose the reduced file, showing what remains.
- **A tracked `ROADMAP.md`** needs an explicit decision, because gitignoring a
  tracked file is a **no-op** — git keeps tracking it. Two honest options, and
  the user picks:
  - *Generated:* `git rm --cached ROADMAP.md`, add it to `.gitignore`, and it
    becomes the regenerated view — `/orca:status` rewrites it on every run.
    Say plainly that untracking means the committed copy stops updating for
    anyone reading the repo on GitHub; the file survives locally and refreshes,
    but it leaves the remote.
  - *Keep it:* it stays tracked as human-authored narrative, and the generated
    roadmap uses a different filename. Legitimate — a narrative roadmap is not a
    bug. What must not happen is a *skill* writing progress into it.

  Never `git rm` someone's roadmap without this being an approved choice.

### 3e. The `AGENTS.md` block

Propose appending the fenced block from `../_shared/agents-fragment.md`
**verbatim** to `AGENTS.md` or `CLAUDE.md` — whichever the project has, preferring
the one already carrying contributor instructions; create `AGENTS.md` if neither
exists. If a `## Task tracking` heading already exists, propose a reconciliation,
not a duplicate.

**Include the schema marker** immediately under the heading — §0a reads it on
every later run, and without it a future run cannot tell an old-schema repo from
a current one:

```markdown
## Task tracking
<!-- orca-skills tracking model v1 -->
```

Write the version this run applied, not the plugin version. On a §5a upgrade,
update the marker to the version reached — and only after the upgrade's changes
are actually applied, so a partial run does not claim a schema it did not reach.

Together with §3f this is the half that makes the migration stick.

### 3f. Instructions to remove

Every hit from §1c: quote the line, and propose deleting or rewriting it. An
instruction that says "update the roadmap when you finish a task" must go, or the
next session rebuilds exactly what was just dismantled.

## 4. Approve, then apply

Present the whole proposal — counts first (`12 issues, 3 milestones, 2 specs, 4
file edits`), then the detail — and get approval. Let the user strike individual
items; apply what survives.

Order matters, because later steps depend on earlier ones:

1. **Labels and milestones** — must exist before issues reference them.
2. **Issues** — record each new number as it is created.
3. **Dependencies** — needs the numbers from step 2.
4. **Spec files** — narrative moved verbatim.
5. **File edits and deletions** — only now, once the content is safely in GitHub.
6. **`AGENTS.md` block, and the §3f removals.**
7. **`.gitignore`** — add `ROADMAP.md` if §3d chose "generated".

Step 5 is deliberately after 1–4: **never delete the only copy of something
before its replacement exists.** If issue creation fails partway, the tracking
file is still there and the run is resumable.

Multi-line bodies go through stdin (`--body-file -`), never `--body "…"`.

Do **not** commit. Leave every file change in the working tree for the user to
review and commit — this skill's writes are a proposal that landed, and a diff
they can still reject wholesale is the last safety net. Say so in the report.

Failures: report which step failed and what was already applied. Do not roll
back — a partial migration is recoverable and visible, whereas an automatic
rollback can destroy work that succeeded.

## 5. Re-running: schema upgrade and drift audit

This skill is idempotent by construction and is meant to be re-run — after a
plugin upgrade, or any time you want the repo checked.

Issues carrying `spec:<slug>` are diffed by title, so a re-run never duplicates
what it already created:

```bash
gh issue list --state all --label "spec:<slug>" --json number,title
```

### 5a. Schema upgrade (marker < current)

The repo is already in the model; only the delta between its schema version and
the current one is in scope. **Do not re-inventory the tree and do not re-propose
the original migration** — that work is done, and redoing it against already-
migrated files produces noise and risks duplicate issues.

Instead: for each schema version between the repo's and the current one, apply
that version's documented repo-side change. Propose the delta, apply what is
approved, then update the marker to the current version.

Schema history:

| Version | Repo-side change required |
|---|---|
| v1 | The initial model: issues carry `### Done when`; narrative in `docs/specs/`; the `AGENTS.md` block; roadmap generated, not tracked. |

When a future release changes what these skills expect of a repo, it adds a row
here **and** a step below saying exactly what to change. A schema version with no
row is a bug in the release, not a no-op — stop and say so rather than guessing
what the upgrade should do.

### 5b. Drift audit — always run this

Runs on every re-invocation: after a §5a upgrade, and on a repo whose marker is
already current. Drift is the repo moving away from the model, so it accumulates
with ordinary use and is independent of which schema version is recorded.

**What to check.** Each is a `gh` query or a `grep` you already know from §1:

| Drift | How it shows up | How to detect |
|---|---|---|
| Issues without criteria | Filed by hand since the migration — the usual source | `gh issue list --state open --json number,title,body`, check for `### Done when` |
| Decorative blocking | A `blocked` label with no edge; readiness reports it ready | `labels` contains a blocking label while `blockedBy.totalCount == 0` |
| A tracker regrowing | Progress rows reappearing in a tracked file | §1a's search, re-run |
| Reintroduced instructions | "update the roadmap when done" added back | §1c's grep, re-run |
| The block edited away | `## Task tracking` gone, gutted, or contradicted | Read `AGENTS.md`/`CLAUDE.md` |
| `ROADMAP.md` re-tracked | Someone committed the generated file | `git ls-files --error-unmatch ROADMAP.md` |
| No resolvable active milestone | Several open, none with a due date | §1b's milestone query |
| Work outside the model | Live work only in files, never filed as issues | §1a's classification |

**Then judge severity, because it decides what happens next:**

- **Localized drift** — a handful of issues missing criteria, a stale label, one
  reintroduced instruction. Propose a fix list, apply what is approved. This is
  the common case and should stay cheap.
- **Structural drift** — the model is no longer really in force: a status file is
  back and holding live work, most open issues have no criteria, or the
  `AGENTS.md` block is gone entirely. **A fix list is the wrong shape here.**
  Say plainly that the repo has regressed, then run §1's inventory over the
  regressed parts and propose a real migration for them.

The line between them is whether **live work now lives outside GitHub Issues**.
Once it does, no amount of per-issue patching restores the model — the work has
to be brought back the way §1–§4 brought it in the first time.

Nothing to change ⇒ say so in one line and stop. A clean audit should be cheap
and quiet; that is what makes it safe to run after every plugin upgrade.

### Reporting a combined run

When §5a and §5b both found work, present **one** proposal with the two clearly
separated — schema upgrade first (the model moved), drift second (the repo
moved). The user should be able to approve one and decline the other; they are
different kinds of change and one is far more likely to be contentious than the
other.

## Failure modes to avoid

- **Migrating a reference doc.** Not every tracked markdown file is a tracker.
  When unsure, leave it and ask.
- **Fabricating acceptance criteria.** A `### Done when` invented to look
  complete is worse than an honestly thin one — it will pass a gate that should
  have failed.
- **Rewriting the user's narrative.** Specs move verbatim.
- **Deleting before creating.** Order in §4 is not negotiable.
- **Gitignoring a tracked file** and reporting success. It is a no-op; the file
  stays tracked. `git rm --cached` is the actual operation, and it needs consent.
- **Silently converting a `blocked` label** you only half-understood. Propose the
  edge; let the user confirm the direction.
