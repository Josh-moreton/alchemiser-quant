#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Sync SonarQube issues into GitHub Issues.

- Pulls issues from SonarQube Web API (/api/issues/search)
- Filters by project, severity, and type
- Creates GitHub Issues with labels and optional assignee (e.g., Copilot agent)

Environment variables:
- SONAR_HOST_URL: Base URL of SonarQube server (e.g., https://sonar.mycompany.com)
- SONAR_TOKEN: Token with api access
- GITHUB_TOKEN: GitHub token with repo and issues scope (Actions provides this by default)
- GITHUB_REPOSITORY: owner/repo slug (provided by GitHub Actions)
- COPILOT_ASSIGNEE: optional GitHub username to assign (e.g., github-copilot)
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from pathlib import Path

# Optional .env support for local runs
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception as exc:
    logging.debug("dotenv not loaded: %s", exc)

SESSION = requests.Session()
SESSION.headers.update(
    {
        "Accept": "application/json",
        "User-Agent": "alchemiser-sonar-sync/1.0",
    }
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# Basic rate limit/backoff for GitHub API
GITHUB_REMAINING_HEADER = "x-ratelimit-remaining"
GITHUB_RESET_HEADER = "x-ratelimit-reset"


@dataclass(frozen=True)
class SonarIssue:
    """Minimal view of a SonarQube issue used for GitHub issue creation."""

    key: str
    rule: str
    severity: str
    type: str
    component: str
    project: str
    message: str
    effort: str | None
    debt: str | None
    author: str | None
    line: int | None
    creationDate: str
    tags: list[str]
    url: str


def getenv_required(name: str) -> str:
    """Fetch required environment variable or exit with code 2."""
    val = os.getenv(name)
    if not val:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(2)
    return val


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for Sonar→GitHub sync."""
    parser = argparse.ArgumentParser(description="Sync SonarQube issues to GitHub")
    parser.add_argument(
        "--project-key",
        default="Josh-moreton_alchemiser-quant",
        help="Sonar project key (default: Josh-moreton_alchemiser-quant)",
    )
    parser.add_argument("--severity", default="")
    parser.add_argument("--types", default="")
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--state", default="OPEN", help="SonarQube issue state filter")
    parser.add_argument("--max", type=int, default=2000, help="Max issues to fetch")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--no-labels",
        action="store_true",
        help="Do not create or attach labels to GitHub issues",
    )
    parser.add_argument(
        "--group-by",
        choices=["file", "issue"],
        default="file",
        help="Aggregate GitHub issues by file (component) or create one per Sonar issue",
    )
    return parser.parse_args()


def sonar_paginated(
    url: str, params: dict[str, str], limit: int, token: str | None = None
) -> Iterable[dict[str, object]]:
    """Yield SonarQube issues via paginated API until limit is reached."""
    page = 1
    page_size = 500
    fetched = 0
    while fetched < limit:
        p = dict(params)
        p.update({"p": str(page), "ps": str(page_size)})
        resp = (
            SESSION.get(url, params=p, auth=(token, ""))
            if token
            else SESSION.get(url, params=p)
        )
        resp.raise_for_status()
        data = resp.json()
        issues = data.get("issues", [])
        if not issues:
            break
        for it in issues:
            yield it
            fetched += 1
            if fetched >= limit:
                break
        page += 1


def map_issue(it: dict[str, object], host: str) -> SonarIssue:
    """Map raw SonarQube issue JSON to a SonarIssue dataclass."""
    component = it.get("component", "")
    project = it.get("project", "")
    key = it.get("key", "")
    line = it.get("line")
    rule = it.get("rule", "")
    url = f"{host}/project/issues?id={project}&issues={key}&open={key}"
    return SonarIssue(
        key=key,
        rule=rule,
        severity=it.get("severity", "UNKNOWN"),
        type=it.get("type", "CODE_SMELL"),
        component=component,
        project=project,
        message=it.get("message", ""),
        effort=it.get("effort"),
        debt=it.get("debt"),
        author=it.get("author"),
        line=int(line) if isinstance(line, int) else None,
        creationDate=it.get("creationDate", ""),
        tags=it.get("tags", []) or [],
        url=url,
    )


def issue_title(si: SonarIssue) -> str:
    """Build a concise GitHub issue title from Sonar issue fields."""
    comp = si.component.split(":", 1)[-1]
    loc = f":{si.line}" if si.line else ""
    return f"[{si.severity}] {si.type}: {si.message} ({comp}{loc})"


def issue_body(si: SonarIssue) -> str:
    """Build a detailed GitHub issue body with a link back to SonarQube."""
    lines = [
        "Source: SonarQube",
        f"Project: {si.project}",
        f"Rule: {si.rule}",
        f"Severity: {si.severity}",
        f"Type: {si.type}",
        f"Component: {si.component}",
        f"Line: {si.line or 'n/a'}",
        f"Created: {si.creationDate}",
        f"Tags: {', '.join(si.tags) if si.tags else 'none'}",
        "",
        f"Message: {si.message}",
        "",
        f"SonarQube Link: {si.url}",
        f"SonarQube Key: {si.key}",
    ]
    return "\n".join(lines)


def file_issue_title(component: str, issues: list[SonarIssue]) -> str:
    """Build a GitHub issue title for a file aggregating its Sonar findings."""
    rel = component.split(":", 1)[-1]
    count = len(issues)
    severities = {s.severity for s in issues}
    max_sev_order = {"BLOCKER": 5, "CRITICAL": 4, "MAJOR": 3, "MINOR": 2, "INFO": 1}
    max_sev = (
        max(severities, key=lambda s: max_sev_order.get(s, 0)) if severities else "INFO"
    )
    return f"[SonarQube] {rel} — {count} finding(s), top severity {max_sev}"


def file_issue_body(
    component: str, project: str, host: str, issues: list[SonarIssue]
) -> str:
    """Build a GitHub issue body listing all findings for a file, with links."""
    rel = component.split(":", 1)[-1]
    # Link to SonarQube filtered by component
    file_link = (
        f"{host}/project/issues?id={project}&componentKeys={component}&resolved=false"
    )
    lines: list[str] = []
    lines.append("Source: SonarQube (aggregated per file)")
    lines.append(f"Project: {project}")
    lines.append(f"SonarQube Component: {component}")  # stable marker for idempotency
    lines.append(f"File: {rel}")
    lines.append("")
    lines.append(f"All issues for this file: {file_link}")
    lines.append("")
    lines.append("Findings:")
    # Sort issues by severity desc, then type, then line
    sev_order = {"BLOCKER": 5, "CRITICAL": 4, "MAJOR": 3, "MINOR": 2, "INFO": 1}
    issues_sorted = sorted(
        issues,
        key=lambda s: (-sev_order.get(s.severity, 0), s.type, s.line or 0),
    )
    for si in issues_sorted:
        loc = f":{si.line}" if si.line else ""
        per_issue_link = (
            f"{host}/project/issues?id={si.project}&issues={si.key}&open={si.key}"
        )
        lines.append(
            f"- [{si.severity}] {si.type} {si.rule}: {si.message} ({rel}{loc}) — Key: {si.key} — {per_issue_link}"
        )
    return "\n".join(lines)


def github_request(method: str, url: str, **kwargs: object) -> requests.Response:
    """Wrap requests with auth, version headers, and rate-limit backoff."""
    token = get_github_token()
    headers_obj = kwargs.pop("headers", {})
    # Type assertion: we know this should be a mutable dict
    headers: dict[str, str] = dict(headers_obj) if isinstance(headers_obj, dict) else {}
    headers["Authorization"] = f"Bearer {token}"
    headers["Accept"] = "application/vnd.github+json"
    headers["X-GitHub-Api-Version"] = "2022-11-28"
    resp = SESSION.request(method, url, headers=headers, **kwargs)  # type: ignore[arg-type]
    if resp.status_code == 403:
        remaining = resp.headers.get(GITHUB_REMAINING_HEADER)
        reset = resp.headers.get(GITHUB_RESET_HEADER)
        if remaining == "0" and reset:
            # simple backoff until reset epoch
            try:
                reset_ts = int(reset)
                sleep_for = max(0, reset_ts - int(time.time()) + 2)
                if sleep_for > 0:
                    logging.info("Rate limited, sleeping for %d seconds", sleep_for)
                    time.sleep(sleep_for)
                    resp = SESSION.request(method, url, headers=headers, **kwargs)  # type: ignore[arg-type]
            except Exception as exc:
                logging.exception("GitHub rate limit backoff failed: %s", exc)
    resp.raise_for_status()
    return resp


def _run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a command and return (code, stdout, stderr)."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as exc:
        return 1, "", str(exc)


def get_github_token() -> str:
    """Return a GitHub token from env or gh CLI; exit with a clear message if unavailable."""
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        return token
    # Dry-run paths don't call GitHub APIs, but this function is used only when needed.
    # Try gh CLI if available.
    if shutil.which("gh"):
        code, out, _ = _run_command(["gh", "auth", "token"])
        if code == 0 and out:
            return out
        # Fallback: check status for hint
        _run_command(["gh", "auth", "status"])
    print(
        "Missing GitHub token. Set GITHUB_TOKEN or authenticate via 'gh auth login' (gh CLI).",
        file=sys.stderr,
    )
    sys.exit(2)


def get_sonar_token() -> str:
    """Return Sonar token from env, optional file, or command; exit if missing.

    Supported sources in order:
    - SONAR_TOKEN env var
    - SONAR_TOKEN_FILE env var pointing to a file with the token
    - SONAR_TOKEN_CMD env var with a shell command that prints the token
    """
    token = os.getenv("SONAR_TOKEN")
    if token:
        return token
    token_file = os.getenv("SONAR_TOKEN_FILE")
    if token_file:
        p = Path(token_file).expanduser()
        if p.exists():
            try:
                content = p.read_text(encoding="utf-8").strip()
                if content:
                    return content
            except Exception as exc:
                logging.debug("Failed reading SONAR_TOKEN_FILE: %s", exc)
    print(
        "Missing Sonar token. Set SONAR_TOKEN (or SONAR_TOKEN_FILE/SONAR_TOKEN_CMD).",
        file=sys.stderr,
    )
    sys.exit(2)


def _validate_and_return(owner: str, repo: str) -> tuple[str, str] | None:
    """Validate owner and repo names match GitHub naming rules.
    
    GitHub naming rules:
        - Alphanumeric characters, hyphens, and underscores only
        - Cannot start with hyphen
        - Max 39 characters for owner, 100 for repo
    
    Security:
        - Prevents path traversal attacks (e.g., "../../../etc/passwd")
        - Blocks query parameter injection
        - Ensures only valid GitHub identifiers are used
    
    Returns:
        Validated (owner, repo) tuple or None if invalid
    """
    # GitHub username/org pattern: alphanumeric, hyphens, cannot start with hyphen
    owner_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9-]){0,38}$"
    # GitHub repo name pattern: alphanumeric, dots, hyphens, underscores
    repo_pattern = r"^[a-zA-Z0-9._-]{1,100}$"
    
    if not re.match(owner_pattern, owner):
        logging.warning(f"Invalid GitHub owner name: {owner}")
        return None
    
    if not re.match(repo_pattern, repo):
        logging.warning(f"Invalid GitHub repo name: {repo}")
        return None
    
    return owner, repo


def get_github_repo(owner_repo_env: str | None = None) -> tuple[str, str] | None:
    """Determine owner/repo from env, gh CLI, or git remote origin.
    
    Security:
        - Uses urllib.parse for proper URL parsing
        - Validates path structure before extraction
        - Strips query parameters and fragments
        - Validates owner/repo format (alphanumeric + hyphens/underscores)
    """
    if owner_repo_env:
        try:
            owner, repo = owner_repo_env.split("/", 1)
            return _validate_and_return(owner, repo)
        except ValueError:
            pass
    # gh CLI
    if shutil.which("gh"):
        code, out, _ = _run_command(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]
        )
        if code == 0 and out and "/" in out:
            owner, repo = out.split("/", 1)
            return _validate_and_return(owner, repo)
    # git remote
    if shutil.which("git"):
        code, out, _ = _run_command(["git", "remote", "get-url", "origin"])
        if code == 0 and out:
            url = out.strip()
            
            # Handle SSH URLs: git@github.com:owner/repo.git
            if url.startswith("git@"):
                match = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", url)
                if match:
                    owner, repo = match.groups()
                    return _validate_and_return(owner, repo)
            
            # Handle HTTPS URLs: https://github.com/owner/repo.git
            elif url.startswith("http"):
                parsed = urlparse(url)
                
                # Validate domain is exactly github.com
                if parsed.netloc.lower() != "github.com":
                    return None
                
                # Extract path, strip leading/trailing slashes
                path = parsed.path.strip("/")
                
                # Remove .git suffix if present
                if path.endswith(".git"):
                    path = path[:-4]
                
                # Split into owner/repo
                parts = path.split("/")
                if len(parts) >= 2:
                    owner, repo = parts[0], parts[1]
                    return _validate_and_return(owner, repo)
    
    return None


def ensure_label(
    owner: str, repo: str, name: str, color: str, description: str = ""
) -> None:
    """Ensure a label exists in the repository; create if missing.

    Strategy: attempt to create; if it already exists, ignore 409/422.
    If we lack permission or repo is archived, log and continue without failing the run.
    """
    create_api = f"https://api.github.com/repos/{owner}/{repo}/labels"
    try:
        github_request(
            "POST",
            create_api,
            json={"name": name, "color": color, "description": description},
        )
    except requests.exceptions.HTTPError as err:
        resp = getattr(err, "response", None)
        status = getattr(resp, "status_code", None)
        # Already exists or conflict → fine
        if status in (409, 422):
            return
        # Permission or not found → warn and continue; labels are optional for issue creation
        logging.warning(
            "Label creation for '%s' skipped due to HTTP %s", name, status or "unknown"
        )
        return


def find_existing_issue(owner: str, repo: str, sonar_key: str) -> int | None:
    """Return an existing open GitHub issue number matching the Sonar key, if any."""
    from urllib.parse import quote

    # Search issues by exact Sonar key in body using GitHub search API
    q = f'repo:{owner}/{repo} in:body "SonarQube Key: {sonar_key}" state:open'
    url = f"https://api.github.com/search/issues?q={quote(q)}"
    r = github_request("GET", url)
    items = r.json().get("items", [])
    if items:
        # Type assertion for return value
        issue_num = items[0].get("number")
        return int(issue_num) if isinstance(issue_num, (int, str)) else None
    return None


def find_existing_file_issue(owner: str, repo: str, component: str) -> int | None:
    """Return an existing open GitHub issue number for the given component (file)."""
    from urllib.parse import quote

    marker = f"SonarQube Component: {component}"
    q = f'repo:{owner}/{repo} in:body "{marker}" state:open'
    url = f"https://api.github.com/search/issues?q={quote(q)}"
    r = github_request("GET", url)
    items = r.json().get("items", [])
    if items:
        # Type assertion for return value
        issue_num = items[0].get("number")
        return int(issue_num) if isinstance(issue_num, (int, str)) else None
    return None


def create_or_update_issue(
    owner: str,
    repo: str,
    si: SonarIssue,
    labels: list[str],
    assignee: str | None,
    *,
    dry_run: bool = False,
) -> None:
    """Create a GitHub issue for the given Sonar issue if one doesn't already exist."""
    title = issue_title(si)
    body = issue_body(si)
    if dry_run:
        print(f"Would create issue: {title}")
        return

    existing = find_existing_issue(owner, repo, si.key)
    if existing:
        logging.info(
            "Issue already exists for SonarQube key '%s' (GitHub issue #%d), skipping",
            si.key,
            existing,
        )
        return

    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    data = {"title": title, "body": body}
    if labels:
        data["labels"] = labels
    if assignee:
        data["assignees"] = [assignee]
    github_request("POST", url, json=data)
    logging.info("Created new issue for SonarQube key '%s': %s", si.key, title)


def create_or_update_file_issue(
    owner: str,
    repo: str,
    component: str,
    project: str,
    host: str,
    issues: list[SonarIssue],
    labels: list[str],
    assignee: str | None,
    *,
    dry_run: bool = False,
) -> None:
    """Create a GitHub issue per file (component) if one doesn't already exist."""
    title = file_issue_title(component, issues)
    body = file_issue_body(component, project, host, issues)
    if dry_run:
        print(f"Would create file issue: {title}")
        return

    existing = find_existing_file_issue(owner, repo, component)
    if existing:
        logging.info(
            "File issue already exists for component '%s' (GitHub issue #%d), skipping",
            component,
            existing,
        )
        return

    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    data: dict[str, object] = {"title": title, "body": body}
    if labels:
        data["labels"] = labels
    if assignee:
        data["assignees"] = [assignee]
    github_request("POST", url, json=data)
    logging.info("Created new file issue for component '%s': %s", component, title)


def main() -> int:
    """Entrypoint: read args/env, fetch Sonar issues, and open GitHub issues."""
    args = parse_args()
    # Defaults for this repository and SonarCloud
    gh_repo = os.getenv("GITHUB_REPOSITORY") or "Josh-moreton/alchemiser-quant"
    owner, repo = gh_repo.split("/", 1)
    sonar_org = os.getenv("SONAR_ORGANIZATION") or "josh-moreton"
    sonar_host = (os.getenv("SONAR_HOST_URL") or "https://sonarcloud.io").rstrip("/")
    # Sonar token optional (public projects); will add auth only if available
    sonar_token = os.getenv("SONAR_TOKEN")
    if not sonar_token:
        token_file = os.getenv("SONAR_TOKEN_FILE")
        if token_file:
            p = Path(token_file).expanduser()
            if p.exists():
                try:
                    val = p.read_text(encoding="utf-8").strip()
                    if val:
                        sonar_token = val
                except Exception as exc:
                    logging.debug("Failed reading SONAR_TOKEN_FILE: %s", exc)

    # Labels: optionally disabled entirely
    if args.no_labels:
        all_labels: list[str] = []
    else:
        default_labels = ["sonarqube"]
        all_labels = list(dict.fromkeys(default_labels + (args.label or [])))
        label_palette = {
            "sonarqube": ("0e8a16", "Imported from SonarQube"),
            "bug": ("d73a4a", "Bug"),
            "tech-debt": ("9e6a03", "Technical debt from static analysis"),
            "automated": ("1f88d1", "Created by automation pipeline"),
        }
        if not args.dry_run:
            for lab in all_labels:
                color, desc = label_palette.get(lab, ("ededed", ""))
                ensure_label(owner, repo, lab, color, desc)

    params: dict[str, str] = {"componentKeys": args.project_key, "statuses": args.state}
    if sonar_org:
        params["organization"] = sonar_org
    if args.severity:
        params["severities"] = args.severity
    if args.types:
        params["types"] = args.types

    url = f"{sonar_host}/api/issues/search"
    count = 0
    assignee = os.getenv("COPILOT_ASSIGNEE") or None

    if args.group_by == "issue":
        for raw in sonar_paginated(url, params, args.max, token=sonar_token):
            si = map_issue(raw, sonar_host)
            labels = list(all_labels)
            if labels:
                # Map Sonar type/severity to GitHub labels
                labels.append("bug" if si.type == "BUG" else "tech-debt")
                labels = list(dict.fromkeys(labels))
            create_or_update_issue(
                owner, repo, si, labels, assignee, dry_run=args.dry_run
            )
            count += 1
    else:
        # Group by file/component and create 1 issue per file
        by_component: dict[str, list[SonarIssue]] = {}
        for raw in sonar_paginated(url, params, args.max, token=sonar_token):
            si = map_issue(raw, sonar_host)
            by_component.setdefault(si.component, []).append(si)
        for component, group in by_component.items():
            labels = list(all_labels)
            if labels:
                if any(si.type == "BUG" for si in group):
                    labels.append("bug")
                else:
                    labels.append("tech-debt")
                labels = list(dict.fromkeys(labels))
            create_or_update_file_issue(
                owner,
                repo,
                component,
                project=group[0].project if group else args.project_key,
                host=sonar_host,
                issues=group,
                labels=labels,
                assignee=assignee,
                dry_run=args.dry_run,
            )
            count += 1

    print(f"Processed {count} SonarQube issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
