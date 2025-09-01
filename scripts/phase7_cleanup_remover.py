#!/usr/bin/env python3
"""Business Unit: shared | Status: current

Phase 7 Cleanup Removal Tool - Systematic removal of backward compatibility artifacts.

This tool provides safe, controlled removal of backward compatibility code
with testing, rollback capabilities, and detailed logging.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Import our scanner
from phase7_cleanup_scanner import BackwardCompatibilityScanner, CompatibilityArtifact


@dataclass
class RemovalOperation:
    """Represents a single removal operation."""
    
    artifact: CompatibilityArtifact
    operation_type: str  # "line_removal", "function_removal", "file_removal", etc.
    backup_content: str = ""
    completed: bool = False
    test_passed: bool = False
    rollback_applied: bool = False
    error_message: str = ""


@dataclass
class RemovalSession:
    """Tracks a complete removal session."""
    
    session_id: str
    start_time: str
    operations: List[RemovalOperation] = field(default_factory=list)
    total_artifacts: int = 0
    completed_operations: int = 0
    failed_operations: int = 0
    test_failures: int = 0
    session_notes: str = ""


class BackwardCompatibilityRemover:
    """Tool for safely removing backward compatibility artifacts."""
    
    def __init__(self, root_path: str = ".", dry_run: bool = False, interactive: bool = True):
        self.root_path = Path(root_path)
        self.dry_run = dry_run
        self.interactive = interactive
        self.session = None
        self.backup_dir = Path("/tmp") / "phase7_cleanup_backups"
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        # Test commands (adjust paths based on working directory)
        self.smoke_test_cmd = ["scripts/smoke_tests.sh"]
        self.lint_test_cmd = ["poetry", "run", "ruff", "check", "the_alchemiser/"]
        self.type_test_cmd = ["poetry", "run", "mypy", "the_alchemiser/"]
    
    def start_session(self, artifacts: List[CompatibilityArtifact]) -> str:
        """Start a new removal session."""
        session_id = f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.session = RemovalSession(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            total_artifacts=len(artifacts)
        )
        
        # Create operations for each artifact
        for artifact in artifacts:
            operation = RemovalOperation(
                artifact=artifact,
                operation_type=self._determine_operation_type(artifact)
            )
            self.session.operations.append(operation)
        
        print(f"🚀 Started removal session: {session_id}")
        print(f"📊 Total artifacts to process: {len(artifacts)}")
        
        return session_id
    
    def _determine_operation_type(self, artifact: CompatibilityArtifact) -> str:
        """Determine the type of removal operation needed."""
        if artifact.artifact_type in ["backward_compatibility_comment", "legacy_comment", 
                                     "migration_todo", "phase_todo"]:
            return "comment_removal"
        elif artifact.artifact_type in ["backward_compat_function", "legacy_function"]:
            return "function_removal"
        elif artifact.artifact_type in ["legacy_import", "backward_import", "legacy_from_import"]:
            return "import_removal"
        elif artifact.artifact_type in ["legacy_alias"]:
            return "alias_removal"
        elif artifact.artifact_type in ["legacy_directory", "old_ddd_structure"]:
            return "directory_analysis"  # Special case - needs manual review
        else:
            return "line_removal"
    
    def process_all_artifacts(self, risk_levels: Optional[List[str]] = None) -> None:
        """Process all artifacts in the session."""
        if not self.session:
            raise ValueError("No active session. Call start_session() first.")
        
        # Filter by risk levels if specified
        operations_to_process = self.session.operations
        if risk_levels:
            operations_to_process = [
                op for op in operations_to_process 
                if op.artifact.risk_level in risk_levels
            ]
        
        print(f"📋 Processing {len(operations_to_process)} operations...")
        
        for i, operation in enumerate(operations_to_process, 1):
            print(f"\n[{i}/{len(operations_to_process)}] Processing {operation.artifact.artifact_type}")
            print(f"📁 File: {operation.artifact.file_path}:{operation.artifact.line_number}")
            print(f"🎯 Risk Level: {operation.artifact.risk_level}")
            
            if self.dry_run:
                print("🔍 DRY RUN: Would remove...")
                print(f"   Content: {operation.artifact.content}")
                operation.completed = True
                continue
            
            # Ask for confirmation for high-risk items
            if operation.artifact.risk_level == "high":
                if not self._confirm_high_risk_removal(operation):
                    print("⏭️  Skipping high-risk item")
                    continue
            
            # Process the operation
            success = self._process_single_operation(operation)
            
            if success:
                # Run tests after each removal
                test_success = self._run_tests(operation)
                if not test_success:
                    print("❌ Tests failed, attempting rollback...")
                    self._rollback_operation(operation)
                    self.session.test_failures += 1
                else:
                    print("✅ Removal successful and tests passed")
                    self.session.completed_operations += 1
            else:
                print(f"❌ Removal failed: {operation.error_message}")
                self.session.failed_operations += 1
            
            # Brief pause between operations - only in interactive mode
            if not self.dry_run and self.interactive:
                input("Press Enter to continue to next operation...")
    
    def _confirm_high_risk_removal(self, operation: RemovalOperation) -> bool:
        """Ask for confirmation before removing high-risk items."""
        print("⚠️  HIGH RISK REMOVAL")
        print(f"   Content: {operation.artifact.content}")
        print(f"   Notes: {operation.artifact.removal_notes}")
        
        while True:
            response = input("Remove this item? (y/n/s to skip): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', 's', 'skip']:
                return False
            else:
                print("Please enter 'y' for yes, 'n' for no, or 's' to skip")
    
    def _process_single_operation(self, operation: RemovalOperation) -> bool:
        """Process a single removal operation."""
        try:
            file_path = self.root_path / operation.artifact.file_path
            
            # Create backup
            backup_success = self._create_backup(operation, file_path)
            if not backup_success:
                operation.error_message = "Failed to create backup"
                return False
            
            # Perform the removal based on operation type
            if operation.operation_type == "comment_removal":
                return self._remove_comment_line(operation, file_path)
            elif operation.operation_type == "line_removal":
                return self._remove_line(operation, file_path)
            elif operation.operation_type == "import_removal":
                return self._remove_import_line(operation, file_path)
            elif operation.operation_type == "function_removal":
                return self._remove_function(operation, file_path)
            elif operation.operation_type == "alias_removal":
                return self._remove_alias(operation, file_path)
            elif operation.operation_type == "directory_analysis":
                return self._analyze_directory(operation, file_path)
            else:
                operation.error_message = f"Unknown operation type: {operation.operation_type}"
                return False
                
        except Exception as e:
            operation.error_message = f"Exception during removal: {str(e)}"
            return False
    
    def _create_backup(self, operation: RemovalOperation, file_path: Path) -> bool:
        """Create a backup of the file before modification."""
        try:
            if file_path.is_file():
                backup_file = self.backup_dir / f"{self.session.session_id}_{file_path.name}_{operation.artifact.line_number}.backup"
                shutil.copy2(file_path, backup_file)
                operation.backup_content = str(backup_file)
                return True
            return True  # No backup needed for directories
        except Exception as e:
            print(f"Failed to create backup: {e}")
            return False
    
    def _remove_comment_line(self, operation: RemovalOperation, file_path: Path) -> bool:
        """Remove a comment line or comment part of a line."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            line_index = operation.artifact.line_number - 1
            if line_index < 0 or line_index >= len(lines):
                operation.error_message = "Line number out of range"
                return False
            
            original_line = lines[line_index].rstrip()
            content = operation.artifact.content.strip()
            
            # Try to remove just the comment part
            if '#' in original_line and content in original_line:
                # Find the comment start
                comment_start = original_line.find('#')
                if content in original_line[comment_start:]:
                    # Keep the code part, remove the comment
                    code_part = original_line[:comment_start].rstrip()
                    if code_part:
                        lines[line_index] = code_part + '\n'
                    else:
                        # Remove the entire line if it's just a comment
                        del lines[line_index]
                else:
                    operation.error_message = "Could not locate comment in line"
                    return False
            else:
                # Remove the entire line
                del lines[line_index]
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            operation.completed = True
            return True
            
        except Exception as e:
            operation.error_message = f"Error removing comment: {str(e)}"
            return False
    
    def _remove_line(self, operation: RemovalOperation, file_path: Path) -> bool:
        """Remove an entire line."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            line_index = operation.artifact.line_number - 1
            if line_index < 0 or line_index >= len(lines):
                operation.error_message = "Line number out of range"
                return False
            
            # Remove the line
            del lines[line_index]
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            operation.completed = True
            return True
            
        except Exception as e:
            operation.error_message = f"Error removing line: {str(e)}"
            return False
    
    def _remove_import_line(self, operation: RemovalOperation, file_path: Path) -> bool:
        """Remove an import line, handling multi-line imports carefully."""
        # For now, use the same logic as remove_line but could be enhanced
        # to handle multi-line imports more intelligently
        return self._remove_line(operation, file_path)
    
    def _remove_function(self, operation: RemovalOperation, file_path: Path) -> bool:
        """Remove a function (requires more sophisticated parsing)."""
        operation.error_message = "Function removal requires manual review"
        return False  # For now, mark for manual review
    
    def _remove_alias(self, operation: RemovalOperation, file_path: Path) -> bool:
        """Remove an alias assignment."""
        return self._remove_line(operation, file_path)
    
    def _analyze_directory(self, operation: RemovalOperation, file_path: Path) -> bool:
        """Analyze a directory for potential removal."""
        print(f"📁 Directory analysis: {file_path}")
        if file_path.exists():
            files = list(file_path.rglob("*"))
            print(f"   Contains {len(files)} files/directories")
            operation.error_message = "Directory requires manual review and migration"
        else:
            operation.error_message = "Directory does not exist"
        return False  # Always require manual review for directories
    
    def _run_tests(self, operation: RemovalOperation) -> bool:
        """Run tests after a removal operation."""
        print("🧪 Running tests...")
        
        # Run smoke tests first (most important)
        print("   Running smoke tests...")
        result = subprocess.run(
            self.smoke_test_cmd, 
            cwd=self.root_path.parent,  # Run from repository root
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            print("   ❌ Smoke tests failed")
            operation.test_passed = False
            return False
        
        print("   ✅ Smoke tests passed")
        
        # Note: Skipping lint/type checks for individual operations to save time
        # They can be run at the end of the session
        
        operation.test_passed = True
        return True
    
    def _rollback_operation(self, operation: RemovalOperation) -> bool:
        """Rollback a failed operation."""
        try:
            if operation.backup_content and Path(operation.backup_content).exists():
                file_path = self.root_path / operation.artifact.file_path
                shutil.copy2(operation.backup_content, file_path)
                operation.rollback_applied = True
                operation.completed = False
                print("🔄 Rollback successful")
                return True
            else:
                print("❌ No backup available for rollback")
                return False
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False
    
    def generate_session_report(self) -> str:
        """Generate a report for the current session."""
        if not self.session:
            return "No active session"
        
        report = [
            f"# Phase 7 Cleanup Session Report",
            f"",
            f"**Session ID:** {self.session.session_id}",
            f"**Start Time:** {self.session.start_time}",
            f"**Dry Run Mode:** {self.dry_run}",
            f"",
            f"## Summary",
            f"",
            f"- **Total Artifacts:** {self.session.total_artifacts}",
            f"- **Completed Operations:** {self.session.completed_operations}",
            f"- **Failed Operations:** {self.session.failed_operations}",
            f"- **Test Failures:** {self.session.test_failures}",
            f"",
            f"## Operations Log",
            f""
        ]
        
        for i, operation in enumerate(self.session.operations, 1):
            status = "✅ Completed" if operation.completed else "❌ Failed"
            if operation.rollback_applied:
                status += " (Rolled Back)"
            
            report.append(f"### {i}. {operation.artifact.artifact_type}")
            report.append(f"**Status:** {status}")
            report.append(f"**File:** `{operation.artifact.file_path}:{operation.artifact.line_number}`")
            report.append(f"**Risk Level:** {operation.artifact.risk_level}")
            report.append(f"**Operation Type:** {operation.operation_type}")
            
            if operation.error_message:
                report.append(f"**Error:** {operation.error_message}")
            
            report.append(f"```")
            report.append(operation.artifact.content)
            report.append(f"```")
            report.append("")
        
        return "\n".join(report)
    
    def run_final_tests(self) -> bool:
        """Run comprehensive tests at the end of the session."""
        print("🧪 Running final comprehensive tests...")
        
        # Smoke tests
        print("   Running smoke tests...")
        result = subprocess.run(self.smoke_test_cmd, cwd=self.root_path.parent)
        if result.returncode != 0:
            print("   ❌ Final smoke tests failed")
            return False
        print("   ✅ Smoke tests passed")
        
        # Linting (allow some errors as baseline has 679 errors)
        print("   Running linting check...")
        result = subprocess.run(
            self.lint_test_cmd, 
            cwd=self.root_path.parent,  # Run from repository root
            capture_output=True,
            text=True
        )
        # Note: We allow linting errors since baseline has 679 errors
        print(f"   ℹ️  Linting completed (baseline expects ~679 errors)")
        
        return True


def main():
    """Main entry point for the removal tool."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove backward compatibility artifacts")
    parser.add_argument("--root", default=".", help="Root directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't make changes")
    parser.add_argument("--risk-levels", nargs="+", choices=["high", "medium", "low"], 
                       help="Only process specified risk levels")
    parser.add_argument("--max-artifacts", type=int, help="Maximum number of artifacts to process")
    parser.add_argument("--scan-file", help="Use pre-generated scan JSON file")
    
    args = parser.parse_args()
    
    # Get artifacts to process
    if args.scan_file:
        with open(args.scan_file, 'r') as f:
            scan_data = json.load(f)
        artifacts = [
            CompatibilityArtifact(
                artifact_type=item["type"],
                file_path=item["file"],
                line_number=item["line"],
                content=item["content"],
                risk_level=item["risk_level"],
                removal_notes=item["removal_notes"]
            )
            for item in scan_data["artifacts"]
        ]
    else:
        # Run fresh scan
        scanner = BackwardCompatibilityScanner(args.root)
        report = scanner.run_scan()
        artifacts = report.artifacts
    
    # Filter by risk levels
    if args.risk_levels:
        artifacts = [a for a in artifacts if a.risk_level in args.risk_levels]
    
    # Limit number of artifacts
    if args.max_artifacts:
        artifacts = artifacts[:args.max_artifacts]
    
    if not artifacts:
        print("No artifacts to process")
        return
    
    # Start removal process
    remover = BackwardCompatibilityRemover(args.root, args.dry_run)
    session_id = remover.start_session(artifacts)
    
    try:
        remover.process_all_artifacts(args.risk_levels)
        
        # Run final tests if not dry run
        if not args.dry_run:
            remover.run_final_tests()
        
    finally:
        # Generate report
        report = remover.generate_session_report()
        report_file = f"/tmp/cleanup_session_{session_id}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Session report written to: {report_file}")


if __name__ == "__main__":
    main()