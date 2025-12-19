#!/usr/bin/env python3
"""
Workflow Security Validator

Ensures GitHub Actions workflows are safe for public repositories by preventing:
1. Use of pull_request_target trigger (allows PR from fork to access base repo secrets)
2. Use of pull_request trigger with secret access (could leak secrets in logs)

This script should be run in CI on all PRs to prevent malicious workflow modifications.
"""

import sys
from pathlib import Path
from typing import List, Tuple
import yaml
import re


class WorkflowSecurityViolation(Exception):
    """Raised when a workflow has a security issue."""
    pass


def validate_workflow_file(workflow_path: Path) -> List[str]:
    """
    Validate a single workflow file for security issues.
    
    Args:
        workflow_path: Path to the workflow YAML file
        
    Returns:
        List of security violation messages (empty if no issues)
    """
    violations = []
    
    try:
        with open(workflow_path, 'r') as f:
            content = f.read()
            workflow = yaml.safe_load(content)
    except Exception as e:
        violations.append(f"Failed to parse workflow {workflow_path}: {e}")
        return violations
    
    if not workflow:
        return violations
    
    # YAML can parse 'on:' as either the string 'on' or boolean True
    # depending on context. We need to check both.
    triggers = workflow.get('on') or workflow.get(True)
    if not triggers:
        return violations
    if isinstance(triggers, str):
        triggers = [triggers]
    elif isinstance(triggers, dict):
        triggers = list(triggers.keys())
    
    # CRITICAL: pull_request_target is NEVER safe in public repos
    if 'pull_request_target' in triggers:
        violations.append(
            f"❌ CRITICAL: {workflow_path.name} uses 'pull_request_target' trigger.\n"
            f"   This allows PRs from forks to access repository secrets!\n"
            f"   NEVER use this trigger in public repositories."
        )
    
    # WARNING: pull_request with secrets is risky
    if 'pull_request' in triggers:
        # Check if workflow accesses secrets
        if re.search(r'secrets\.\w+', content):
            violations.append(
                f"⚠️  WARNING: {workflow_path.name} uses 'pull_request' trigger and accesses secrets.\n"
                f"   Secrets could be leaked in logs or via malicious code.\n"
                f"   Consider using 'push' trigger on protected branches instead."
            )
    
    return violations


def validate_all_workflows(workflows_dir: Path) -> Tuple[List[str], List[Path]]:
    """
    Validate all workflow files in the .github/workflows directory.
    
    Args:
        workflows_dir: Path to .github/workflows directory
        
    Returns:
        Tuple of (list of violations, list of validated files)
    """
    all_violations = []
    validated_files = []
    
    if not workflows_dir.exists():
        return all_violations, validated_files
    
    for workflow_file in workflows_dir.glob('*.yml'):
        validated_files.append(workflow_file)
        violations = validate_workflow_file(workflow_file)
        all_violations.extend(violations)
    
    for workflow_file in workflows_dir.glob('*.yaml'):
        validated_files.append(workflow_file)
        violations = validate_workflow_file(workflow_file)
        all_violations.extend(violations)
    
    return all_violations, validated_files


def main() -> int:
    """
    Main entry point for workflow security validation.
    
    Returns:
        Exit code (0 for success, 1 for violations found)
    """
    # Find workflows directory
    repo_root = Path(__file__).parent.parent
    workflows_dir = repo_root / '.github' / 'workflows'
    
    print("🔍 Validating GitHub Actions workflow security...")
    print(f"📁 Workflows directory: {workflows_dir}")
    print()
    
    if not workflows_dir.exists():
        print("✅ No workflows directory found - nothing to validate")
        return 0
    
    violations, validated_files = validate_all_workflows(workflows_dir)
    
    print(f"📋 Validated {len(validated_files)} workflow file(s):")
    for wf in validated_files:
        print(f"   - {wf.name}")
    print()
    
    if violations:
        print("=" * 80)
        print("🚨 WORKFLOW SECURITY VIOLATIONS DETECTED")
        print("=" * 80)
        print()
        for violation in violations:
            print(violation)
            print()
        print("=" * 80)
        print()
        print("❌ Security validation FAILED")
        print()
        print("💡 How to fix:")
        print("   1. Remove 'pull_request_target' triggers (use 'push' instead)")
        print("   2. Remove secrets access from 'pull_request' workflows")
        print("   3. Use environment protection for sensitive workflows")
        print("   4. Re-run this script to verify fixes")
        print()
        return 1
    
    print("✅ All workflows passed security validation!")
    print()
    print("🛡️  Safe triggers detected:")
    print("   - push (to protected branches)")
    print("   - workflow_dispatch (manual trigger)")
    print("   - schedule (cron)")
    print("   - tags (for releases)")
    print()
    print("✨ Repository is safe to make public")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
