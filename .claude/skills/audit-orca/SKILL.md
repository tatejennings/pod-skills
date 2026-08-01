---
name: audit-orca
description: Audit this plugin's skills against the installed Orca CLI and its bundled skills - re-verifies every `orca` command and flag the skills reference against live `--help` output, checks whether Orca's bundled skill descriptions have started claiming trigger phrases that collide with /orca:*, reports new CLI surface worth adopting, and updates the version stamp. Use when the user says "/audit-orca", "audit against orca", "did orca change", "check the CLI facts", "Orca updated - are we still correct", or after upgrading the Orca app. This maintains THIS repo; it is not shipped to users.
---

# Audit against the installed Orca

Every `orca` CLI fact in this plugin was verified against a specific Orca version
on a specific day. **Orca updates independently.** Flags get added, argument
styles change, response shapes shift, and bundled skill descriptions get
rewritten — and nothing in this repo would notice until a user hit a broken
command.

This skill is that notice. It is a maintenance skill for this repo, like
`/ship` — never shipped to consuming projects.

## 0. Establish the delta

```bash
orca status --json          # result.runtime.appVersion — what is installed
grep -n "Verified against \`orca\`" plugins/orca/skills/_shared/orca-lanes.md
```

Same version ⇒ say so and offer to run the checks anyway (a rebuild can change
behavior without changing the version). Different ⇒ report both numbers; that
delta is the reason to keep reading.

Orca unreachable or the CLI missing ⇒ stop. This audit is meaningless without
the real binary; do not fall back to memory.

## 1. Every referenced command still exists

Collect the distinct commands the skills reference:

```bash
grep -rhoE 'orca [a-z-]+( [a-z-]+)?' plugins/orca/skills/ | sort -u
```

Filter out prose matches (`orca skills get <name>` is a real command; "orca
worktree" alone in a sentence is not). Then check each:

```bash
orca <command> --help
```

Report anything that errors. A vanished subcommand is a **hard break** — a skill
telling an agent to run it will fail at the worst moment.

## 2. Every referenced flag still exists

This is the finer-grained and more valuable check, because a removed flag fails
silently in ways a missing command does not.

For each command above, diff the flags the skills use against live `--help`:

```bash
orca <command> --help          # authoritative list
grep -rn "orca <command>" plugins/orca/skills/   # what we tell agents to pass
```

Three findings to report separately:

- **A flag we use that no longer exists** — hard break, fix immediately.
- **A flag whose meaning or argument style changed** — e.g. positional vs
  `--flag`. The `automations` group already mixes both (`show`/`edit`/`run` take
  a positional id; `runs` takes `--id`), which is documented in
  `_shared/automation.md` precisely because it is easy to get wrong.
- **A new flag that would simplify something we do the hard way** — not a break,
  but worth surfacing (§4).

## 3. `gh` facts too

The same rot applies to GitHub's CLI, and `_shared/github-backlog.md` carries a
verified-on stamp:

```bash
gh --version
gh issue list --json nope      # enumerates every valid field
gh pr list --json nope
gh issue edit --help
```

Check especially the fields the readiness query depends on — `blockedBy`,
`blocking`, and whether `blockedBy.nodes[]` still carries `state`. That last one
is load-bearing: readiness is computed from it, and `github-backlog.md` records
it as verified on live data.

## 4. Bundled skill collisions — the subtle one

Orca ships its own skills, and **their descriptions can start claiming phrases
this plugin also claims.** That is not hypothetical: `/orca:handoff` was renamed
to `/orca:launch` in 1.5.0 precisely because `orca-cli` and `orchestration` both
list "hand off"/"handover" as their triggers.

```bash
orca skills list
orca skills get orca-cli
orca skills get orchestration
```

For each bundled skill whose scope overlaps ours (`orca-cli`, `orchestration`,
and any **new** one that appears), compare its trigger phrases against our seven
descriptions:

```bash
grep -h "^description:" plugins/orca/skills/*/SKILL.md
```

Report:

- **A phrase claimed by both** — a real routing ambiguity. The fix is usually to
  drop it from ours and name theirs, the way `/orca:launch` now does.
- **A new bundled skill** that overlaps a skill here — worth a considered
  boundary statement before users hit it.
- **A bundled skill that now does what one of ours does.** If Orca ships the
  capability natively, ours may be redundant; say so plainly rather than
  defending it.

## 5. New CLI surface worth adopting

Compare the full command list against what the skills use:

```bash
orca agent-context --json     # machine-readable schema of every command
```

Look for commands that would let a skill do something more directly than it
currently does. Report each as: what it is, which skill would use it, and what it
would replace. **Propose, do not apply** — adopting new surface is a design
decision, and the schema documents commands and flags but *not response shapes*,
so anything new still needs a live probe before it goes in a skill.

## 6. Report, and update the stamp

Report in severity order:

1. **Breaks** — a command or flag we reference that no longer exists.
2. **Collisions** — trigger phrases now contested with a bundled skill.
3. **Behavior changes** — same command, different semantics.
4. **Opportunities** — new surface worth adopting.
5. **Clean** — what was checked and found correct. Say this explicitly; an audit
   that reports only problems is indistinguishable from one that failed to look.

Then, **only if the checks passed**, update the stamp in
`_shared/orca-lanes.md`:

```
Verified against `orca` **<version>**, <YYYY-MM-DD>.
```

Do the same for `gh` in `_shared/github-backlog.md` if it moved.

**Never update a stamp on a run that found breaks** — the stamp asserts the
facts were verified, and moving it forward over known-broken facts is worse than
leaving it stale. Fix first, or leave the stamp and say why.

If anything was fixed, follow the repo's after-edit checklist in `CLAUDE.md`:
validate, bump the version, add a CHANGELOG entry, regenerate `GUIDE.html` if the
README changed, and publish.

## What this skill does not do

- **It does not test the skills' behavior**, only the facts they assert. A skill
  can reference every flag correctly and still be wrong about what to do with
  them.
- **It does not adopt new CLI surface on its own.** §5 proposes.
- **It does not touch consuming repos.** This is about this plugin's correctness.
