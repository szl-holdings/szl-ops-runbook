#!/usr/bin/env python3
"""Weekday unblocker board — stalled PRs and reviews across szl-holdings, ranked fixes first.

Reads live state through the `gh` CLI (no token handling here), classifies every open
pull request by what is actually blocking it, maps each blocker to a runbook entry, and
writes a Markdown board plus a JSON receipt. Nothing is mutated.

Usage:
  python tools/unblocker.py                 # board to stdout, files under board/
  python tools/unblocker.py --org szl-holdings --out board

Blocker classes (in priority order; a PR can carry several):
  CONFLICTING      mergeable=CONFLICTING                        -> pr-conflicting
  BEHIND           mergeStateStatus=BEHIND                      -> pr-behind-main
  DRAFT_GATE       draft + 'Exact-head organization provenance' -> pr-exact-head-provenance
  PROVENANCE_BODY  'szl/provenance' failing                      -> pr-provenance-headings
  CP_EFFECT        'Static control-plane effect boundary'        -> pr-control-plane-effect
  HF_PARITY        a11oy parity / single-writer / killinchu sync -> a11oy-parity-single-writer
  SECURITY_GATE    Security Gate / Dependency Vulnerability Scan -> security-gate-platform
  TESTS_RED        any other failing check                        -> red-workflows-scan
  CHECKS_PENDING   checks still running                         -> wait for evidence
  CHECKS_UNKNOWN   absent or unrecognized check evidence         -> inspect coverage
  REVIEW_WAIT      outstanding review request or review required -> ask reviewer
  CHANGES_REQUESTED reviewer requested changes                   -> address review
  HOLD             title carries HOLD / Stephen decides          -> skip, listed separately
  READY            observed checks pass, CLEAN, no known blocker -> owner review, not merge authority
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

FAIL = {"FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE", "ERROR"}
CHECK_MAP = [
    ("szl/provenance", "PROVENANCE_BODY", "pr-provenance-headings", "Add the seven policy headings to the PR body (template in templates/pr-body.md)."),
    ("Exact-head organization provenance", "DRAFT_GATE", "pr-exact-head-provenance", "Mark ready for review and update the branch so behind_by is 0."),
    ("Static control-plane effect boundary", "CP_EFFECT", "pr-control-plane-effect", "Split or pin the effectful workflow change; extend the effect policy only with a receipt."),
    ("Shared source files in sync with killinchu", "HF_PARITY", "a11oy-parity-single-writer", "Re-copy shared modules from the owner and update the branch."),
    ("single-writer guard", "HF_PARITY", "a11oy-parity-single-writer", "Update the branch; canonical sync owns HF writes."),
    ("Protected base matches immutable HF repository", "HF_PARITY", "a11oy-parity-single-writer", "Update the branch to the live main head."),
    ("Security Gate", "SECURITY_GATE", "security-gate-platform", "Clear HIGH CVEs with root pnpm overrides."),
    ("Dependency Vulnerability Scan", "SECURITY_GATE", "security-gate-platform", "Clear HIGH CVEs with root pnpm overrides."),
    ("Exact taxonomy, front doors, and publication set", "FRONT_DOOR", "org-profile-validators", "Restore the required profile blocks (router, HISTORICAL contract, truth markers)."),
    ("router-flagship/validate", "FRONT_DOOR", "org-profile-validators", "Restore the inference-flagship block in profile/README.md."),
    ("trivy", "SECURITY_GATE", "security-gate-platform", "Read the trivy table; pin or bump the flagged image/package."),
    ("Lint commit messages", "TESTS_RED", "pr-conflicting", "Squash to one conventional commit when merging; rebase if the branch is stale."),
    ("Run tests", "TESTS_RED", "red-workflows-scan", "Open the failing step log and fix the test, or state why it is expected."),
    ("test (", "TESTS_RED", "red-workflows-scan", "Open the failing step log; conflicting PRs often fail tests only because of the stale base."),
    ("observe (", "TESTS_RED", "red-workflows-scan", "Observation lane failed; check the prerequisite it probes."),
]
PRIORITY = {"READY": 0, "BEHIND": 1, "DRAFT_GATE": 2, "PROVENANCE_BODY": 3, "FRONT_DOOR": 3, "CONFLICTING": 4, "HF_PARITY": 5, "SECURITY_GATE": 6, "CP_EFFECT": 7, "TESTS_RED": 8, "CHECKS_PENDING": 8, "CHECKS_UNKNOWN": 8, "MERGE_STATE_UNKNOWN": 8, "CHANGES_REQUESTED": 9, "REVIEW_WAIT": 9, "HOLD": 99}


def gh(*args: str) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:3])} failed: {r.stderr.strip()[:300]}")
    return r.stdout


def collect(org: str) -> list[dict]:
    prs = json.loads(gh("search", "prs", "--owner", org, "--state", "open", "--limit", "200", "--json", "number,title,repository,author,createdAt,updatedAt,isDraft,url"))
    out = []
    for p in prs:
        repo = p["repository"]["nameWithOwner"]
        d = json.loads(gh("pr", "view", str(p["number"]), "--repo", repo, "--json", "number,title,isDraft,mergeable,mergeStateStatus,reviewDecision,reviewRequests,statusCheckRollup,headRefName,baseRefName,additions,deletions,changedFiles,createdAt,updatedAt,url,body,author"))
        d["repo"] = repo
        out.append(d)
    return out


def classify(pr: dict, now: dt.datetime) -> dict:
    raw_checks = pr.get("statusCheckRollup")
    checks = raw_checks if isinstance(raw_checks, list) else []
    failing = []
    pending = 0
    unknown = int(not checks)
    successful = 0
    for c in checks:
        if not isinstance(c, dict):
            unknown += 1
            continue
        name = c.get("name") or c.get("context") or ""
        status = c.get("status") or ""
        concl = c.get("conclusion") or c.get("state") or ""
        if not isinstance(name, str) or not isinstance(status, str) or not isinstance(concl, str):
            unknown += 1
            continue
        status, concl = status.upper(), concl.upper()
        if concl in FAIL:
            failing.append(name)
        if status in {"IN_PROGRESS", "QUEUED", "PENDING", "WAITING", "REQUESTED", "PENDING_DEPLOYMENT"} or concl == "PENDING":
            pending += 1
        elif status not in {"", "COMPLETED"} or concl not in FAIL | {"SUCCESS", "NEUTRAL", "SKIPPED"} or not name:
            unknown += 1
        elif concl == "SUCCESS":
            successful += 1
    failing = sorted(set(failing))
    blockers: list[dict] = []
    seen = set()

    def add(cls, entry, fix, detail=""):
        key = (cls, entry)
        if key in seen:
            return
        seen.add(key)
        blockers.append({"class": cls, "entry": entry, "fix": fix, "detail": detail})

    hold = bool(__import__("re").search(r"\bHOLD\b|Stephen decides", pr["title"], __import__("re").I))
    if hold:
        add("HOLD", "", "Owner decision pending; not a mechanical blocker.")
    if pr["mergeable"] == "CONFLICTING":
        add("CONFLICTING", "pr-conflicting", "Rebase onto main and resolve, or close as net-zero with a receipt comment.")
    if pr["mergeStateStatus"] == "BEHIND":
        add("BEHIND", "pr-behind-main", "gh pr update-branch --rebase, then re-check provenance.")
    for name in failing:
        matched = False
        for needle, cls, entry, fix in CHECK_MAP:
            if needle.lower() in name.lower():
                add(cls, entry, fix, name)
                matched = True
                break
        if not matched:
            add("TESTS_RED", "red-workflows-scan", "Open the failing step log.", name)
    if pr["isDraft"] and not hold:
        add("DRAFT_GATE", "pr-exact-head-provenance", "Draft PRs fail the exact-head provenance gate by design; mark ready when it should merge.")
    body = pr.get("body") or ""
    missing_headings = [h for h in ("Origin", "Rights", "Agents and tools", "Tests", "Security", "Rollback", "Known limits") if not __import__("re").search(r"(?m)^##\s+" + __import__("re").escape(h) + r"\s*$", body)]
    # The szl/provenance check only runs where the solo-provenance workflow exists (the .github repo) or where the
    # rollup carries it. Elsewhere, missing headings are advisory and must not be reported as a blocker.
    provenance_enforced = pr["repo"].endswith("/.github") or any(isinstance(c, dict) and (c.get("name") or c.get("context") or "") == "szl/provenance" for c in checks)
    if missing_headings and provenance_enforced and not any(b["class"] == "PROVENANCE_BODY" for b in blockers):
        add("PROVENANCE_BODY", "pr-provenance-headings", f"PR body missing headings: {', '.join(missing_headings)}.")
    updated = dt.datetime.fromisoformat(pr["updatedAt"].replace("Z", "+00:00"))
    stale_days = (now - updated).days
    if pr.get("reviewDecision") == "CHANGES_REQUESTED":
        add("CHANGES_REQUESTED", "", "Address the requested changes and obtain a new review.")
    elif pr.get("reviewDecision") == "REVIEW_REQUIRED" or pr.get("reviewRequests"):
        add("REVIEW_WAIT", "", "Required or requested review remains outstanding.")
    elif pr.get("reviewDecision") not in {None, "", "APPROVED"}:
        add("REVIEW_WAIT", "", "Review decision is unknown; inspect the current review evidence.")
    if pending:
        add("CHECKS_PENDING", "red-workflows-scan", f"{pending} check(s) still running; re-check later.")
    if unknown or (not successful and not failing and not pending):
        add("CHECKS_UNKNOWN", "red-workflows-scan", "Check evidence is absent, unrecognized, or has no successful result; inspect coverage.")
    if pr["mergeable"] not in {"MERGEABLE", "CONFLICTING"} or pr["mergeStateStatus"] not in {"CLEAN", "BEHIND"}:
        add("MERGE_STATE_UNKNOWN", "", "Merge state is not confirmed clean; inspect the current GitHub blockers.")
    if not blockers and pr["mergeable"] == "MERGEABLE" and pr["mergeStateStatus"] == "CLEAN" and not pr["isDraft"]:
        add("READY", "pr-merge-conveyor", "Observed checks pass; verify required reviews, current head and owner merge authorization.")
    rank = min(PRIORITY.get(b["class"], 50) for b in blockers) if blockers else 50
    return {
        "repo": pr["repo"].split("/")[1], "number": pr["number"], "title": pr["title"], "url": pr["url"], "draft": pr["isDraft"],
        "mergeable": pr["mergeable"], "state": pr["mergeStateStatus"], "failing": failing, "pending": pending,
        "stale_days": stale_days, "size": f"+{pr['additions']}/-{pr['deletions']} · {pr['changedFiles']} files",
        "blockers": blockers, "rank": rank, "hold": hold,
    }


def board(rows: list[dict], org: str, now: dt.datetime, red_main: list[dict] | None = None, issues: dict | None = None, security: dict | None = None) -> str:
    rows = sorted(rows, key=lambda r: (r["rank"], -r["stale_days"], r["repo"], r["number"]))
    date = now.astimezone(dt.timezone(dt.timedelta(hours=-4))).strftime("%A %Y-%m-%d %H:%M ET")
    counts = Counter(b["class"] for r in rows for b in r["blockers"])
    top: list[str] = []
    # Top fixes: aggregate by (class, entry) with the PRs they unblock
    agg: dict[tuple, dict] = {}
    for r in rows:
        for b in r["blockers"]:
            if b["class"] in {"HOLD", "READY"}:
                continue
            slot = agg.setdefault((b["class"], b["entry"]), {"fix": b["fix"], "prs": []})
            tag = f"{r['repo']}#{r['number']}"
            if tag not in slot["prs"]:
                slot["prs"].append(tag)
    for (cls, entry), slot in sorted(agg.items(), key=lambda kv: (-len(kv[1]["prs"]), PRIORITY.get(kv[0][0], 50)))[:6]:
        ref = f" → runbook `{entry}`" if entry else ""
        top.append(f"- **{cls}** unblocks {len(slot['prs'])} PR(s): {slot['fix']}{ref}  \n  {', '.join(slot['prs'])}")
    ready = [r for r in rows if any(b["class"] == "READY" for b in r["blockers"])]
    holds = [r for r in rows if r["hold"]]
    lines = [f"# Unblocker board — {org} — {date}", "",
             f"{len(rows)} open PRs · {len(ready)} ready for owner review · {len(holds)} on HOLD · blockers: " + ", ".join(f"{k} {v}" for k, v in counts.most_common()), "",
             "Observed checks are a snapshot, not proof of complete required-check coverage or permission to merge.", "",
             "## Top fixes before you start coding", *(top or ["- No classified mechanical blockers; inspect the snapshot and owner decisions before action."]), ""]
    if ready:
        lines += ["## Checks passed — ready for owner review", *(f"- [{r['repo']}#{r['number']}]({r['url']}) {r['title']} · {r['size']}" for r in ready), ""]
    lines += ["## Every open PR, ranked by the cheapest unblock", "", "| PR | state | blocker → fix | runbook | stale |", "|---|---|---|---|---|"]
    for r in rows:
        bl = "; ".join(f"{b['class']}" + (f" ({b['detail']})" if b['detail'] and b['class'] in {'TESTS_RED','CP_EFFECT','HF_PARITY','SECURITY_GATE','FRONT_DOOR','PROVENANCE_BODY'} else "") for b in r["blockers"]) or "—"
        entries = ", ".join(sorted({f"`{b['entry']}`" for b in r["blockers"] if b["entry"]})) or "—"
        flags = ("DRAFT " if r["draft"] else "") + f"{r['mergeable']}/{r['state']}"
        lines.append(f"| [{r['repo']}#{r['number']}]({r['url']}) {r['title'][:70]} | {flags} | {bl} | {entries} | {r['stale_days']}d |")
    if red_main:
        lines += ["", "## Red on main (latest run per workflow)", *(f"- {x['repo']} · {x['workflow']} · {x['conclusion']} · [{x['when']}]({x['url']})" for x in red_main[:20])]
    if issues and "error" not in issues:
        lines += ["", f"## Open issues — {issues['total']} (ledger, not noise)",
                  "- by repo: " + ", ".join(f"{k} {v}" for k, v in issues["by_repo"]),
                  "- by class: " + ", ".join(f"{k} {v}" for k, v in issues["by_class"]),
                  "- by label: " + ", ".join(f"{k} {v}" for k, v in issues["by_label"]),
                  f"- `estate:p0`: {issues['p0']} · `estate:code-actionable`: {len(issues['actionable'])}"]
        if issues["actionable"]:
            lines += ["", "Code-actionable now:", *(f"- [{r}#{n}]({u}) {t}" for r, n, t, u in issues["actionable"])]
    if security:
        dep = security.get("dependabot", {}); sec = security.get("secret_scanning", {})
        lines += ["", "## Security posture (org)",
                  f"- Dependabot alerts open: {dep.get('open', dep.get('error', '?'))}" + (f" · severity {dict(dep.get('severity', []))}" if dep.get('severity') else ""),
                  f"- Secret-scanning alerts open: {sec.get('open', sec.get('error', '?'))}" + (f" · {dict(sec.get('by_repo', []))}" if sec.get('by_repo') else ""),
                  "- Managed security configuration 252588 (secret scanning, push protection, Dependabot alerts + security updates, private vuln reporting) is enforced on every repository; code-scanning backlog is tracked in runbook `codeql-scorecard-backlog`."]
    lines += ["", "_Read-only snapshot. Nothing was merged, edited, or re-run by this board._"]
    return "\n".join(lines) + "\n"


def issues_summary(org: str) -> dict:
    """Open-issue ledger by repo, label, and class. Read-only; nothing is closed."""
    import re as _re
    try:
        items = json.loads(gh("search", "issues", "--owner", org, "--state", "open", "--limit", "1000", "--json", "number,title,repository,labels,url,createdAt"))
    except RuntimeError as e:
        return {"error": str(e)}
    def cls(t: str) -> str:
        t = t.lower()
        for k, pat in [("frontier-eval", r"frontier|\[eval"), ("hf-drift", r"drift|parity|hugging|hf[- ]"), ("estate", r"estate|census|reconcil|inventory|closeout"), ("owner-queue", r"owner|founder|stephen|decision|\bhold\b"), ("security", r"security|codeql|cve|secret|vuln|protect"), ("incident", r"incident|outage|530|404|down|degraded"), ("ci", r"ci |digest|workflow")]:
            if _re.search(pat, t):
                return k
        return "other"
    by_repo = Counter(i["repository"]["nameWithOwner"].split("/")[1] for i in items)
    by_label = Counter(l["name"] for i in items for l in i["labels"])
    by_class = Counter(cls(i["title"]) for i in items)
    p0 = [i for i in items if any(l["name"] == "estate:p0" for l in i["labels"])]
    actionable = [i for i in items if any(l["name"] == "estate:code-actionable" for l in i["labels"])]
    return {"total": len(items), "by_repo": by_repo.most_common(12), "by_label": by_label.most_common(8), "by_class": by_class.most_common(), "p0": len(p0), "actionable": [(i["repository"]["nameWithOwner"].split("/")[1], i["number"], i["title"][:80], i["url"]) for i in actionable]}


def security_summary(org: str) -> dict:
    out: dict = {}
    for key, path in (("dependabot", f"orgs/{org}/dependabot/alerts?state=open&per_page=100"), ("secret_scanning", f"orgs/{org}/secret-scanning/alerts?state=open&per_page=100")):
        try:
            items = json.loads(gh("api", "--paginate", "--slurp", path))
            flat = [x for pg in items for x in (pg if isinstance(pg, list) else [])]
            out[key] = {"open": len(flat), "by_repo": Counter(x["repository"]["name"] for x in flat).most_common(6)}
            if key == "dependabot":
                out[key]["severity"] = Counter((x.get("security_advisory") or {}).get("severity") for x in flat).most_common()
        except RuntimeError as e:
            out[key] = {"error": str(e)[:120]}
    return out


def red_on_main(org: str, repos: list[str]) -> list[dict]:
    out = []
    for name in repos:
        try:
            runs = json.loads(gh("run", "list", "--repo", f"{org}/{name}", "--branch", "main", "--limit", "30", "--json", "workflowName,conclusion,createdAt,url"))
        except RuntimeError:
            continue
        seen = set()
        for r in runs:
            if r["workflowName"] in seen:
                continue
            seen.add(r["workflowName"])
            if r["conclusion"] in {"failure", "timed_out", "startup_failure", "action_required"}:
                out.append({"repo": name, "workflow": r["workflowName"], "conclusion": r["conclusion"], "when": r["createdAt"][:10], "url": r["url"]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--org", default="szl-holdings")
    ap.add_argument("--out", default="board")
    ap.add_argument("--red-main", action="store_true", help="also scan latest default-branch workflow runs for the repos that have open PRs")
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    prs = collect(a.org)
    rows = [classify(p, now) for p in prs]
    red = red_on_main(a.org, sorted({r["repo"] for r in rows})) if a.red_main else None
    issues = issues_summary(a.org) if a.red_main else None
    security = security_summary(a.org) if a.red_main else None
    md = board(rows, a.org, now, red, issues, security)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y-%m-%d")
    (out / f"board-{stamp}.md").write_text(md)
    (out / "latest.md").write_text(md)
    (out / f"board-{stamp}.json").write_text(json.dumps({"schema": "szl.unblocker-board/v1", "observed": now.isoformat(), "org": a.org, "prs": rows, "red_main": red, "issues": issues, "security": security}, indent=1))
    sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
