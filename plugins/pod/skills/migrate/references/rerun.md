# Re-running `/pod:migrate` — schema upgrade and drift audit

`../SKILL.md` §0a sends you here when the repo already carries the tracking
block. §1–§4 of that file are the first migration; this is every run after it.
Section numbers continue from there.

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
| v1 | The initial model: issues carry an acceptance checklist under `### Done when`; narrative in `docs/specs/`; the `AGENTS.md` block; roadmap generated, not tracked. |
| v2 | That checklist's heading is renamed to **`### Acceptance criteria`**. Nothing else changes — same items, same forms, same meaning. |

When a future release changes what these skills expect of a repo, it adds a row
here **and** a step below saying exactly what to change. A schema version with no
row is a bug in the release, not a no-op — stop and say so rather than guessing
what the upgrade should do.

#### v1 → v2: rename the acceptance checklist heading

**Every skill reads both headings**, so this upgrade is a tidy-up, not a repair —
a repo that never runs it keeps working. Say that plainly when you propose it, so
nobody believes their backlog is broken.

Find the issues still using the old heading:

```bash
gh issue list --state all --limit 500 --json number,title,body \
  --jq '[.[] | select(.body | test("(?m)^#{2,4} +Done when *$")) | {number, title}]'
```

For each, rewrite **only that heading line** and leave the body otherwise byte-identical:

```bash
gh issue view <n> --json body --jq .body > /tmp/issue-<n>.md
# replace the single heading line, e.g. '### Done when' → '### Acceptance criteria'
gh issue edit <n> --body-file /tmp/issue-<n>.md
```

Rules that keep this safe:

- **Only the heading changes.** Not the checklist items, not their order, not
  their checked state, not surrounding prose. An acceptance criterion is an
  executable contract (`../../_shared/evidence-gates.md`); a migration that edits one
  is changing what a branch will be gated against.
- **Match the heading anchored to its own line**, at any depth (`##`–`####`), and
  only when `Done when` is the whole heading text. A line mentioning "done when"
  inside a sentence, or a criterion containing the words, is not a heading.
- **Skip closed issues unless the user asks for them.** They are history; nothing
  will gate them again. Offer it, default to open only.
- **An issue with both headings is a conflict, not a rename** — report it and
  leave it alone. Two acceptance checklists means someone was mid-edit, and
  picking one is a decision you do not get to make.
- **Batch, and report counts**: how many rewritten, how many skipped and why.
  This can touch hundreds of issues, so it goes through the same approval gate as
  everything else here — propose, then apply.

Then update the marker to v2.

### 5b. Drift audit — always run this

Runs on every re-invocation: after a §5a upgrade, and on a repo whose marker is
already current. Drift is the repo moving away from the model, so it accumulates
with ordinary use and is independent of which schema version is recorded.

**What to check.** Each is a `gh` query or a `grep` you already know from §1:

| Drift | How it shows up | How to detect |
|---|---|---|
| Issues without criteria | Filed by hand since the migration — the usual source | `gh issue list --state open --json number,title,body`, check for `### Acceptance criteria` **or** the older `### Done when` — an issue carrying either has criteria |
| Issues still on the old heading | Filed before v2, or by someone copying an old issue | Same query. **Not a defect** — every skill reads both. Offer the v1→v2 rename above; never report it as missing criteria |
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
