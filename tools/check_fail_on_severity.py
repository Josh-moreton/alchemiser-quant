#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

CI Severity Checker for Typing Architecture Audit.

This script checks the audit report and fails the CI build if there are
HIGH or CRITICAL severity violations that exceed the allowed thresholds.

Used in GitHub Actions workflow to enforce typing architecture rules.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    """Main entry point for severity checking."""
    if len(sys.argv) < 2:
        print("Usage: python check_fail_on_severity.py <report_json_path>")
        sys.exit(1)
        
    report_path = Path(sys.argv[1])
    if not report_path.exists():
        print(f"Report file not found: {report_path}")
        sys.exit(1)
        
    with open(report_path) as f:
        report = json.load(f)
        
    summary = report["summary"]["by_severity"]
    
    critical_count = summary.get("CRITICAL", 0)
    high_count = summary.get("HIGH", 0)
    
    # Define thresholds (can be adjusted over time as we fix violations)
    max_critical = 0  # No critical violations allowed
    max_high = 10     # Allow up to 10 high violations for now
    
    print(f"Typing Architecture Audit Results:")
    print(f"  CRITICAL: {critical_count} (max allowed: {max_critical})")
    print(f"  HIGH: {high_count} (max allowed: {max_high})")
    
    if critical_count > max_critical:
        print(f"❌ CRITICAL violations exceed threshold: {critical_count} > {max_critical}")
        print("Please fix critical typing violations before merging.")
        sys.exit(1)
        
    if high_count > max_high:
        print(f"❌ HIGH violations exceed threshold: {high_count} > {max_high}")
        print("Please fix high-priority typing violations before merging.")
        sys.exit(1)
        
    print("✅ Typing architecture audit passed!")
    
    # Show progress toward zero violations
    total_violations = report["summary"]["total_violations"]
    if total_violations > 0:
        print(f"📋 Total violations remaining: {total_violations}")
        print("Continue working toward zero typing violations!")


if __name__ == "__main__":
    main()