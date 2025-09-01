#!/usr/bin/env python3
"""Business Unit: shared | Status: current

Phase 7 Cleanup Scanner - Systematic discovery of backward compatibility artifacts.

This script scans the codebase to identify all backward compatibility code
that needs to be removed after the modular migration.
"""

from __future__ import annotations

import ast
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set


@dataclass
class CompatibilityArtifact:
    """Represents a backward compatibility artifact found in the codebase."""
    
    artifact_type: str
    file_path: str
    line_number: int
    content: str
    context: str = ""
    risk_level: str = "medium"  # low, medium, high
    removal_notes: str = ""


@dataclass
class ScanReport:
    """Complete scan report of backward compatibility artifacts."""
    
    artifacts: List[CompatibilityArtifact] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    scan_timestamp: str = ""
    
    def add_artifact(self, artifact: CompatibilityArtifact) -> None:
        """Add an artifact to the report."""
        self.artifacts.append(artifact)
        self.summary[artifact.artifact_type] = self.summary.get(artifact.artifact_type, 0) + 1


class BackwardCompatibilityScanner:
    """Scanner for identifying backward compatibility artifacts."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.report = ScanReport()
        
        # Patterns to search for
        self.comment_patterns = [
            (r"backward compatibility", "backward_compatibility_comment"),
            (r"TODO.*migration", "migration_todo"),
            (r"TODO.*remove", "removal_todo"),
            (r"Phase \d+ -", "phase_todo"),
            (r"legacy", "legacy_comment"),
            (r"deprecated", "deprecated_comment"),
            (r"for compatibility", "compatibility_comment"),
            (r"keep.*for.*compatibility", "keep_compatibility"),
        ]
        
        # Function/variable patterns
        self.code_patterns = [
            (r"def _.*backward.*compatibility", "backward_compat_function"),
            (r".*_legacy.*", "legacy_identifier"),
            (r".*_compat.*", "compat_identifier"),
            (r".*_deprecated.*", "deprecated_identifier"),
            (r"# Legacy.*alias", "legacy_alias"),
            (r"# Import.*backward compatibility", "backward_import"),
        ]
        
        # Import patterns
        self.import_patterns = [
            (r"from.*error_handling.*import", "legacy_error_import"),
            (r"import.*legacy", "legacy_import"),
            (r"from.*legacy", "legacy_from_import"),
        ]
        
        # Directories that might contain legacy code
        self.legacy_directories = [
            "legacy",
            "deprecated", 
            "compat",
            "backward_compat"
        ]
        
        # Files to exclude from scanning
        self.exclude_patterns = [
            r"\.venv/",
            r"__pycache__/",
            r"\.git/",
            r"node_modules/",
            r"\.pyc$",
            r"\.pyo$",
        ]
    
    def should_scan_file(self, file_path: Path) -> bool:
        """Check if a file should be scanned."""
        file_str = str(file_path)
        
        # Exclude certain patterns
        for pattern in self.exclude_patterns:
            if re.search(pattern, file_str):
                return False
        
        # Only scan Python files and some config files
        return file_path.suffix in [".py", ".md", ".txt", ".yaml", ".yml", ".toml"]
    
    def scan_file_content(self, file_path: Path) -> None:
        """Scan a single file for backward compatibility artifacts."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            rel_path = str(file_path.relative_to(self.root_path))
            
            # Scan line by line
            for line_num, line in enumerate(lines, 1):
                self._scan_line(rel_path, line_num, line)
                
            # For Python files, also do AST analysis
            if file_path.suffix == ".py":
                self._scan_python_ast(file_path, content)
                
        except (UnicodeDecodeError, FileNotFoundError, PermissionError) as e:
            print(f"Warning: Could not read {file_path}: {e}")
    
    def _scan_line(self, file_path: str, line_num: int, line: str) -> None:
        """Scan a single line for patterns."""
        line_lower = line.lower()
        
        # Check comment patterns
        for pattern, artifact_type in self.comment_patterns:
            if re.search(pattern, line_lower):
                risk_level = self._assess_risk_level(artifact_type, line)
                artifact = CompatibilityArtifact(
                    artifact_type=artifact_type,
                    file_path=file_path,
                    line_number=line_num,
                    content=line.strip(),
                    risk_level=risk_level,
                    removal_notes=self._get_removal_notes(artifact_type)
                )
                self.report.add_artifact(artifact)
        
        # Check code patterns
        for pattern, artifact_type in self.code_patterns:
            if re.search(pattern, line):
                risk_level = self._assess_risk_level(artifact_type, line)
                artifact = CompatibilityArtifact(
                    artifact_type=artifact_type,
                    file_path=file_path,
                    line_number=line_num,
                    content=line.strip(),
                    risk_level=risk_level,
                    removal_notes=self._get_removal_notes(artifact_type)
                )
                self.report.add_artifact(artifact)
        
        # Check import patterns
        for pattern, artifact_type in self.import_patterns:
            if re.search(pattern, line):
                risk_level = self._assess_risk_level(artifact_type, line)
                artifact = CompatibilityArtifact(
                    artifact_type=artifact_type,
                    file_path=file_path,
                    line_number=line_num,
                    content=line.strip(),
                    risk_level=risk_level,
                    removal_notes=self._get_removal_notes(artifact_type)
                )
                self.report.add_artifact(artifact)
    
    def _scan_python_ast(self, file_path: Path, content: str) -> None:
        """Scan Python AST for compatibility artifacts."""
        try:
            tree = ast.parse(content)
            rel_path = str(file_path.relative_to(self.root_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for functions with backward compatibility indicators
                    if any(keyword in node.name.lower() for keyword in ['legacy', 'compat', 'backward']):
                        artifact = CompatibilityArtifact(
                            artifact_type="legacy_function",
                            file_path=rel_path,
                            line_number=node.lineno,
                            content=f"def {node.name}(...)",
                            risk_level="medium",
                            removal_notes="Function with legacy naming pattern"
                        )
                        self.report.add_artifact(artifact)
                
                elif isinstance(node, ast.Assign):
                    # Check for legacy variable assignments
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if any(keyword in target.id.lower() for keyword in ['legacy', 'compat', 'backward']):
                                artifact = CompatibilityArtifact(
                                    artifact_type="legacy_variable",
                                    file_path=rel_path,
                                    line_number=node.lineno,
                                    content=f"{target.id} = ...",
                                    risk_level="low",
                                    removal_notes="Variable with legacy naming pattern"
                                )
                                self.report.add_artifact(artifact)
                
        except SyntaxError:
            # Skip files with syntax errors
            pass
    
    def _assess_risk_level(self, artifact_type: str, content: str) -> str:
        """Assess the risk level of removing an artifact."""
        # High risk patterns
        high_risk_patterns = [
            "global",
            "public api",
            "exported",
            "__all__",
            "facade",
            "interface"
        ]
        
        # Low risk patterns  
        low_risk_patterns = [
            "todo",
            "note:",
            "comment",
            "internal",
            "private",
            "_"
        ]
        
        content_lower = content.lower()
        
        if any(pattern in content_lower for pattern in high_risk_patterns):
            return "high"
        elif any(pattern in content_lower for pattern in low_risk_patterns):
            return "low"
        else:
            return "medium"
    
    def _get_removal_notes(self, artifact_type: str) -> str:
        """Get specific removal notes for an artifact type."""
        notes_map = {
            "backward_compatibility_comment": "Review and remove comment if no longer needed",
            "migration_todo": "Complete TODO item or remove if obsolete",
            "phase_todo": "Address phase-specific TODO or mark as complete",
            "legacy_comment": "Remove legacy reference",
            "backward_compat_function": "Replace calls and remove function",
            "legacy_alias": "Update references to use new name",
            "legacy_import": "Update to use new import path",
            "legacy_function": "Refactor callers to use new implementation",
        }
        return notes_map.get(artifact_type, "Review and remove if no longer needed")
    
    def scan_directory_structure(self) -> None:
        """Scan for legacy directory structures."""
        for root, dirs, files in os.walk(self.root_path):
            for directory in dirs:
                if any(legacy_dir in directory.lower() for legacy_dir in self.legacy_directories):
                    dir_path = Path(root) / directory
                    rel_path = str(dir_path.relative_to(self.root_path))
                    
                    artifact = CompatibilityArtifact(
                        artifact_type="legacy_directory",
                        file_path=rel_path,
                        line_number=0,
                        content=f"Directory: {directory}",
                        risk_level="high",
                        removal_notes="Review contents before removing entire directory"
                    )
                    self.report.add_artifact(artifact)
    
    def scan_old_ddd_structure(self) -> None:
        """Scan for old DDD layered architecture that should be migrated."""
        old_structure_dirs = [
            "the_alchemiser/application",
            "the_alchemiser/domain", 
            "the_alchemiser/services",
            "the_alchemiser/infrastructure",
            "the_alchemiser/utils"
        ]
        
        for dir_path in old_structure_dirs:
            full_path = self.root_path / dir_path
            if full_path.exists() and full_path.is_dir():
                # Check if it has any Python files
                python_files = list(full_path.rglob("*.py"))
                if python_files:
                    artifact = CompatibilityArtifact(
                        artifact_type="old_ddd_structure",
                        file_path=dir_path,
                        line_number=0,
                        content=f"Old DDD directory with {len(python_files)} Python files",
                        risk_level="high",
                        removal_notes="Migrate remaining code to new modular structure"
                    )
                    self.report.add_artifact(artifact)
    
    def run_scan(self) -> ScanReport:
        """Run the complete scan."""
        from datetime import datetime
        
        print("🔍 Starting backward compatibility artifact scan...")
        
        self.report.scan_timestamp = datetime.now().isoformat()
        
        # Scan directory structure first
        print("📁 Scanning directory structure...")
        self.scan_directory_structure()
        self.scan_old_ddd_structure()
        
        # Scan all files
        print("📄 Scanning file contents...")
        scanned_files = 0
        for root, dirs, files in os.walk(self.root_path):
            for file in files:
                file_path = Path(root) / file
                if self.should_scan_file(file_path):
                    self.scan_file_content(file_path)
                    scanned_files += 1
                    if scanned_files % 50 == 0:
                        print(f"   Scanned {scanned_files} files...")
        
        print(f"✅ Scan complete. Processed {scanned_files} files.")
        return self.report
    
    def generate_report(self, output_format: str = "json") -> str:
        """Generate a formatted report."""
        if output_format == "json":
            return self._generate_json_report()
        elif output_format == "markdown":
            return self._generate_markdown_report()
        else:
            return self._generate_text_report()
    
    def _generate_json_report(self) -> str:
        """Generate JSON format report."""
        report_data = {
            "scan_timestamp": self.report.scan_timestamp,
            "summary": self.report.summary,
            "total_artifacts": len(self.report.artifacts),
            "artifacts": [
                {
                    "type": artifact.artifact_type,
                    "file": artifact.file_path,
                    "line": artifact.line_number,
                    "content": artifact.content,
                    "risk_level": artifact.risk_level,
                    "removal_notes": artifact.removal_notes
                }
                for artifact in self.report.artifacts
            ]
        }
        return json.dumps(report_data, indent=2)
    
    def _generate_markdown_report(self) -> str:
        """Generate Markdown format report."""
        report = ["# Phase 7 Cleanup - Backward Compatibility Artifacts Report\n"]
        report.append(f"**Scan Date:** {self.report.scan_timestamp}\n")
        report.append(f"**Total Artifacts Found:** {len(self.report.artifacts)}\n")
        
        # Summary by type
        report.append("## Summary by Type\n")
        for artifact_type, count in sorted(self.report.summary.items()):
            report.append(f"- **{artifact_type}**: {count}")
        report.append("")
        
        # Summary by risk level
        risk_summary = {}
        for artifact in self.report.artifacts:
            risk_summary[artifact.risk_level] = risk_summary.get(artifact.risk_level, 0) + 1
        
        report.append("## Summary by Risk Level\n")
        for risk_level in ["high", "medium", "low"]:
            count = risk_summary.get(risk_level, 0)
            report.append(f"- **{risk_level.title()} Risk**: {count}")
        report.append("")
        
        # Detailed findings
        report.append("## Detailed Findings\n")
        
        # Group by risk level
        for risk_level in ["high", "medium", "low"]:
            risk_artifacts = [a for a in self.report.artifacts if a.risk_level == risk_level]
            if risk_artifacts:
                report.append(f"### {risk_level.title()} Risk Items ({len(risk_artifacts)})\n")
                
                for artifact in risk_artifacts:
                    report.append(f"**{artifact.artifact_type}** - `{artifact.file_path}:{artifact.line_number}`")
                    report.append(f"```")
                    report.append(artifact.content)
                    report.append(f"```")
                    report.append(f"*Removal Notes:* {artifact.removal_notes}\n")
        
        return "\n".join(report)
    
    def _generate_text_report(self) -> str:
        """Generate plain text report."""
        report = [f"Phase 7 Cleanup - Backward Compatibility Artifacts Report"]
        report.append(f"Scan Date: {self.report.scan_timestamp}")
        report.append(f"Total Artifacts Found: {len(self.report.artifacts)}")
        report.append("")
        
        # Summary
        report.append("Summary by Type:")
        for artifact_type, count in sorted(self.report.summary.items()):
            report.append(f"  {artifact_type}: {count}")
        report.append("")
        
        # Detailed findings
        report.append("Detailed Findings:")
        report.append("=" * 50)
        
        for i, artifact in enumerate(self.report.artifacts, 1):
            report.append(f"{i}. [{artifact.risk_level.upper()}] {artifact.artifact_type}")
            report.append(f"   File: {artifact.file_path}:{artifact.line_number}")
            report.append(f"   Content: {artifact.content}")
            report.append(f"   Notes: {artifact.removal_notes}")
            report.append("")
        
        return "\n".join(report)


def main():
    """Main entry point for the scanner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scan for backward compatibility artifacts")
    parser.add_argument("--root", default=".", help="Root directory to scan")
    parser.add_argument("--format", choices=["json", "markdown", "text"], default="markdown", 
                       help="Output format")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--filter-risk", choices=["high", "medium", "low"], 
                       help="Only show artifacts of specified risk level")
    
    args = parser.parse_args()
    
    scanner = BackwardCompatibilityScanner(args.root)
    report = scanner.run_scan()
    
    # Filter by risk level if specified
    if args.filter_risk:
        report.artifacts = [a for a in report.artifacts if a.risk_level == args.filter_risk]
        # Recalculate summary
        report.summary = {}
        for artifact in report.artifacts:
            report.summary[artifact.artifact_type] = report.summary.get(artifact.artifact_type, 0) + 1
    
    output = scanner.generate_report(args.format)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()