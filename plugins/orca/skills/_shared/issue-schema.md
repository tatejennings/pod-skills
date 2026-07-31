# Issue body schema — the contract every skill in this plugin reads

One shape, five consumers. `/orca:adopt` establishes it, `/orca:plan` writes it,
`/orca:handoff` binds an executor to it, `/orca:status` reads readiness from it,
and `/orca:verify` mechanically checks it. **Point at this file; do not restate
the schema inside a skill.**

This file is deliberately **project-agnostic**. It defines how to *express* an
acceptance criterion so a machine can check it — never what any particular
project's criteria are. Repo-specific gates live in the consuming repo, not here.

## The shape

```markdown
<one-paragraph summary of the work>

## Context

<why this exists; link to docs/specs/<slug>.md rather than restating it>

### Done when

- [ ] `./scripts/test.sh` exits 0
- [ ] `parseManifest` appears in the diff
- [ ] `docs/api.md` is modified
- [ ] The importer handles a malformed header without crashing

### Notes

<optional: anything an implementer needs that is not a criterion>
```

Only two parts are load-bearing:

- **`### Done when`** — the acceptance checklist. Required. This is what gates
  the work, and it is written **when the issue is filed**, not after the work is
  done. A checklist written afterwards describes what happened; a checklist
  written up front describes what must happen. Only the second one is a gate.
- **`### Blocked by`** is *not* part of this schema. Dependencies are real
  GitHub edges (`gh issue edit <n> --add-blocked-by <m>`), because that is what
  readiness queries read. A prose "blocked by #12" line is decorative — see
  `github-backlog.md`.

Everything else (`## Context`, `### Notes`, section order) is convention. A skill
must not fail because an issue lacks them.

## Writing a checkable criterion

`/orca:verify` sorts every checklist item into one of three buckets. The bucket
is determined by the item's **form**, so the form is the whole contract:

| Bucket | Form | How verify treats it |
|---|---|---|
| **Command** | A backticked shell command: `` `./scripts/test.sh` `` | Runs it; exit 0 passes |
| **Diff assertion** | `` `<string>` appears in the diff``, or `` `<path>` is modified`` | Greps the branch diff |
| **Human** | Any prose that is neither of the above | **Reports, never asserts** — surfaced for a human to judge |

The third bucket is the important one. A criterion like "the importer handles a
malformed header without crashing" is a perfectly good acceptance criterion and a
machine cannot check it. `/orca:verify` must **never** guess at these, never mark
them passed, and never let them block a verdict silently — it lists them as
requiring human judgement. A gate that quietly passes what it cannot check is
worse than no gate.

Write criteria in the checkable forms **where you honestly can**, and in prose
where you cannot. Do not contort an unverifiable criterion into a fake command
just to make the gate go green — that defeats the entire point of the gate.

### Recognizing the forms

Keep recognition loose and conservative:

- **Command**: the item is (or begins with) a single backticked token that looks
  like an executable path or a known runner. If it is ambiguous whether prose is
  a command, treat it as **human** — running an arbitrary sentence is worse than
  deferring it.
- **Diff assertion**: matches `<backticked thing> appears in the diff` or
  `<backticked path> is modified` (and near-synonyms: "is present in", "changed",
  "touched"). Anything vaguer is **human**.
- Never infer a criterion from a checkbox's *checked state*. `- [x]` in an issue
  body means someone typed an `x`; it is not evidence. Verify checks the world,
  not the checkbox.

## Where this schema is enforced, and where it is not

**Enforced** — a skill may require the checklist and stop without it:

- `/orca:verify` has nothing to do without a `### Done when` section. Missing ⇒
  report that the issue has no gate and stop. Do not invent criteria.

**Suggested, never required** — the repo may predate the schema:

- `/orca:status` reads readiness from milestones and dependency edges, not from
  the checklist. It works on any repo.
- `/orca:handoff` binds the executor to the checklist when one exists, and hands
  off fine when it does not — it notes the absence in the contract.
- `/orca:plan` **writes** the checklist when it drafts or refines an issue. This
  is the main way conforming issues come to exist after adoption.

`/orca:adopt` is the only skill that retrofits the schema across a backlog, and
it proposes every rewrite before making it — an issue body is someone's writing.

## Why the checklist lives in the issue

It could live in a spec file, a plan file, or a PR template. It lives in the
issue because the issue is the one artifact that:

- exists **before** the work starts (so the criteria cannot be written to fit
  the implementation),
- is visible to the planner, the executor, and the gate alike,
- survives the worktree being deleted, and
- is already the unit that `Closes #<n>` closes.

A plan file is per-lane and disappears; a PR body is written by the person the
gate exists to check. The issue is the only place the criteria are neither.
