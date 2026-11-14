---
name: audit-claude-code
description: Audit this plugin's skills against the installed Claude Code - re-checks every Claude Code fact the skills lean on (tool names like AskUserQuestion, EnterPlanMode, ScheduleWakeup, Monitor; $ARGUMENTS; /loop; plan mode; plugin and skill frontmatter) against the running harness and the current docs, reads the Claude Code changelog since the last audit, and proposes features worth adopting - new frontmatter fields, harness tools, plugin schema, `claude plugin eval`. Use when the user says "/audit-claude-code", "audit against claude code", "did claude code change", "can the skills use anything new", "check for new claude code features", "are the skills using claude code well", or after a Claude Code upgrade. For the Orca CLI and gh, use /audit-orca instead. This maintains THIS repo; it is not shipped to users.
---

# Audit against the installed Claude Code

These skills run inside Claude Code and lean on it: they name its tools, read
`\$ARGUMENTS`, enter plan mode, tell the user to `/loop`. **Claude Code updates
independently and often.** A renamed tool fails silently: the skill says "use
AskUserQuestion", the tool isn't there, and the agent improvises.

This audit has two halves, with different standards:

- **Facts** (§1–2): what the skills assert about Claude Code. These either hold
  or they break. Report breaks and fix them.
- **Opportunities** (§3–4): features that would make a skill better. These are
  design decisions. **Propose, do not apply.**

`/audit-orca` covers the Orca CLI, `gh`, and Orca's bundled skills. Do not
repeat those here.

## 0. Establish the delta

```bash
claude --version
```

Compare it against the last-audited version in `CLAUDE.md` (under
`/audit-claude-code`). Then read the
Claude Code changelog for every release in between:

```
https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md
```

**That delta is the agenda.** Note every entry touching skills, plugins,
subagents, tools, hooks, plan mode, slash commands, or frontmatter; §1–4 check
each one. No recorded version yet ⇒ this is the first run: skip the changelog,
do the full sweep, and record the version at the end.

## 1. Tool names the skills reference still exist

Collect what the skills name:

```bash
grep -rnoE '\b(AskUserQuestion|EnterPlanMode|ExitPlanMode|ScheduleWakeup|CronCreate|Monitor|TaskStop|SendMessage|WebFetch|WebSearch|Agent|Skill)\b' plugins/pod/skills/ | sort -u
```

Widen the pattern if the changelog delta names tools not listed here.

**The authority is this session's own tool list**, not the docs and not memory.
The harness you are running in is the installed version, and its tools are what
a skill's agent will actually have. For each name the skills use:

- **Present** ⇒ clean.
- **Present but deferred** (listed by name, loaded via ToolSearch) ⇒ clean,
  but a skill that calls it directly needs the load step. Check that it says so.
- **Mode-gated** (e.g. `ScheduleWakeup` exists only under a dynamic `/loop`)
  ⇒ check the skill uses it only in that mode.
- **Absent** ⇒ confirm against the docs that it was renamed or removed, not
  just disabled in this session. Then it is a **hard break**.

## 2. Harness behaviors the skills assert

The rest of the surface is behavior, not a name:

```bash
grep -rnE '[$]ARGUMENTS|/loop|plan mode|/reload-plugins|claude plugin [a-z]+|claude --[a-z-]+' plugins/pod/skills/ README.md CLAUDE.md
```

For each hit, check the claim against the docs (§ Sources):

- **`\$ARGUMENTS`**: still the substitution for skill arguments, and still
  substituted in plugin skills.
- **`/loop`**: the interval syntax the skills show (`/loop 15m /pod:status`)
  still parses.
- **Plan mode**: `/pod:plan --auto` promises "never entering plan mode". Check
  that nothing now enters it automatically.
- **`claude plugin …`**: the publish commands in `CLAUDE.md` and the README
  (`marketplace update`, `update`, `validate`) still exist. Run each with `--help`.

Then run the validator. Its warnings are the cheapest signal there is:

```bash
claude plugin validate .
```

## 3. Skill and plugin schema worth adopting

The shipped skills use only `name` and `description`. Fetch the current skill
frontmatter reference and plugin manifest schema, and for each field this repo
does not use, ask whether a specific skill would be better with it:

- **Tool restrictions** (`disallowed-tools`, not `allowed-tools`, which
  pre-approves rather than restricts): `status` and `verify` promise to only
  read. A restriction would enforce that promise rather than state it.
- **Argument hints**: every skill reading `\$ARGUMENTS` has an argument shape
  the user could be shown.
- **Invocation control** (e.g. user-only invocation): a skill that should never
  auto-trigger. A user-only skill cannot run under `/loop` or be invoked by
  `tech-lead` through the Skill tool.
- **YAML in descriptions**: in an unquoted description, ` #` starts a comment
  and drops the rest. `grep -n '^description:.* #' plugins/pod/skills/*/SKILL.md`
  must come back empty.
- **Model or context settings**: a skill that would be better forked or on a
  different model.
- **Description limits**: a length cap or truncation rule. The descriptions
  here are long and pushy by design, and a cap would cut off trigger phrases
  without any error. **If a limit exists and a description exceeds it, that is
  a break, not an opportunity.**
- **Plugin manifest and marketplace fields**: anything new in `plugin.json` or
  `marketplace.json`.

## 4. Harness features worth adopting

Read the changelog delta and the docs for features that would replace something
a skill does the hard way. Look hardest at:

- **`tech-lead`**: it runs a loop with hand-written bounds and a ledger. Check
  for scheduling, background monitoring, or workflow features that could carry
  part of it. **Its bounds are the design** (see `CLAUDE.md`): a feature can
  replace the mechanism, never relax a bound.
- **`plan` (several issues) and `launch`**: they drive terminals and agents. Check for native
  ways to watch or message a running agent.
- **`claude plugin eval`**: this repo has no tests. An eval suite could check
  routing by behavior: that "what should I work on next" reaches `/pod:status`
  and not `/pod:tech-lead`, and that no `/pod:*` skill fires on a phrase Orca's
  bundled skills own.

Report each as: the feature, the skill that would use it, what it would
replace, and what could go wrong. **The skills must stay app- and
project-agnostic** (`CLAUDE.md`). A feature only some users have, such as a
paid tier, a desktop-only tool, or a research preview, can be offered as an
option. It cannot become a requirement.

## 5. Report, and record the version

Report in severity order:

1. **Breaks**: a tool, syntax, or command the skills reference that no longer
   works as stated.
2. **Behavior changes**: same name, different semantics.
3. **Opportunities**: schema (§3) and features (§4), each with its skill and
   tradeoff.
4. **Clean**: what was checked and found correct. Say this explicitly; an audit
   that reports only problems is indistinguishable from one that failed to look.

Then update the version line under `/audit-claude-code` in `CLAUDE.md`:

```
Last audited against Claude Code **<version>**, <YYYY-MM-DD>.
```

**Breaks block it; open suggestions do not.** Never record a version over an
unfixed break. Suggestions have already reached the user in the report, so
holding the version back for them would only resurface ideas already declined.

If anything was fixed, follow the after-edit checklist in `CLAUDE.md`.

## Sources

In order of authority:

1. **This session's tool list**: ground truth for tool names (§1).
2. **`--help` and `claude plugin validate`**: ground truth for CLI commands.
3. **The official docs**: skills, plugins reference, subagents, hooks, and
   settings pages. Delegate the lookup to the `claude-code-guide` agent with
   specific questions ("what frontmatter fields does a SKILL.md accept, and
   which work in plugin skills?"), not "what's new".
4. **The changelog**: what moved, and when. It sets the agenda; the docs
   settle the facts.

Never assert a Claude Code fact from memory. The harness changes faster than
any model's training data.

## What this skill does not do

- **It does not audit Orca or `gh`.** That is `/audit-orca`.
- **It does not adopt features on its own.** §3–4 propose.
- **It does not test the skills' behavior**, only the facts they assert.
  `claude plugin eval` is how that would happen, and §4 proposes it.
- **It does not touch consuming repos.**
