#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Merge reports from multiple linting tools for unified violation tracking.

Combines Ruff, MyPy, and custom typing audit results into a single 
comprehensive report for developer workflow optimization.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def run_ruff_check() -> Dict[str, Any]:
    """Run Ruff and capture JSON output."""
    try:
        result = subprocess.run(
            ["poetry", "run", "ruff", "check", "the_alchemiser/", "--output-format=json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout.strip():
            return {"tool": "ruff", "violations": json.loads(result.stdout)}
        else:
            return {"tool": "ruff", "violations": []}
            
    except Exception as e:
        print(f"Error running Ruff: {e}")
        return {"tool": "ruff", "violations": [], "error": str(e)}


def run_mypy_check() -> Dict[str, Any]:
    """Run MyPy and capture JSON output."""
    try:
        result = subprocess.run(
            ["poetry", "run", "mypy", "the_alchemiser/", "--config-file=pyproject.toml", "--show-error-codes"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # MyPy doesn't have JSON output, parse text output
        violations = []
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if ':' in line and 'error:' in line:
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        violations.append({
                            "file": parts[0],
                            "line": int(parts[1]) if parts[1].isdigit() else 0,
                            "column": int(parts[2]) if parts[2].isdigit() else 0,
                            "message": parts[3].strip()
                        })
        
        return {"tool": "mypy", "violations": violations}
        
    except Exception as e:
        print(f"Error running MyPy: {e}")
        return {"tool": "mypy", "violations": [], "error": str(e)}


def load_typing_audit() -> Dict[str, Any]:
    """Load typing audit results."""
    audit_path = Path("report/typing_violations.json")
    
    if not audit_path.exists():
        return {"tool": "typing_audit", "violations": [], "error": "Report not found"}
    
    try:
        with open(audit_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        
        return {
            "tool": "typing_audit",
            "violations": report.get("violations", []),
            "summary": report.get("summary", {})
        }
        
    except Exception as e:
        print(f"Error loading typing audit: {e}")
        return {"tool": "typing_audit", "violations": [], "error": str(e)}


def prioritize_violations(merged_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Prioritize violations by severity and impact."""
    all_violations = []
    
    for tool_report in merged_report["tools"]:
        tool_name = tool_report["tool"]
        violations = tool_report.get("violations", [])
        
        for violation in violations:
            priority_score = calculate_priority_score(violation, tool_name)
            
            unified_violation = {
                "tool": tool_name,
                "file": violation.get("file", "unknown"),
                "line": violation.get("line", 0),
                "message": violation.get("message", ""),
                "priority_score": priority_score,
                "severity": get_severity(violation, tool_name),
                "violation_type": get_violation_type(violation, tool_name),
                "raw_violation": violation
            }
            
            all_violations.append(unified_violation)
    
    # Sort by priority score (higher = more important)
    return sorted(all_violations, key=lambda x: x["priority_score"], reverse=True)


def calculate_priority_score(violation: Dict[str, Any], tool: str) -> int:
    """Calculate priority score for violation (higher = more important)."""
    score = 0
    
    # Base score by tool
    if tool == "typing_audit":
        severity = violation.get("severity", "")
        if severity == "CRITICAL":
            score += 100
        elif severity == "HIGH":
            score += 75
        elif severity == "MEDIUM":
            score += 50
        else:
            score += 25
            
        # Extra score for specific violation types
        vtype = violation.get("type", "")
        if "ANN401" in vtype:
            score += 20  # Any usage is high priority
        elif "FORBIDDEN_CROSS_MODULE_IMPORT" in vtype:
            score += 30  # Architecture violations are critical
            
    elif tool == "ruff":
        # Ruff violations are generally lower priority unless specific rules
        score += 30
        rule = violation.get("code", "")
        if rule.startswith("ANN"):
            score += 20  # Type annotation issues
        elif rule.startswith("F"):
            score += 15  # Pyflakes errors
            
    elif tool == "mypy":
        # MyPy errors are high priority
        score += 60
        message = violation.get("message", "").lower()
        if "any" in message:
            score += 15  # Any-related errors
        elif "missing" in message and "return" in message:
            score += 10  # Missing return type annotations
    
    return score


def get_severity(violation: Dict[str, Any], tool: str) -> str:
    """Get unified severity level."""
    if tool == "typing_audit":
        return violation.get("severity", "MEDIUM")
    elif tool == "mypy":
        return "HIGH"  # MyPy errors are generally high priority
    elif tool == "ruff":
        return "MEDIUM"  # Ruff violations are generally medium priority
    else:
        return "LOW"


def get_violation_type(violation: Dict[str, Any], tool: str) -> str:
    """Get unified violation type."""
    if tool == "typing_audit":
        return violation.get("type", "UNKNOWN")
    elif tool == "mypy":
        return "MYPY_ERROR"
    elif tool == "ruff":
        return f"RUFF_{violation.get('code', 'UNKNOWN')}"
    else:
        return "UNKNOWN"


def generate_merged_report(prioritized_violations: List[Dict[str, Any]]) -> None:
    """Generate merged report."""
    report_path = Path("report/merged_violations.json")
    
    # Summary statistics
    summary = {
        "total_violations": len(prioritized_violations),
        "by_tool": {},
        "by_severity": {},
        "by_file": {},
        "top_priority_files": []
    }
    
    file_counts = {}
    
    for violation in prioritized_violations:
        tool = violation["tool"]
        severity = violation["severity"]
        file_path = violation["file"]
        
        # Count by tool
        summary["by_tool"][tool] = summary["by_tool"].get(tool, 0) + 1
        
        # Count by severity
        summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        
        # Count by file
        file_counts[file_path] = file_counts.get(file_path, 0) + 1
    
    # Top files with most violations
    summary["top_priority_files"] = sorted(
        file_counts.items(), key=lambda x: x[1], reverse=True
    )[:10]
    
    # Generate report
    merged_report = {
        "summary": summary,
        "prioritized_violations": prioritized_violations[:50],  # Top 50 for readability
        "all_violations_count": len(prioritized_violations)
    }
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(merged_report, f, indent=2)
    
    print(f"📊 Merged report written to {report_path}")


def print_summary(prioritized_violations: List[Dict[str, Any]]) -> None:
    """Print summary of merged violations."""
    print("\n🔍 Merged Linting Report Summary")
    print(f"Total violations: {len(prioritized_violations)}")
    
    # Count by tool
    tool_counts = {}
    severity_counts = {}
    
    for violation in prioritized_violations:
        tool = violation["tool"]
        severity = violation["severity"]
        
        tool_counts[tool] = tool_counts.get(tool, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    print("\nBy tool:")
    for tool, count in tool_counts.items():
        print(f"  {tool}: {count}")
    
    print("\nBy severity:")
    for severity, count in sorted(severity_counts.items(), reverse=True):
        emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
        print(f"  {emoji} {severity}: {count}")
    
    # Show top priority violations
    print(f"\n🎯 Top 10 Priority Violations:")
    for i, violation in enumerate(prioritized_violations[:10]):
        file_path = Path(violation["file"]).name
        print(f"{i+1:2d}. {file_path}:{violation['line']} "
              f"[{violation['tool']}] {violation['message'][:60]}...")


def main() -> int:
    """Main entry point for merged report generation."""
    print("🔄 Running merged linting analysis...")
    
    # Collect reports from all tools
    reports = {
        "tools": [
            run_ruff_check(),
            run_mypy_check(),
            load_typing_audit()
        ]
    }
    
    # Prioritize all violations
    prioritized_violations = prioritize_violations(reports)
    
    # Generate outputs
    generate_merged_report(prioritized_violations)
    print_summary(prioritized_violations)
    
    # Return exit code based on high-priority violations
    critical_count = sum(1 for v in prioritized_violations if v["severity"] == "CRITICAL")
    high_count = sum(1 for v in prioritized_violations if v["severity"] == "HIGH")
    
    if critical_count > 0:
        print(f"\n🔴 {critical_count} CRITICAL violations found")
        return 1
    elif high_count > 0:
        print(f"\n🟠 {high_count} HIGH violations found")
        return 1
    else:
        print("\n✅ No critical or high-priority violations")
        return 0


if __name__ == "__main__":
    sys.exit(main())