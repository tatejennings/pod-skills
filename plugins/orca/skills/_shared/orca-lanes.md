# Orca lanes — the identity, selector, and safety model

What every skill in this plugin needs to know about Orca's own model: how a
worktree is identified, how to resolve one safely, and which facts are native
(so we never reconstruct them) versus which we must derive ourselves.

> **Orca's bundled skills own the CLI.** `orca skills get orca-cli` documents the
> commands; `orca skills get orchestration` documents multi-agent coordination.
> **Read those rather than trusting this file for CLI usage** — they ship with the
> binary and are version-matched to it, while this file is a separate artifact
> that can drift. What follows is only the subset this plugin's skills depend on,
> plus the gotchas that bit us in practice.
>
> **Where the boundary sits:** `orca-cli` owns *how the CLI works*. This plugin
> owns *what to hand off and what contract binds the executor*. When a skill here
> needs to explain a command's mechanics, it points at `orca-cli` instead.

Verified against `orca` **1.4.162**, 2026-07-31. Re-verify with
`orca <group> --help` before writing any new CLI fact into a skill — never from
memory. That rule has caught real defects, including one below.

## Verified facts

Everything in this section was checked against live `--help` or live `--json`
output at the version above.

### A worktree ID is `<repoId>::<absolute-path>`

```
<repo-uuid>::/absolute/path/to/checkout
```

Both halves matter: the repo UUID and the absolute filesystem path, joined by
`::`. Take the exact string from a command's JSON output — never assemble one.

**The key name differs between commands.** This is a real trap:

| Command | Field holding the ID |
|---|---|
| `orca worktree list --json` | `result.worktrees[].id` |
| `orca worktree ps --json` | `result.worktrees[].worktreeId` |

Same value, two names. A skill reading the wrong key gets `undefined` and
silently degrades.

### Selectors — how to name a worktree

`--worktree` accepts: `id:<repo-id>::<path>`, `name:<displayName>`,
`branch:<branch>`, `issue:<number>`, `path:<path>`, and `active`/`current`.
`--repo` accepts `id:<id>`, `name:<name>`, `path:<path>`.

**Resolve repos by `path:` or `id:`, never by `name:`.** Orca's repo
`displayName` is user-editable and frequently does *not* match the directory
name. A repo whose folder is `my-project` may be registered as `MyProject`, in
which case `--repo name:my-project` fails with `repo_not_found` — not an empty
result, a hard error. Verified live against a repo whose display name had been
edited — a broken selector here fails every skill, so do not assume the two
match.

Derive the path from the primary checkout and pass `path:<abs-path>`. Use
`name:` only for a name a human just typed and confirmed.

### Worktrees live under `~/orca/workspaces/<repo>/<name>/`

**Do not identify lanes by a path prefix.** Filter on **`repoId` plus
`isMainWorktree: false`** instead — structural, and immune to both a change in
where Orca puts worktrees and to repos whose names prefix-match each other
(`app` vs `app-website`). Treat the path layout above as informational, not as a
selector.

### Orca derives the branch itself

`worktree create` names the branch `refs/heads/<git-username>/<name>` — user-
prefixed, derived from the worktree name. **Do not pass a hand-built
`<type>/<slug>` branch and assume it took.** Read `branch` back from the create
response and use that value everywhere downstream.

### Terminal handles are routing metadata, not identity

A handle returned by `worktree create` (`agentTerminalHandle`) **can differ**
from what `terminal list` reports for the same terminal minutes later. Never
cache one across operations — re-resolve via
`orca terminal list --worktree <selector> --json` at each use.

### `--agent` produces exactly one terminal

Passing `--agent <id>` to `worktree create` launches the agent in the first
terminal and creates no stray fallback shell. Confirmed empirically. With
`--agent --json`, read the handle from `result.agentTerminalHandle`; older
runtimes return only `result.startupTerminal.handle`, and folder-based repos may
return neither.

### What Orca tracks natively — do not reconstruct it

`worktree ps --json` returns, per worktree, in **one call**:

| Field | Use |
|---|---|
| `worktreeId`, `repoId`, `path` | identity |
| `isMainWorktree` | **the deletion-safety discriminator** |
| `branch` | current branch |
| `linkedIssue`, `linkedPR` | native issue/PR links — no frontmatter needed |
| `workspaceStatus` | board column (`todo`, `in-progress`, `in-review`, `completed`) |
| `liveTerminalCount`, `hasAttachedPty` | session liveness |
| `agents[]` | `state`, `agentType`, current `toolName` per agent |
| `lastActivityAt`, `lastOutputAt` | staleness |
| `parentWorktreeId`, `childWorktreeIds` | lineage |
| `comment` | free-text note set via `worktree set --comment` |

This is why `/orca:status` is cheap: Orca stores lane state, so the lane half is
**one call for every lane**. Never fan out per-lane commands to rebuild facts
this call already returns.

What Orca does *not* have — and what this plugin adds — is the backlog half:
milestones, readiness, dependencies, git dirty state, and PR *state*
(`linkedPR` is a number, not a status; resolving it needs `gh`).

## Safety rules

### Never delete a primary checkout

`isMainWorktree: true` means the worktree **is the repo**. Deleting it destroys
the user's actual project directory.

Orca reports this natively, but a skill that deletes must **not** trust a cached
value. Confirm with git immediately before any destructive operation:

```bash
git -C <path> rev-parse --git-dir --git-common-dir
```

Different ⇒ a linked worktree, safe to consider. **Equal ⇒ a primary checkout,
never delete.** This costs one command; the failure it prevents is
unrecoverable, so never trade it for a cached flag. A `git worktree
move`/`repair`, or the user reorganizing a checkout mid-run, is rare but real.

### The full pre-deletion checklist

Every one must pass, and 1/3/4 must be re-run **immediately before** the delete —
a dirty file or a reopened terminal can appear in the seconds since a scan:

1. **Linked worktree** — the `--git-dir` ≠ `--git-common-dir` proof above.
2. **PR merged** — from `gh`, not from `linkedPR` (which is only a number).
3. **Clean tree** — `git -C <path> status --porcelain` is empty.
4. **No live terminals** — `liveTerminalCount == 0`. Necessary but **not
   sufficient**: a terminal can outlive its process, so zero means "nobody is
   watching", not "no work is in flight". Checks 1–3 are what make deletion safe.
5. **`HEAD` matches the PR's `headRefOid`** — post-merge commits would be lost.

Any check failing ⇒ skip and report which one. Never prompt, never retry.

Deletion itself: `orca worktree rm --worktree <selector> --force`. Repo-defined
`orca.yaml` archive hooks are skipped unless `--run-hooks` is passed.

### Degraded mode — when Orca is not there

These skills drive an app that may not be running. Check before assuming:

```bash
command -v orca && orca status --json     # result.runtime.reachable
```

If the CLI is missing or the runtime is unreachable, **say so and stop** rather
than half-working. The backlog half of some skills (`/orca:status`'s milestone
and readiness sections, all of `/orca:adopt`) is pure `gh` and still works —
where that is true, run it and report the lane half as unavailable. Never fail
silently and never present a partial report as complete.

## The handoff invocation

The one command that performs a full handoff — proven end-to-end:

```bash
orca worktree create --name <slug> --no-parent \
  --agent claude \
  --prompt "Read the file <abs path outside the repo> and execute its instructions exactly." \
  --issue <n> --json
```

Why each flag:

- `--no-parent` — the lane is independent work, not a child of the caller's
  context. Without it, Orca infers a parent from the calling terminal.
- `--agent claude` — one terminal, agent already running (see above).
- `--prompt` — kept to a **single short pointer sentence**. The full contract
  lives in the file, so nothing multi-line has to survive shell quoting.
- `--issue <n>` — sets `linkedIssue` natively. This is why no plan-file
  frontmatter is needed to map a lane back to its tracker entry.
- The pointer file path must be **outside the repo**: a new checkout cannot see
  another checkout's untracked files, but any absolute path is readable.

**A worktree cannot be created from an unborn `HEAD`.** A repo with zero commits
has no ref to branch from. Make the initial commit first, or use
`orca terminal create --worktree path:<repo> --command "claude"` to run an agent
in the existing checkout instead.

For a fresh agent in an *existing* checkout, always use `terminal create` — not
`worktree create`. Orca's own doctrine: create a worktree only when the user
explicitly asks for one, or a concrete checkout conflict makes sharing unsafe.
