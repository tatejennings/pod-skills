# The executor contract — what `/pod:launch` writes

§3 of `../SKILL.md`. A lane gets **three files**, side by side, outside the repo:

```
~/.claude/plans/<repo-name>/<YYYY-MM-DD>-<slug>.prompt.md   the contract — you write this
~/.claude/plans/<repo-name>/<YYYY-MM-DD>-<slug>.steps.md    copied from executor-steps.md
~/.claude/plans/<repo-name>/<YYYY-MM-DD>-<slug>.gate.md     copied from gate-prompt.md
```

`<repo-name>` is the primary checkout's folder name, derived as `../SKILL.md` §3
shows — never the cwd basename or the GitHub repo name.

**Copy the two static files with `cp`; never retype them.** They are the lane's
working rules and its gate, and a paraphrase drops rules without anyone
noticing. The two `cp` commands are in `../SKILL.md` §3; the sources are
`executor-steps.md` and `gate-prompt.md` in this directory.

## Three rules about the files

- **They are a snapshot, not a link.** Updating this plugin does not reach a
  lane already launched; its three files still bind it to the rules it was
  launched under. A change that must reach lanes in flight means editing their
  files under `~/.claude/plans/<repo-name>/` directly — say so when reporting
  such a change.
- **Never overwrite an existing contract** — suffix the slug instead. An
  overwritten contract silently changes what a running lane was told to do.
- The launch prompt stays a **single short pointer sentence** at the contract.
  Everything multi-line lives in the files, so nothing has to survive shell
  quoting.

## The contract template

Fill in every section; omit one only when it genuinely has no content.

```markdown
# <Issue title, or a one-line name for the work>

Implement the work described below. Read this entire file, then read the steps
file under "Files" and follow it exactly.

## The work

<2–4 sentences: the goal and the chosen approach.>

Issue: #<n> — <url>          (omit both lines if there is no issue)

## Files

- Steps: <abs path>.steps.md — how to work, review, gate, and open the PR. Binding.
- Gate prompt: <abs path>.gate.md — for the gate agent at step 7. Do not act on it yourself.
- Base branch: <base>

## Context

<Why now, relevant background, links to docs/specs/<slug>.md. Quote the issue
body rather than paraphrasing it.>

## Decisions already made

<Choices locked during planning, one line of rationale each, so they are not
re-litigated. Omit if the handoff carries no prior planning.>

## Plan

<The plan's Steps, or the path to the plan file. Omit if there is none.>

## Acceptance criteria

<The issue's ### Acceptance criteria checklist, VERBATIM. A cold agent checks
this exact list against your branch before your PR opens.

If the issue had no checklist, say so explicitly: "This issue has no acceptance
criteria. Establish them before implementing and record them on the issue — do
not assume." >

## Out of scope

<Explicit non-goals, especially adjacent work that looks related.>
```
