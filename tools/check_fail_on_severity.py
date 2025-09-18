#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

CI enforcement tool for typing architecture violations.

Checks audit results against severity thresholds and fails CI for 
HIGH/CRITICAL violations to enforce typing architecture standards.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List


def load_violations_report(report_path: Path) -> Dict[str, any]:
    """Load violations report from JSON file."""
    if not report_path.exists():
        print(f"❌ Report file not found: {report_path}")
        return {}
    
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_severity_thresholds(report: Dict[str, any]) -> bool:
    """Check if violations exceed severity thresholds for CI failure."""
    summary = report.get("summary", {})
    violations_by_severity = summary.get("violations_by_severity", {})
    
    critical_count = violations_by_severity.get("CRITICAL", 0)
    high_count = violations_by_severity.get("HIGH", 0)
    medium_count = violations_by_severity.get("MEDIUM", 0)
    
    # Fail CI for CRITICAL or HIGH violations
    if critical_count > 0:
        print(f"🔴 CRITICAL violations found: {critical_count}")
        print("CI enforcement: CRITICAL violations must be fixed before merge")
        return False
        
    if high_count > 0:
        print(f"🟠 HIGH violations found: {high_count}")
        print("CI enforcement: HIGH violations must be fixed before merge")
        return False
    
    if medium_count > 0:
        print(f"🟡 MEDIUM violations found: {medium_count}")
        print("CI enforcement: MEDIUM violations allowed but should be addressed")
    
    print("✅ No blocking violations found")
    return True


def print_summary_stats(report: Dict[str, any]) -> None:
    """Print summary statistics."""
    summary = report.get("summary", {})
    
    print("\n📊 Typing Architecture Audit Summary")
    print(f"Files analyzed: {summary.get('files_analyzed', 0)}")
    print(f"Lines analyzed: {summary.get('lines_analyzed', 0):,}")
    print(f"Total violations: {summary.get('total_violations', 0)}")
    
    violations_by_type = summary.get("violations_by_type", {})
    if violations_by_type:
        print("\nViolations by type:")
        for vtype, count in sorted(violations_by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"  {vtype}: {count}")


def print_high_priority_violations(report: Dict[str, any], limit: int = 10) -> None:
    """Print details of high-priority violations."""
    violations = report.get("violations", [])
    
    high_priority = [v for v in violations if v.get("severity") in ["CRITICAL", "HIGH"]]
    
    if not high_priority:
        return
        
    print(f"\n🎯 High Priority Violations (showing first {limit}):")
    
    for i, violation in enumerate(high_priority[:limit]):
        file_path = Path(violation["file"]).relative_to(Path.cwd())
        print(f"\n{i+1}. {file_path}:{violation['line']}")
        print(f"   Type: {violation['type']}")
        print(f"   Severity: {violation['severity']}")
        print(f"   Message: {violation['message']}")
        print(f"   Fix: {violation['suggested_fix']}")


def main() -> int:
    """Main entry point for CI enforcement."""
    report_path = Path("report/typing_violations.json")
    
    if not report_path.exists():
        print("❌ No violations report found. Run typing audit first.")
        return 1
    
    report = load_violations_report(report_path)
    if not report:
        return 1
    
    print_summary_stats(report)
    print_high_priority_violations(report)
    
    # Check if CI should pass or fail
    if check_severity_thresholds(report):
        return 0
    else:
        print("\n💥 CI enforcement failed: Fix HIGH/CRITICAL violations before merge")
        return 1


if __name__ == "__main__":
    sys.exit(main())