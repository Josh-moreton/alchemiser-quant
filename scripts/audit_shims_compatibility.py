#!/usr/bin/env python3
"""Comprehensive Shims & Compatibility Layers Audit Script.

This script systematically identifies all shims, compatibility layers, polyfills,
and backward-compatibility code in the codebase to support issue #492.
"""

from __future__ import annotations

import ast
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ShimInfo:
    """Information about a detected shim or compatibility layer."""

    file_path: str
    description: str
    purpose: str
    dependency: str | None = None
    suggested_action: str = "analyze"
    risk_level: str = "medium"
    evidence: list[str] = field(default_factory=list)
    active_imports: int = 0
    replacement_path: str | None = None


class ShimAuditor:
    """Comprehensive shim and compatibility layer auditor."""

    def __init__(self, root_path: str = ".") -> None:
        """Initialize the auditor."""
        self.root_path = Path(root_path)
        self.findings: list[ShimInfo] = []
        self.exclude_patterns = [
            ".venv",
            "__pycache__",
            ".git",
            "node_modules",
            "dist",
            "build",
        ]

    def audit_all(self) -> list[ShimInfo]:
        """Run comprehensive audit for all types of shims and compatibility layers."""
        print("🔍 Starting comprehensive shims & compatibility audit...")

        # 1. Files explicitly named with shim/compat/legacy keywords
        self._audit_by_filename_patterns()

        # 2. Files with shim/compatibility content patterns
        self._audit_by_content_patterns()

        # 3. Deprecation warnings and notices
        self._audit_deprecation_warnings()

        # 4. Import redirections and compatibility imports
        self._audit_import_redirections()

        # 5. Backup and temporary files
        self._audit_backup_files()

        # 6. Status markers indicating legacy/compatibility
        self._audit_status_markers()

        # 7. Polyfills and browser compatibility (if any)
        self._audit_polyfills()

        # 8. Analyze active imports for each finding
        self._analyze_active_imports()

        print(f"✅ Audit complete. Found {len(self.findings)} potential shims/compatibility layers.")
        return self.findings

    def _audit_by_filename_patterns(self) -> None:
        """Audit files with shim/compatibility keywords in filename."""
        patterns = ["*shim*", "*compat*", "*legacy*", "*deprecated*", "*polyfill*", "*adapter*"]

        for pattern in patterns:
            for file_path in self._find_python_files_by_pattern(pattern):
                if self._should_exclude_file(file_path):
                    continue

                purpose = f"File named with pattern: {pattern}"
                risk = "medium" if "legacy" in str(file_path).lower() else "low"

                self.findings.append(
                    ShimInfo(
                        file_path=str(file_path),
                        description=f"File with {pattern} pattern in name",
                        purpose=purpose,
                        risk_level=risk,
                        evidence=[f"Filename matches pattern: {pattern}"],
                    )
                )

    def _audit_by_content_patterns(self) -> None:
        """Audit files containing shim/compatibility keywords in content."""
        keywords = [
            "shim",
            "compatibility",
            "backward",
            "compat",
            "polyfill",
            "adapter",
            "wrapper",
            "bridge",
        ]

        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]

                if found_keywords:
                    self.findings.append(
                        ShimInfo(
                            file_path=str(file_path),
                            description=f"Contains compatibility/shim keywords: {', '.join(found_keywords)}",
                            purpose="File contains compatibility-related content",
                            risk_level="medium",
                            evidence=[f"Keywords found: {', '.join(found_keywords)}"],
                        )
                    )
            except (UnicodeDecodeError, PermissionError):
                continue

    def _audit_deprecation_warnings(self) -> None:
        """Audit files with deprecation warnings and notices."""
        deprecation_patterns = [
            r"warnings\.warn.*[Dd]eprecat",
            r"DEPRECATED",
            r"TODO.*remove",
            r"FIXME.*remove",
            r"@deprecated",
            r"#.*deprecated",
        ]

        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                matches = []

                for pattern in deprecation_patterns:
                    pattern_matches = re.findall(pattern, content, re.IGNORECASE)
                    matches.extend(pattern_matches)

                if matches:
                    self.findings.append(
                        ShimInfo(
                            file_path=str(file_path),
                            description="Contains deprecation warnings or removal notices",
                            purpose="File marked for deprecation or removal",
                            suggested_action="review_for_removal",
                            risk_level="high",
                            evidence=[f"Deprecation patterns: {', '.join(matches[:3])}"],
                        )
                    )
            except (UnicodeDecodeError, PermissionError):
                continue

    def _audit_import_redirections(self) -> None:
        """Audit import redirections and compatibility imports."""
        redirection_patterns = [
            r"from.*import.*\*.*#.*redirect",
            r"from.*import.*\*.*#.*compat",
            r"# Import.*redirect",
            r"# Legacy import",
            r"# Backward compatibility",
            r"moved to",
            r"import.*redirect",
        ]

        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                matches = []

                for pattern in redirection_patterns:
                    pattern_matches = re.findall(pattern, content, re.IGNORECASE)
                    matches.extend(pattern_matches)

                # Also check for star imports with compatibility comments
                star_import_lines = [
                    line.strip()
                    for line in content.split("\n")
                    if "import *" in line and any(kw in line.lower() for kw in ["redirect", "compat", "legacy"])
                ]
                matches.extend(star_import_lines)

                if matches:
                    self.findings.append(
                        ShimInfo(
                            file_path=str(file_path),
                            description="Contains import redirections or compatibility imports",
                            purpose="File provides import compatibility layer",
                            suggested_action="migrate_imports",
                            risk_level="medium",
                            evidence=[f"Import patterns: {', '.join(matches[:3])}"],
                        )
                    )
            except (UnicodeDecodeError, PermissionError):
                continue

    def _audit_backup_files(self) -> None:
        """Audit backup and temporary files."""
        backup_patterns = ["*.backup", "*.bak", "*.orig", "*_backup.py", "*_original.py"]

        for pattern in backup_patterns:
            for file_path in self.root_path.rglob(pattern):
                if self._should_exclude_file(file_path):
                    continue

                self.findings.append(
                    ShimInfo(
                        file_path=str(file_path),
                        description=f"Backup file with pattern: {pattern}",
                        purpose="Backup or temporary file",
                        suggested_action="remove",
                        risk_level="low",
                        evidence=[f"Backup file pattern: {pattern}"],
                    )
                )

    def _audit_status_markers(self) -> None:
        """Audit files with Status: legacy or similar markers."""
        status_patterns = [
            r"Status.*legacy",
            r"Status.*deprecated",
            r"Business Unit.*legacy",
        ]

        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                matches = []

                for pattern in status_patterns:
                    pattern_matches = re.findall(pattern, content, re.IGNORECASE)
                    matches.extend(pattern_matches)

                if matches:
                    self.findings.append(
                        ShimInfo(
                            file_path=str(file_path),
                            description="File marked with legacy/deprecated status",
                            purpose="File explicitly marked as legacy or deprecated",
                            suggested_action="review_for_migration",
                            risk_level="high",
                            evidence=[f"Status markers: {', '.join(matches)}"],
                        )
                    )
            except (UnicodeDecodeError, PermissionError):
                continue

    def _audit_polyfills(self) -> None:
        """Audit for polyfills and environment-specific patches."""
        polyfill_patterns = [
            r"polyfill",
            r"# Patch for",
            r"# Fix for.*version",
            r"try:.*except ImportError:",
            r"sys\.version_info",
            r"platform\.",
        ]

        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                matches = []

                for pattern in polyfill_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        matches.append(pattern)

                if matches:
                    self.findings.append(
                        ShimInfo(
                            file_path=str(file_path),
                            description="Contains polyfill or environment-specific compatibility code",
                            purpose="File provides cross-version or cross-platform compatibility",
                            suggested_action="review_for_modernization",
                            risk_level="medium",
                            evidence=[f"Polyfill patterns: {', '.join(matches[:3])}"],
                        )
                    )
            except (UnicodeDecodeError, PermissionError):
                continue

    def _analyze_active_imports(self) -> None:
        """Analyze how many files actively import from each detected shim."""
        for finding in self.findings:
            if finding.file_path.endswith(".py"):
                # Convert file path to import path
                import_path = self._file_path_to_import_path(finding.file_path)
                finding.active_imports = self._count_imports_of_module(import_path)

                if finding.active_imports > 0:
                    finding.risk_level = "high"
                    finding.evidence.append(f"Actively imported by {finding.active_imports} files")

    def _file_path_to_import_path(self, file_path: str) -> str:
        """Convert file path to Python import path."""
        # Remove file extension and convert to import path
        path = Path(file_path)
        if path.suffix == ".py":
            path = path.with_suffix("")

        # Convert to import path
        import_path = str(path).replace("/", ".").replace("\\", ".")
        
        # Remove leading ./ if present
        if import_path.startswith("./"):
            import_path = import_path[2:]

        return import_path

    def _count_imports_of_module(self, module_path: str) -> int:
        """Count how many files import from a specific module."""
        count = 0
        import_patterns = [
            rf"from\s+{re.escape(module_path)}\s+import",
            rf"import\s+{re.escape(module_path)}",
        ]

        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                for pattern in import_patterns:
                    if re.search(pattern, content):
                        count += 1
                        break
            except (UnicodeDecodeError, PermissionError):
                continue

        return count

    def _find_python_files_by_pattern(self, pattern: str) -> list[Path]:
        """Find Python files matching a glob pattern."""
        return [p for p in self.root_path.rglob(pattern) if p.suffix == ".py"]

    def _find_all_python_files(self) -> list[Path]:
        """Find all Python files in the repository."""
        return [p for p in self.root_path.rglob("*.py")]

    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from analysis."""
        path_str = str(file_path)
        return any(pattern in path_str for pattern in self.exclude_patterns)

    def generate_report(self, output_file: str = "SHIMS_COMPATIBILITY_AUDIT_REPORT.md") -> None:
        """Generate a comprehensive audit report."""
        print(f"📝 Generating report: {output_file}")

        # Categorize findings
        by_risk = {"high": [], "medium": [], "low": []}
        by_type = {}

        for finding in self.findings:
            by_risk[finding.risk_level].append(finding)
            
            # Categorize by type based on description
            if "backup" in finding.description.lower():
                type_key = "Backup Files"
            elif "deprecat" in finding.description.lower():
                type_key = "Deprecated Code"
            elif "import" in finding.description.lower():
                type_key = "Import Redirections"
            elif "legacy" in finding.description.lower():
                type_key = "Legacy Code"
            elif "status" in finding.description.lower():
                type_key = "Status Markers"
            else:
                type_key = "Other Compatibility"
            
            if type_key not in by_type:
                by_type[type_key] = []
            by_type[type_key].append(finding)

        # Generate report content
        report_lines = [
            "# Shims & Compatibility Layers Audit Report",
            "",
            "## Executive Summary",
            "",
            f"This report provides a comprehensive audit of all shims, compatibility layers, and backward-compatibility code in the codebase. The audit identified **{len(self.findings)} potential items** requiring review.",
            "",
            f"**Risk Distribution:**",
            f"- 🔴 **High Risk**: {len(by_risk['high'])} items",
            f"- 🟡 **Medium Risk**: {len(by_risk['medium'])} items", 
            f"- 🟢 **Low Risk**: {len(by_risk['low'])} items",
            "",
            "## Summary by Category",
            "",
        ]

        for category, items in by_type.items():
            report_lines.extend([
                f"### {category} ({len(items)} items)",
                "",
            ])
            for item in items:
                report_lines.append(f"- `{item.file_path}` - {item.description}")
            report_lines.append("")

        # Detailed findings by risk level
        report_lines.extend([
            "## Detailed Findings by Risk Level",
            "",
        ])

        for risk_level in ["high", "medium", "low"]:
            items = by_risk[risk_level]
            if not items:
                continue

            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[risk_level]
            report_lines.extend([
                f"### {icon} {risk_level.upper()} RISK ({len(items)} items)",
                "",
            ])

            for i, item in enumerate(items, 1):
                report_lines.extend([
                    f"**{i}. {Path(item.file_path).name}**",
                    f"- **File**: `{item.file_path}`",
                    f"- **Description**: {item.description}",
                    f"- **Purpose**: {item.purpose}",
                    f"- **Suggested Action**: {item.suggested_action}",
                    f"- **Risk Level**: {item.risk_level}",
                ])
                if item.dependency:
                    report_lines.append(f"- **Dependency**: {item.dependency}")
                if item.replacement_path:
                    report_lines.append(f"- **Replacement**: `{item.replacement_path}`")
                if item.active_imports > 0:
                    report_lines.append(f"- **Active Imports**: {item.active_imports} files")
                if item.evidence:
                    report_lines.append(f"- **Evidence**: {'; '.join(item.evidence)}")
                report_lines.append("")

        # Recommendations
        report_lines.extend([
            "## Recommendations",
            "",
            "### Immediate Actions",
            "1. **High Risk Items**: Require immediate attention and careful migration planning",
            "2. **Active Imports**: Items with active imports need coordinated migration",
            "3. **Backup Files**: Can likely be safely removed if no longer needed",
            "",
            "### Risk Mitigation",
            "1. **Never remove more than 5 shims without testing**",
            "2. **Update import statements before removing shim files**",
            "3. **Maintain compatibility during migration periods**",
            "4. **Test thoroughly after each removal**",
            "",
            "---",
            "",
            f"**Generated**: {json.dumps(None)}",
            "**Scope**: Complete codebase shims and compatibility audit",
            "**Issue**: #492",
            "**Tool**: scripts/audit_shims_compatibility.py",
        ])

        # Write report
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        print(f"✅ Report generated: {output_file}")


def main() -> None:
    """Main entry point."""
    auditor = ShimAuditor()
    findings = auditor.audit_all()
    auditor.generate_report()

    print(f"\n📊 Audit Summary:")
    print(f"   Total findings: {len(findings)}")
    print(f"   High risk: {len([f for f in findings if f.risk_level == 'high'])}")
    print(f"   Medium risk: {len([f for f in findings if f.risk_level == 'medium'])}")
    print(f"   Low risk: {len([f for f in findings if f.risk_level == 'low'])}")


if __name__ == "__main__":
    main()