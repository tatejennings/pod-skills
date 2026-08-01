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

### A worktree ID is `<repoId>::<absolute-path>` — sometimes with a third segment

```
<repo-uuid>::/absolute/path/to/checkout
<repo-uuid>::/absolute/path/to/checkout::workspace:<uuid>     # also occurs
```

Take the exact string from a command's JSON output — **never assemble one, and
never assume it has exactly two segments.** The three-segment form appears for
workspace entries (see `kind: folder`, below) and is a valid selector.

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

### `worktree create` does not always create a checkout — CHECK

**Verified 2026-07-31, and this invalidates a natural assumption.** Against a
repo Orca has registered as **`kind: folder`** rather than `kind: git`,
`orca worktree create --name X --agent claude --json` returned `ok: true` with:

```json
"path":   "/Users/…/the-primary-checkout",   ← NOT a new directory
"branch": "",                                 ← no branch
"head":   "",
"isMainWorktree": false,
"id": "<repoId>::/…/the-primary-checkout::workspace:<uuid>"
```

`git worktree list` showed **one** checkout. Orca had created a metadata-only
workspace entry *pointing at the primary checkout*, not an isolated worktree.

The danger is specific and severe: an agent launched into that "lane" runs **in
the primary checkout**, on whatever branch is checked out there, while every
report calls it an isolated lane. It will commit onto `main` in the user's real
working directory.

**So never trust `ok: true` alone. After any create, verify isolation:**

```bash
git -C <returned-path> rev-parse --git-dir --git-common-dir
```

Different ⇒ a real linked worktree. **Equal ⇒ it is the primary checkout** —
report that plainly and do not treat it as a lane. Also treat an empty `branch`
or a `path` equal to the primary checkout's as a failure to isolate.

Note that `isMainWorktree: false` is **not sufficient** — the probe entry above
reported `false` while sharing the primary path. Only the git proof settles it.

### The usual cause: `kind: folder`

Check how Orca registered the repo:

```bash
orca repo list --json      # each repo's "kind": "git" | "folder"
```

- **`kind: git`** — Orca tracks it as a git repo; `worktree create` should
  produce a real isolated checkout with a derived branch.
- **`kind: folder`** — Orca treats it as a plain directory. It cannot create git
  worktrees from it, so `worktree create` yields a workspace entry sharing the
  primary path. **Verified live**: a repo registered while its `HEAD` was still
  unborn (a fresh `git init` with zero commits) was recorded as `kind: folder`
  and stayed that way after commits existed.

**The classification is sticky.** It is decided at registration and never
re-evaluated: the probe repo was still `kind: folder` long after it had commits,
a remote, and a working tree that `git` was perfectly happy with. A repo can look
completely healthy to `git` and still be unable to produce worktrees.

This is a **repo registration problem, not something a skill should work
around.** Report it and name the fix. **Verified working:**

```bash
orca project setups --json                                  # find the setup id
orca project setup-update --setup <id> --kind git --json    # reclassify
```

After that, `worktree create` produced a real isolated checkout at
`~/orca/workspaces/<repo>/<name>/`, with a derived branch and a two-segment id,
and the `--git-dir` ≠ `--git-common-dir` proof passed. Note `orca repo add
--path` is **idempotent and does not re-detect** — it returns the existing record
unchanged, so it is not a fix.

Do not silently launch an agent into a shared checkout.

The `projectId` prefix (`github:<owner>/<repo>` vs `repo:<uuid>`) is **not** the
discriminator — a `kind: git` repo can carry either. Read `kind`.

### Orca derives the branch itself — on a `kind: git` repo

**Verified**: a real worktree create returned
`branch: "refs/heads/206668354_nbcuni/shape-probe2"` — `refs/heads/<git-username>/<name>`,
user-prefixed and derived from the worktree name. The username comes from Orca's
per-repo `gitUsername`, which is **not** necessarily the GitHub account you
expect, so predicting the full ref is unwise even when the pattern holds.

- **Never pass a hand-built `<type>/<slug>` branch and assume it took.**
- **Read `branch` back** from the create response and use that value downstream.
- **Never report an empty `branch` as though it were real.** It comes back empty
  for `kind: folder` repos, and the primary worktree also reports `branch: ""` in
  `worktree list`. Fall back to `git -C <path> branch --show-current`, and if
  that is empty too, say the branch could not be determined.

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

`orca worktree ps --limit 200 --json` returns, per worktree, in one call
(**it spans every repo Orca knows about and has no `--repo` flag** — filter on
`repoId` yourself, and pass `--limit` since the default cap is unspecified):

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

Every one must pass, and **1, 3, 4 and 5 must be re-run immediately before the
delete** — a dirty file, a reopened terminal, or a new commit can all appear in
the seconds since a scan. Only 2 (a merged PR's state) is settled and reusable:

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
and readiness sections, all of `/orca:migrate`) is pure `gh` and still works —
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
