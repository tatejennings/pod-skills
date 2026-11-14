#!/usr/bin/env python3
"""Lane x backlog join for /pod:status. Read-only except the gitignored ROADMAP.md.

Everything is derived on each run from orca, git and gh; nothing is cached.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys

TAG = re.compile(r"<!--\s*orca:verify\b([^>]*)-->")
WORD = re.compile(r"orca:verify\s+—\s+(PASS-AGENT-JUDGED|PASS-WITH-REVIEW|PASS|FAIL)\b")
CRITERIA = re.compile(r"(?mi)^#{2,4}\s+(acceptance criteria|done when)\s*$")
MANUAL = {"manual", "human", "human only", "human-only", "needs human", "needs-human"}
OWNER = {"needs-owner", "needs owner", "decision", "owner-decision", "needs decision", "needs-decision"}
# Orca agent states are working | blocked | waiting | done; only the first is mid-task.
ACTIVE_STATES = {"working"}
PASSING = {"PASS", "PASS-AGENT-JUDGED", "PASS-WITH-REVIEW"}


def run(cmd, cwd=None, timeout=60):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, "", str(e)


def run_json(cmd, cwd=None):
    code, out, err = run(cmd, cwd)
    if code != 0:
        return None, err or out
    try:
        return json.loads(out), None
    except ValueError as e:
        return None, str(e)


def short(ref):
    return (ref or "").replace("refs/heads/", "")


def primary_from_git(cwd):
    code, out, _ = run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd)
    return os.path.dirname(out) if code == 0 and out else None


def read_lanes(cwd):
    """Returns (lanes, primary_path, notes, error)."""
    if not shutil.which("orca"):
        return None, None, [], "orca CLI not found"
    st, err = run_json(["orca", "status", "--json"])
    if not st or not st.get("result", {}).get("runtime", {}).get("reachable"):
        return None, None, [], "Orca runtime unreachable"
    cur, err = run_json(["orca", "worktree", "current", "--json"], cwd)
    if not cur:
        return None, None, [], f"orca worktree current failed: {err}"
    repo_id = cur["result"]["worktree"]["repoId"]
    ps, err = run_json(["orca", "worktree", "ps", "--limit", "200", "--json"])
    if not ps:
        return None, None, [], f"orca worktree ps failed: {err}"
    notes = []
    if ps["result"].get("truncated"):
        notes.append("orca worktree ps was truncated at 200 rows; lanes may be missing")
    mine = [w for w in ps["result"]["worktrees"] if w.get("repoId") == repo_id]
    primary = next((w["path"] for w in mine if w.get("isMainWorktree")), None) or primary_from_git(cwd)
    lanes = []
    for w in mine:
        if w.get("isMainWorktree"):
            continue
        if primary and os.path.realpath(w["path"]) == os.path.realpath(primary):
            notes.append(f"non-isolated workspace entry points at the primary checkout: {w['worktreeId']}")
            continue
        lanes.append(w)
    return lanes, primary, notes, None


def lane_git(path):
    g = {"dirty": None, "head": None, "detached": None, "branch": "", "error": None}
    code, out, err = run(["git", "-C", path, "status", "--porcelain"])
    if code != 0:
        g["error"] = err or "git status failed"
        return g
    g["dirty"] = bool(out)
    g["head"] = run(["git", "-C", path, "rev-parse", "HEAD"])[1] or None
    g["branch"] = run(["git", "-C", path, "branch", "--show-current"])[1]
    g["detached"] = not g["branch"]
    return g


def ci_state(rollup):
    states = [(c.get("conclusion") or c.get("state") or c.get("status") or "").upper() for c in rollup or []]
    if not states:
        return "none"
    if any(s in ("FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE") for s in states):
        return "failing"
    if any(s in ("PENDING", "IN_PROGRESS", "QUEUED", "EXPECTED", "WAITING", "") for s in states):
        return "pending"
    return "green"


def read_verdict(pr, trusted, path, cwd):
    """Newest orca:verify comment from a trusted author, checked against the PR's current head."""
    data, err = run_json(["gh", "pr", "view", str(pr["number"]), "--json", "headRefOid,comments"], cwd)
    if not data:
        return {"state": "error", "detail": err}
    tagged = [c for c in data.get("comments", []) if TAG.search(c.get("body") or "")]
    good = [c for c in tagged if (c.get("author") or {}).get("login") in trusted]
    out = {"state": "none", "untrusted": len(tagged) - len(good)}
    if not good:
        return out
    body = good[-1]["body"]
    attrs = dict(re.findall(r"(\w+)=(\S+)", TAG.search(body).group(1)))
    word = WORD.search(body)
    if not word:
        out.update(state="malformed")
        return out
    out.update(head=attrs.get("head"), base=attrs.get("base"))
    stale = {"stale_verdict": word.group(1)}
    if not attrs.get("head") or attrs["head"] != data["headRefOid"]:
        out.update(stale, state="stale", detail=f"verdict head {str(attrs.get('head'))[:7]} != PR head {data['headRefOid'][:7]}")
        return out
    if path and attrs.get("base") and pr.get("baseRefName"):
        code, mb, _ = run(["git", "-C", path, "merge-base", "HEAD", f"origin/{pr['baseRefName']}"])
        if code == 0 and mb and mb != attrs["base"]:
            out.update(stale, state="stale", detail="base moved under the verdict")
            return out
    out.update(state="fresh", verdict=word.group(1))
    return out


def classify(lane, pr, git, verdict, prs_unreadable=False):
    """One verdict per lane, in the resolution order the skill documents."""
    live = (lane.get("liveTerminalCount") or 0) > 0
    active = any(a.get("state") in ACTIVE_STATES for a in lane.get("agents") or [])
    if git.get("error"):
        return "needs-attention", f"could not read the worktree: {git['error']}"
    if git["detached"]:
        return "needs-attention", "detached HEAD"
    if prs_unreadable:
        return "needs-attention", "PR state could not be read from GitHub — nothing about this lane is known"
    if pr is None:
        return ("working", "") if (active or live) else ("stalled", "session gone with unmerged work")
    if pr["state"] == "MERGED":
        if git["dirty"]:
            return "needs-attention", "dirty tree on a merged PR"
        if git["head"] != pr["headRefOid"]:
            return "needs-attention", "merged PR but HEAD has commits the PR does not"
        return ("merged-live", "merged; close its terminals, then reap") if live else ("merged-reapable", "run /pod:status --reap")
    if pr["state"] == "CLOSED":
        return "needs-attention", "PR closed without merging"
    v = verdict or {"state": "none"}
    if v["state"] == "error":
        return "needs-attention", f"could not read PR comments: {v.get('detail')}"
    if v.get("untrusted"):
        return "needs-attention", "a verdict from an untrusted author was found and ignored"
    if v["state"] == "malformed":
        return "needs-attention", "verdict comment carries the tag but no recognisable verdict"
    if v["state"] == "fresh" and v["verdict"] == "FAIL":
        return "gate-failed", "its own gate rejected this branch — do not merge"
    if v["state"] == "none":
        return ("working", "") if active else ("awaiting-gate", "PR open but never gated — /pod:verify")
    if v["state"] == "stale":
        return ("working", "") if active else ("gated-stale", f"current code is unchecked ({v.get('detail')}) — /pod:verify")
    return "pr-open", f"gated {v['verdict']}, awaiting your review and merge"


def labels(issue):
    return {l["name"].lower() for l in issue.get("labels") or []}


def open_blockers(issue):
    return [b for b in (issue.get("blockedBy") or {}).get("nodes") or [] if b.get("state") == "OPEN"]


def read_backlog(cwd, manual, owner):
    ms, err = run_json(["gh", "api", "repos/{owner}/{repo}/milestones?state=open"], cwd)
    if ms is None:
        return None, f"gh milestones failed: {err}"
    issues, err = run_json(["gh", "issue", "list", "--state", "all", "--limit", "500", "--json",
                            "number,title,state,milestone,labels,blockedBy,body,assignees"], cwd)
    if issues is None:
        return None, f"gh issue list failed: {err}"
    dated = sorted((m for m in ms if m.get("due_on")), key=lambda m: m["due_on"])
    active = dated[0] if dated else (ms[0] if len(ms) == 1 else None)
    out = {"milestones": ms, "issues": issues, "active": active,
           "active_ambiguous": active is None and len(ms) > 1, "manual": manual, "owner": owner}
    return out, None


def build(args):
    cwd = os.getcwd()
    res = {"generated": dt.datetime.now().astimezone().isoformat(timespec="minutes"), "notes": []}
    lanes, primary, notes, lane_err = read_lanes(cwd)
    res["notes"] += notes
    res["lanes_error"] = lane_err
    res["primary"] = primary or primary_from_git(cwd)
    has_remote = run(["git", "remote", "get-url", "origin"], cwd)[0] == 0
    code, login, _ = run(["gh", "api", "user", "--jq", ".login"], cwd) if has_remote else (1, "", "")
    trusted = set(args.trusted) | ({login} if code == 0 and login else set())
    res["trusted"] = sorted(trusted)

    prs, pr_err = (None, "no GitHub remote")
    if has_remote:
        prs, pr_err = run_json(["gh", "pr", "list", "--state", "all", "--limit", "100", "--json",
                                "number,state,isDraft,headRefName,headRefOid,baseRefName,mergedAt,url,"
                                "closingIssuesReferences,mergeable,statusCheckRollup,updatedAt"], cwd)
    res["github_error"] = pr_err if prs is None else None

    rows = []
    for w in lanes or []:
        git = lane_git(w["path"])
        branch = short(w.get("branch")) or git["branch"]
        cands = [p for p in prs or [] if branch and p["headRefName"] == branch]
        opens = [p for p in cands if p["state"] == "OPEN"]
        pr = (opens or sorted(cands, key=lambda p: p["updatedAt"], reverse=True) or [None])[0]
        verdict = read_verdict(pr, trusted, w["path"], cwd) if pr and pr["state"] == "OPEN" else None
        state, action = classify(w, pr, git, verdict, prs_unreadable=has_remote and prs is None)
        closes = [c["number"] for c in (pr or {}).get("closingIssuesReferences") or []]
        flags = []
        if len(opens) > 1:
            flags.append("lane invariant broken: two open PRs from one branch")
        if pr and pr["state"] == "OPEN":
            if pr.get("mergeable") == "CONFLICTING":
                flags.append("will not merge as-is — rebase needed")
            if ci_state(pr.get("statusCheckRollup")) == "failing":
                flags.append("CI failing")
            if not closes:
                flags.append("PR body has no `Closes #n` — the merge will not close the issue")
        if pr and pr["state"] == "MERGED" and not closes:
            flags.append("merged without `Closes #n` — the issue is still open; close it by hand")
        rows.append({
            "name": os.path.basename(w["path"]), "worktreeId": w["worktreeId"], "path": w["path"],
            "issue": w.get("linkedIssue") or (closes[0] if closes else None), "branch": branch,
            "pr": pr and {"number": pr["number"], "state": pr["state"], "url": pr["url"],
                          "updatedAt": pr["updatedAt"], "headRefOid": pr["headRefOid"], "ci": ci_state(pr.get("statusCheckRollup")),
                          "mergeable": pr.get("mergeable"), "isDraft": pr.get("isDraft")},
            "gate": verdict, "liveTerminals": w.get("liveTerminalCount") or 0,
            "agents": [a.get("state") for a in w.get("agents") or []],
            "lastActivityAt": w.get("lastActivityAt"), "git": git,
            "verdict": state, "action": action, "flags": flags,
        })
    paths = [r["path"] for r in rows]
    for r in rows:
        if paths.count(r["path"]) > 1:
            r["flags"].append("lane invariant broken: two lanes share one worktree path")
    res["lanes"] = None if lanes is None else rows

    backlog = None
    if has_remote and not (lanes == [] and prs is None):
        backlog, berr = read_backlog(cwd, MANUAL | {x.lower() for x in args.manual_label},
                                     OWNER | {x.lower() for x in args.owner_label})
        if backlog is None:
            res["github_error"] = berr
    res["backlog"] = summarise(backlog, rows, prs) if backlog else None
    res["waiting"] = waiting(res)
    if backlog and not args.no_roadmap:
        res["roadmap"] = write_roadmap(res["primary"], backlog, rows)
    return res


def summarise(b, rows, prs):
    in_flight = {r["issue"] for r in rows if r["issue"]}
    for p in prs or []:
        if p["state"] == "OPEN":
            in_flight |= {c["number"] for c in p.get("closingIssuesReferences") or []}
    out = {"active": None, "active_ambiguous": b["active_ambiguous"], "ready": [], "blocked": [],
           "manual": [], "needs_owner": [], "decorative_blocked": 0,
           "open_milestones": [m["title"] for m in b["milestones"]]}
    a = b["active"]
    if not a:
        return out
    out["active"] = {"title": a["title"], "due": (a.get("due_on") or "")[:10] or None,
                     "closed": a["closed_issues"], "total": a["closed_issues"] + a["open_issues"]}
    for i in sorted(b["issues"], key=lambda i: i["number"]):
        if i["state"] != "OPEN" or (i.get("milestone") or {}).get("title") != a["title"]:
            continue
        ls, blockers = labels(i), open_blockers(i)
        if "blocked" in ls and not (i.get("blockedBy") or {}).get("totalCount"):
            out["decorative_blocked"] += 1
        if i["number"] in in_flight:
            continue
        row = {"number": i["number"], "title": i["title"],
               "blockedBy": [{"number": x["number"], "title": x.get("title")} for x in blockers],
               "criteria": bool(CRITERIA.search(i.get("body") or ""))}
        if ls & b["manual"]:
            out["manual"].append(row)
        elif ls & b["owner"]:
            out["needs_owner"].append(row)
        elif blockers:
            out["blocked"].append(row)
        else:
            out["ready"].append(row)
    return out


def waiting(res):
    """Everything that cannot move without the user, most urgent first."""
    items = []
    order = ["gate-failed", "needs-attention", "awaiting-gate", "gated-stale", "pr-open", "stalled", "merged-live"]
    for r in sorted(res["lanes"] or [], key=lambda r: order.index(r["verdict"]) if r["verdict"] in order else 99):
        if r["verdict"] in order:
            pr = f"PR #{r['pr']['number']}" if r["pr"] else r["name"]
            items.append(f"{pr} (#{r['issue']}) · {r['verdict']} — {r['action']}")
        for f in r["flags"]:
            items.append(f"{r['name']} · {f}")
    b = res["backlog"] or {}
    items += [f"#{i['number']} {i['title']} · needs your decision" for i in b.get("needs_owner", [])]
    items += [f"#{i['number']} {i['title']} · manual" for i in b.get("manual", []) if not i["blockedBy"]]
    return items


def write_roadmap(primary, b, rows):
    if not primary:
        return "skipped: primary checkout not found"
    target = os.path.join(primary, "ROADMAP.md")
    if run(["git", "-C", primary, "ls-files", "--error-unmatch", "ROADMAP.md"])[0] == 0:
        return "skipped: ROADMAP.md is tracked — /pod:migrate proposes untracking it"
    if not b["milestones"] and not b["issues"] and not os.path.exists(target):
        return "skipped: this repo has no backlog"
    lane_by_issue = {r["issue"]: r["branch"] for r in rows if r["issue"]}
    ms = sorted(b["milestones"], key=lambda m: m.get("due_on") or "9999")
    lines = ["# Roadmap", "", "<!-- GENERATED by /pod:status — do not edit; it is rewritten on every run -->",
             f"<!-- {dt.datetime.now().strftime('%Y-%m-%d %H:%M')} -->", ""]
    for m in ms:
        total = m["closed_issues"] + m["open_issues"]
        lines += [f"## {m['title']} ({m['closed_issues']}/{total} closed)", ""]
        for i in sorted((i for i in b["issues"] if (i.get("milestone") or {}).get("title") == m["title"]),
                        key=lambda i: i["number"]):
            note = ""
            if i["state"] == "OPEN":
                blockers = open_blockers(i)
                if i["number"] in lane_by_issue:
                    note = f"    in flight — {lane_by_issue[i['number']]}"
                elif blockers:
                    note = "    blocked by " + ", ".join(f"#{x['number']}" for x in blockers)
            lines.append(f"- [{'x' if i['state'] == 'CLOSED' else ' '}] #{i['number']}  {i['title']}{note}")
        lines.append("")
    with open(target, "w") as f:
        f.write("\n".join(lines))
    ignored = run(["git", "-C", primary, "check-ignore", "-q", "ROADMAP.md"])[0] == 0
    return f"wrote {target}" + ("" if ignored else " — NOT in .gitignore; add it so it is never committed")


def render(res):
    out = []
    b = res["backlog"]
    if b and b["active"]:
        a = b["active"]
        out.append(f"{a['title']}    {a['closed']}/{a['total']} closed" + (f"    (due {a['due']})" if a["due"] else ""))
        if a["closed"] == a["total"]:
            out.append("  every issue in the active milestone is closed — close it, or date the next one")
    elif b and b["active_ambiguous"]:
        out.append("No active milestone resolves: several are open and none has a due date — "
                   + ", ".join(b["open_milestones"]))
    out.append("")
    if res["lanes"] is None:
        out.append(f"LANES unavailable — {res['lanes_error']}")
    elif not res["lanes"]:
        out.append("LANES  none")
    else:
        out.append("LANES")
        for r in res["lanes"]:
            pr = f"#{r['pr']['number']} {r['pr']['state'].lower()} ci:{r['pr']['ci']}" if r["pr"] else "—"
            g = r["gate"] or {}
            gate = g.get("verdict") or ("stale" if g.get("state") == "stale" else "—")
            out.append(f"  {r['name']:<28} #{str(r['issue'] or '—'):<5} {r['branch']:<34} {pr:<24} gate:{gate:<17} {r['verdict']}")
        for r in res["lanes"]:
            if r["verdict"] != "working":
                out.append(f"  → {r['name']}: {r['action']}")
            if r["verdict"] == "merged-reapable":
                out.append(f"    reap: id={r['worktreeId']} path={r['path']} pr_head={r['pr']['headRefOid']}")
    if res["waiting"]:
        out += ["", "WAITING ON YOU"] + [f"  {w}" for w in res["waiting"]]
    if b is None:
        out += ["", f"BACKLOG unavailable — {res.get('github_error')}"]
    elif not b["open_milestones"]:
        out += ["", "No open milestones — /pod:triage schedules work, /pod:migrate sets a repo up"]
    elif b["active"]:
        rows = b["ready"] + b["blocked"]
        out += ["", "READY NEXT"]
        for i in rows[:8]:
            state = "blocked by " + ", ".join(f"#{x['number']} ({x['title']})" for x in i["blockedBy"]) if i["blockedBy"] else "ready"
            out.append(f"  #{i['number']:<5} {i['title'][:48]:<48} {state}{'' if i['criteria'] else '  (no criteria)'}")
        if len(rows) > 8:
            out.append(f"  … {len(rows) - 8} more")
        if not rows:
            out.append("  nothing ready or blocked — /pod:triage to file work, /pod:migrate to audit")
        if b["manual"]:
            out += ["", "YOUR TASKS (manual — no agent can do these)"]
            for i in b["manual"]:
                state = "blocked by " + ", ".join(f"#{x['number']}" for x in i["blockedBy"]) if i["blockedBy"] else "ready"
                out.append(f"  #{i['number']:<5} {i['title'][:48]:<48} {state}")
        if b["decorative_blocked"]:
            out += ["", f"{b['decorative_blocked']} issues carry a `blocked` label with no dependency edge; "
                    "readiness above treats them as ready."]
    for n in res["notes"]:
        out += ["", f"NOTE {n}"]
    if res.get("roadmap"):
        out += ["", f"ROADMAP {res['roadmap']}"]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--no-roadmap", action="store_true", help="do not rewrite ROADMAP.md")
    ap.add_argument("--trusted", action="append", default=[], help="extra login allowed to post gate verdicts")
    ap.add_argument("--manual-label", action="append", default=[], help="this repo's spelling of the manual label")
    ap.add_argument("--owner-label", action="append", default=[], help="this repo's spelling of needs-owner")
    args = ap.parse_args()
    res = build(args)
    print(json.dumps(res, indent=1, default=str) if args.json else render(res))
    if res["lanes"] is None and res["backlog"] is None:
        sys.exit(2)


if __name__ == "__main__":
    main()
