#!/usr/bin/env python3
"""
Create file review issues using GitHub REST API.

This script bypasses the limitation of gh CLI which cannot pre-fill
YAML issue template form fields. Instead, it creates issues directly
via the REST API with all metadata in the issue body.

Usage:
    python scripts/create_file_reviews.py [--dry-run] [--batch-size N]
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configuration
REPO_OWNER = "Josh-moreton"
REPO_NAME = "alchemiser-quant"
BASE_DIR = Path(__file__).parent.parent
THE_ALCHEMISER_DIR = BASE_DIR / "the_alchemiser"


def get_git_info() -> tuple[str, str]:
    """Get current commit SHA and reviewer name from git."""
    try:
        commit_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=BASE_DIR, text=True
        ).strip()

        reviewer = subprocess.check_output(
            ["git", "config", "user.name"], cwd=BASE_DIR, text=True
        ).strip()

        return commit_sha, reviewer
    except subprocess.CalledProcessError as e:
        print(f"Error getting git info: {e}", file=sys.stderr)
        sys.exit(1)


def find_python_files() -> list[Path]:
    """Find all Python files in the_alchemiser, excluding __pycache__."""
    py_files = []
    for file_path in THE_ALCHEMISER_DIR.rglob("*.py"):
        if "__pycache__" not in str(file_path):
            py_files.append(file_path.relative_to(BASE_DIR))
    return sorted(py_files)


def get_business_function(file_path: Path) -> str:
    """Determine business function from file path."""
    path_str = str(file_path)
    if "/execution_v2/" in path_str:
        return "execution_v2"
    elif "/portfolio_v2/" in path_str:
        return "portfolio_v2"
    elif "/strategy_v2/" in path_str:
        return "strategy_v2"
    elif "/orchestration/" in path_str:
        return "orchestration"
    elif "/shared/" in path_str:
        return "shared"
    elif "/notifications_v2/" in path_str:
        return "notifications_v2"
    else:
        return "other"


def get_criticality(file_path: Path) -> str:
    """Determine criticality based on file path."""
    path_str = str(file_path)
    if "/execution_v2/" in path_str or "/portfolio_v2/" in path_str:
        return "P0 (Critical)"
    elif "/strategy_v2/" in path_str or "/orchestration/" in path_str:
        return "P1 (High)"
    else:
        return "P2 (Medium)"


def create_issue_body(
    file_path: Path,
    commit_sha: str,
    reviewer: str,
    review_date: str,
    business_function: str,
    criticality: str,
) -> str:
    """Create formatted issue body with all template fields."""

    return f"""# [File Review] Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `{file_path}`

**Commit SHA / Tag**: `{commit_sha}`

**Reviewer(s)**: {reviewer}

**Date**: {review_date}

**Business function / Module**: {business_function}

**Runtime context**: TBD (Deployment context, region(s), timeouts, concurrency)

**Criticality**: {criticality}

**Direct dependencies (imports)**:
```
TBD - List internal and external dependencies
Internal: shared.schemas, shared.brokers
External: pydantic, alpaca-py, pandas
```

**External services touched**:
```
TBD - e.g., Alpaca, S3, EventBridge, Secrets Manager, DB, Redis
```

**Interfaces (DTOs/events) produced/consumed**:
```
TBD - Names and versions of DTOs/events
Produced: SignalGenerated v1.0, RebalancePlanned v1.0
Consumed: MarketData v1.0
```

**Related docs/specs**:
- [Copilot Instructions](/.github/copilot-instructions.md)
- [Alpaca Architecture](/docs/ALPACA_ARCHITECTURE.md)
- TBD - Links to design docs, runbooks, incident playbooks

---

## 1) Scope & Objectives

- Verify the file's **single responsibility** and alignment with intended business capability.
- Ensure **correctness**, **numerical integrity**, **deterministic behaviour** where required.
- Validate **error handling**, **idempotency**, **observability**, **security**, and **compliance** controls.
- Confirm **interfaces/contracts** (DTOs/events) are accurate, versioned, and tested.
- Identify **dead code**, **complexity hotspots**, and **performance risks**.

---

## 2) Summary of Findings (use severity labels)

### Critical
TBD - List critical issues found

### High
TBD - List high severity issues found

### Medium
TBD - List medium severity issues found

### Low
TBD - List low severity issues found

### Info/Nits
TBD - List informational items and nits

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| TBD | TBD | TBD | TBD | TBD |

*Use the table above to document specific line-level findings*

---

## 4) Correctness & Contracts

### Correctness Checklist

- [ ] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
- [ ] Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
- [ ] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
- [ ] **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
- [ ] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
- [ ] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
- [ ] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
- [ ] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
- [ ] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
- [ ] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
- [ ] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
- [ ] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
- [ ] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
- [ ] **Module size**: ≤ 500 lines (soft), split if > 800
- [ ] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports

---

## 5) Additional Notes

TBD - Add any additional context, observations, or recommendations

---

**Auto-generated**: {review_date}
**Script**: `scripts/create_file_reviews.py`
"""


def create_issue_via_gh_cli(
    file_path: Path,
    commit_sha: str,
    reviewer: str,
    review_date: str,
    business_function: str,
    criticality: str,
    dry_run: bool = False,
) -> dict[str, str | int]:
    """Create a single issue using gh CLI."""
    title = f"[File Review] {file_path}"
    labels = ["file-review", "audit", business_function]
    body = create_issue_body(
        file_path, commit_sha, reviewer, review_date, business_function, criticality
    )

    if dry_run:
        print(f"DRY RUN: Would create issue for {file_path}")
        print(f"  Title: {title}")
        print(f"  Labels: {', '.join(labels)}")
        print(f"  Business function: {business_function}")
        print(f"  Criticality: {criticality}")
        return {"number": 0, "html_url": "dry-run", "title": title}

    # Create issue using gh CLI
    cmd = [
        "gh",
        "issue",
        "create",
        "--repo",
        f"{REPO_OWNER}/{REPO_NAME}",
        "--title",
        title,
        "--body",
        body,
        "--label",
        ",".join(labels),
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd=BASE_DIR
        )

        # Extract issue URL from output
        issue_url = result.stdout.strip()

        # Extract issue number from URL
        issue_number = issue_url.split("/")[-1] if issue_url else None

        print(f"✅ Created issue #{issue_number}: {file_path}")

        return {
            "number": str(issue_number) if issue_number else "",
            "html_url": issue_url if issue_url else "",
            "title": title,
            "labels": ",".join(labels),
        }

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create issue for {file_path}", file=sys.stderr)
        print(f"   Error: {e.stderr}", file=sys.stderr)
        return None


def create_master_issue(
    issues: list[dict[str, str | int]],
    commit_sha: str,
    reviewer: str,
    review_date: str,
    total_files: int,
    dry_run: bool = False,
) -> dict[str, str | int] | None:
    """Create master tracking issue."""
    # Group issues by module
    by_module: dict[str, list[dict[str, str | int]]] = {}
    for issue in issues:
        if issue:
            # Extract module from labels
            module = None
            for label in issue.get("labels", []):
                if label not in ["file-review", "audit"]:
                    module = label
                    break

            if module:
                if module not in by_module:
                    by_module[module] = []
                by_module[module].append(issue)

    # Build issue list grouped by module
    issue_list = ""
    module_order = [
        "execution_v2",
        "portfolio_v2",
        "strategy_v2",
        "orchestration",
        "shared",
        "notifications_v2",
        "other",
    ]

    for module in module_order:
        if module in by_module:
            issue_list += f"\n### {module}\n\n"
            for issue in by_module[module]:
                issue_list += f"- [ ] #{issue['number']} - `{issue['title'].replace('[File Review] ', '')}`\n"

    body = f"""# Alchemiser Quant - Comprehensive File Review Tracking

**Purpose**: Track the financial-grade, line-by-line audit of all Python files in the `the_alchemiser` codebase.

## Review Parameters

- **Commit SHA**: `{commit_sha}`
- **Review Date**: {review_date}
- **Reviewer(s)**: {reviewer}
- **Total Files**: {total_files}
- **Created Issues**: {len(issues)}

## Review Objectives

This comprehensive audit ensures:
- ✅ **Correctness** & numerical integrity (Decimal for money, tolerances for floats)
- ✅ **Security** & compliance (no secrets, input validation, least privilege)
- ✅ **Observability** & error handling (structured logs, typed errors, idempotency)
- ✅ **Performance** & complexity limits (cyclomatic ≤10, functions ≤50 lines)
- ✅ **Architecture** & contracts (DTOs versioned, event-driven boundaries)
- ✅ **Testing** & determinism (coverage ≥80%, property-based tests for math)

## Module Breakdown

### Execution (P0 - Critical)
Critical path for trade execution and broker interaction.

### Portfolio (P0 - Critical)
Critical path for position management and rebalancing.

### Strategy (P1 - High)
Signal generation and market data analysis.

### Orchestration (P1 - High)
Event-driven workflow coordination.

### Shared (P2 - Medium)
Common utilities, schemas, and services.

### Notifications (P2 - Medium)
Alerting and notification delivery.

## File Review Issues
{issue_list}

## Progress Summary

- **Not Started**: {len(issues)} files
- **In Progress**: 0 files
- **Completed**: 0 files

## Review Process

1. Each file review follows the `file-review.yml` template structure
2. Findings are categorized by severity: Critical, High, Medium, Low, Info
3. Line-by-line analysis with evidence and proposed actions
4. Checklist validation for correctness, contracts, and compliance

## Completion Criteria

- [ ] All file review issues completed
- [ ] Critical/High findings addressed or tracked
- [ ] Medium/Low findings documented
- [ ] Cross-cutting improvements identified and planned
- [ ] Final audit report generated

## Related Documentation

- [Copilot Instructions](/.github/copilot-instructions.md)
- [Alpaca Architecture](/docs/ALPACA_ARCHITECTURE.md)
- [Alpaca Compliance](/docs/ALPACA_COMPLIANCE_REPORT.md)

---

**Auto-generated on {review_date}** | **Commit**: `{commit_sha}` | **Script**: `scripts/create_file_reviews.py`
"""

    if dry_run:
        print(f"\nDRY RUN: Would create master tracking issue")
        print(f"  Title: [MASTER] Comprehensive File Review - the_alchemiser/")
        print(f"  References: {len(issues)} issues")
        return {"number": 0, "html_url": "dry-run"}

    cmd = [
        "gh",
        "issue",
        "create",
        "--repo",
        f"{REPO_OWNER}/{REPO_NAME}",
        "--title",
        "[MASTER] Comprehensive File Review - the_alchemiser/",
        "--body",
        body,
        "--label",
        "file-review,audit,tracking,epic",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd=BASE_DIR
        )

        issue_url = result.stdout.strip()
        issue_number = issue_url.split("/")[-1] if issue_url else None

        print(f"\n✅ Created master tracking issue #{issue_number}")
        print(f"   {issue_url}")

        return {"number": issue_number, "html_url": issue_url}

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create master issue", file=sys.stderr)
        print(f"   Error: {e.stderr}", file=sys.stderr)
        return None


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Create file review issues for all Python files in the_alchemiser/"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually create issues, just show what would be created",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of issues to create before pausing (default: 10)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay in seconds between issue creations (default: 0.5)",
    )
    parser.add_argument(
        "--skip-master",
        action="store_true",
        help="Skip creating the master tracking issue",
    )

    args = parser.parse_args()

    print("🔍 Creating file review issues for alchemiser-quant")
    print(f"Repository: {REPO_OWNER}/{REPO_NAME}")
    print(f"Dry run: {args.dry_run}")
    print()

    # Get git info
    commit_sha, reviewer = get_git_info()
    review_date = datetime.now().strftime("%Y-%m-%d")

    print(f"Commit SHA: {commit_sha}")
    print(f"Reviewer: {reviewer}")
    print(f"Date: {review_date}")
    print()

    # Find all Python files
    print("📁 Finding Python files...")
    py_files = find_python_files()
    print(f"Found {len(py_files)} Python files to review")
    print()

    if not args.dry_run:
        response = input(f"Create {len(py_files)} issues? (y/N): ")
        if response.lower() != "y":
            print("Aborted.")
            sys.exit(0)

    # Create individual issues
    print("📝 Creating individual file review issues...")
    print()

    created_issues = []
    for i, file_path in enumerate(py_files, 1):
        business_function = get_business_function(file_path)
        criticality = get_criticality(file_path)

        issue = create_issue_via_gh_cli(
            file_path,
            commit_sha,
            reviewer,
            review_date,
            business_function,
            criticality,
            dry_run=args.dry_run,
        )

        if issue:
            created_issues.append(issue)

        # Rate limiting
        if not args.dry_run and i % args.batch_size == 0:
            print(f"   ... Created {i}/{len(py_files)} issues, pausing briefly ...")
            time.sleep(2)
        else:
            time.sleep(args.delay)

    print()
    print(f"✅ Created {len(created_issues)} file review issues")
    print()

    # Create master tracking issue
    if not args.skip_master:
        print("📋 Creating master tracking issue...")
        master_issue = create_master_issue(
            created_issues,
            commit_sha,
            reviewer,
            review_date,
            len(py_files),
            dry_run=args.dry_run,
        )

    # Summary
    print()
    print("🎉 Done! Summary:")
    if args.dry_run:
        print(f"   - Would create {len(created_issues)} file review issues")
        if not args.skip_master:
            print(f"   - Would create 1 master tracking issue")
    else:
        print(f"   - Created {len(created_issues)} file review issues")
        if not args.skip_master and master_issue:
            print(f"   - Created 1 master tracking issue (#{master_issue['number']})")
        print()
        print(f"🔍 View all issues:")
        print(
            f"   https://github.com/{REPO_OWNER}/{REPO_NAME}/issues?q=is%3Aissue+is%3Aopen+label%3Afile-review"
        )

    # Save issue info to file
    if not args.dry_run and created_issues:
        output_file = BASE_DIR / "scripts" / "created_issues.json"
        with open(output_file, "w") as f:
            json.dump(
                {
                    "created_at": review_date,
                    "commit_sha": commit_sha,
                    "reviewer": reviewer,
                    "total_files": len(py_files),
                    "master_issue": master_issue,
                    "issues": created_issues,
                },
                f,
                indent=2,
            )
        print(f"\n📝 Issue details saved to: {output_file}")


if __name__ == "__main__":
    main()
