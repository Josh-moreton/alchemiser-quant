#!/usr/bin/env python3
"""Refined Shims & Compatibility Layers Audit Script.

This script focuses on identifying ACTUAL shims and compatibility layers,
not just files that mention compatibility in comments.
"""

from __future__ import annotations

import ast
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


class RefinedShimAuditor:
    """Refined shim and compatibility layer auditor focusing on actual shims."""

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
            "scripts/refined_shim_auditor.py",
            "scripts/audit_shims_compatibility.py",
        ]

    def audit_actual_shims(self) -> list[ShimInfo]:
        """Run focused audit for actual shims and compatibility layers."""
        print("🔍 Starting refined audit for ACTUAL shims & compatibility layers...")

        # 1. Explicit legacy/deprecated files with Status markers
        self._audit_explicit_legacy_status()

        # 2. Files with deprecation warnings
        self._audit_deprecation_warnings()

        # 3. Import redirection shims (actual star imports with redirects)
        self._audit_import_redirections()

        # 4. Backup files
        self._audit_backup_files()

        # 5. Files explicitly named as legacy/shim/deprecated
        self._audit_explicit_legacy_filenames()

        # 6. Module-level redirections (import * from new location)
        self._audit_module_redirections()

        # 7. Compatibility shims with explicit markers
        self._audit_compatibility_shims()

        # 8. Analyze active imports for each finding
        self._analyze_active_imports()

        print(f"✅ Refined audit complete. Found {len(self.findings)} actual shims/compatibility layers.")
        return self.findings

    def _audit_explicit_legacy_status(self) -> None:
        """Audit files with explicit legacy/deprecated status markers."""
        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Look for explicit status markers in docstrings/comments
                status_patterns = [
                    r'".*Status.*legacy.*"',
                    r"'.*Status.*legacy.*'",
                    r'".*Status.*deprecated.*"',
                    r"'.*Status.*deprecated.*'",
                ]

                matches = []
                for pattern in status_patterns:
                    pattern_matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                    matches.extend(pattern_matches)

                if matches:
                    self.findings.append(
                        ShimInfo(
                            file_path=str(file_path),
                            description="File explicitly marked with legacy/deprecated status",
                            purpose="File with explicit legacy/deprecated status marker",
                            suggested_action="review_for_migration",
                            risk_level="high",
                            evidence=[f"Status markers: {matches[0][:100]}..."],
                        )
                    )
            except (UnicodeDecodeError, PermissionError):
                continue

    def _audit_deprecation_warnings(self) -> None:
        """Audit files with actual deprecation warnings."""
        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Look for actual warnings.warn calls with deprecation
                deprecation_patterns = [
                    r"warnings\.warn\s*\(",
                    r"DeprecationWarning",
                    r"\[DEPRECATED\]",
                    r"DEPRECATED:",
                ]

                found_patterns = []
                for pattern in deprecation_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        found_patterns.append(pattern)

                if found_patterns:
                    # Extract the actual warning message if possible
                    warning_match = re.search(
                        r"warnings\.warn\s*\(\s*[\"'](.*?)[\"']",
                        content,
                        re.IGNORECASE | re.DOTALL
                    )
                    
                    evidence = found_patterns
                    if warning_match:
                        evidence.append(f"Warning: {warning_match.group(1)[:100]}...")

                    self.findings.append(
                        ShimInfo(
                            file_path=str(file_path),
                            description="Contains actual deprecation warnings",
                            purpose="File issues deprecation warnings",
                            suggested_action="review_for_removal",
                            risk_level="high",
                            evidence=evidence,
                        )
                    )
            except (UnicodeDecodeError, PermissionError):
                continue

    def _audit_import_redirections(self) -> None:
        """Audit actual import redirection shims."""
        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Look for actual star imports that look like redirections
                star_import_lines = [
                    line.strip()
                    for line in content.split("\n")
                    if "import *" in line
                ]

                # Look for explicit redirection comments
                redirection_comments = [
                    line.strip()
                    for line in content.split("\n")
                    if any(phrase in line.lower() for phrase in [
                        "import redirected",
                        "moved to",
                        "redirect",
                        "shim maintains",
                        "backward compatibility"
                    ])
                ]

                if star_import_lines or redirection_comments:
                    evidence = []
                    if star_import_lines:
                        evidence.extend([f"Star import: {line}" for line in star_import_lines[:3]])
                    if redirection_comments:
                        evidence.extend([f"Redirection: {line}" for line in redirection_comments[:3]])

                    self.findings.append(
                        ShimInfo(
                            file_path=str(file_path),
                            description="Contains import redirections",
                            purpose="Import redirection/compatibility shim",
                            suggested_action="migrate_imports",
                            risk_level="medium",
                            evidence=evidence,
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
                        description=f"Backup file",
                        purpose="Backup or temporary file that should be cleaned up",
                        suggested_action="remove",
                        risk_level="low",
                        evidence=[f"Backup file pattern: {pattern}"],
                    )
                )

    def _audit_explicit_legacy_filenames(self) -> None:
        """Audit files explicitly named with legacy/shim/deprecated keywords."""
        patterns = ["*legacy*", "*deprecated*", "*shim*"]

        for pattern in patterns:
            for file_path in self._find_python_files_by_pattern(pattern):
                if self._should_exclude_file(file_path):
                    continue

                risk = "high" if "legacy" in str(file_path).lower() else "medium"

                self.findings.append(
                    ShimInfo(
                        file_path=str(file_path),
                        description=f"File explicitly named with {pattern}",
                        purpose=f"File explicitly named with legacy/deprecated pattern",
                        suggested_action="review_for_migration",
                        risk_level=risk,
                        evidence=[f"Filename pattern: {pattern}"],
                    )
                )

    def _audit_module_redirections(self) -> None:
        """Audit modules that just redirect imports to new locations."""
        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                lines = [line.strip() for line in content.split("\n") if line.strip()]
                
                # Skip files that are too long to be simple redirections
                if len(lines) > 30:
                    continue

                # Check if file is mostly imports and has redirection indicators
                import_lines = [line for line in lines if line.startswith(("import ", "from "))]
                comment_lines = [line for line in lines if line.startswith("#")]
                
                has_redirection_indicators = any(
                    phrase in content.lower()
                    for phrase in [
                        "moved to",
                        "redirect",
                        "import.*from.*new",
                        "compatibility",
                        "backward",
                        "shim maintains",
                        "import everything from"
                    ]
                )

                # If file is mostly imports and has redirection language
                if (
                    len(import_lines) > len(lines) // 2
                    and has_redirection_indicators
                    and len(lines) < 20
                ):
                    self.findings.append(
                        ShimInfo(
                            file_path=str(file_path),
                            description="Module appears to be an import redirection shim",
                            purpose="Simple module that redirects imports to new location",
                            suggested_action="migrate_imports",
                            risk_level="medium",
                            evidence=[f"Small module with {len(import_lines)} imports and redirection language"],
                        )
                    )

            except (UnicodeDecodeError, PermissionError):
                continue

    def _audit_compatibility_shims(self) -> None:
        """Audit files that explicitly mention they are compatibility shims."""
        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Look for explicit shim language in docstrings/comments
                shim_indicators = [
                    "this shim",
                    "shim maintains",
                    "compatibility shim",
                    "backward compatibility",
                    "maintains backward",
                    "import redirected",
                    "everything from the new location",
                ]

                found_indicators = [
                    indicator for indicator in shim_indicators
                    if indicator in content.lower()
                ]

                if found_indicators:
                    self.findings.append(
                        ShimInfo(
                            file_path=str(file_path),
                            description="File explicitly describes itself as a compatibility shim",
                            purpose="Explicit compatibility/backward-compatibility shim",
                            suggested_action="migrate_imports",
                            risk_level="high",
                            evidence=[f"Shim indicators: {', '.join(found_indicators[:3])}"],
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
        path = Path(file_path)
        if path.suffix == ".py":
            path = path.with_suffix("")

        import_path = str(path).replace("/", ".").replace("\\", ".")
        
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

    def generate_report(self, output_file: str = "REFINED_SHIMS_AUDIT_REPORT.md") -> None:
        """Generate a focused audit report for actual shims."""
        print(f"📝 Generating focused report: {output_file}")

        # Categorize findings
        by_risk = {"high": [], "medium": [], "low": []}
        by_type = {}

        for finding in self.findings:
            by_risk[finding.risk_level].append(finding)
            
            # Categorize by type
            if "backup" in finding.description.lower():
                type_key = "Backup Files"
            elif "deprecat" in finding.description.lower():
                type_key = "Deprecated Code"
            elif "status" in finding.description.lower():
                type_key = "Legacy Status Markers"
            elif "import" in finding.description.lower():
                type_key = "Import Redirections"
            elif "filename" in finding.description.lower() or "named" in finding.description.lower():
                type_key = "Legacy Named Files"
            else:
                type_key = "Compatibility Shims"
            
            if type_key not in by_type:
                by_type[type_key] = []
            by_type[type_key].append(finding)

        # Generate report content
        report_lines = [
            "# Refined Shims & Compatibility Layers Audit Report",
            "",
            "## Executive Summary",
            "",
            f"This report provides a focused audit of **ACTUAL** shims, compatibility layers, and backward-compatibility code in the codebase. Unlike broader audits, this focuses on files that are genuinely shims or compatibility layers.",
            "",
            f"**Total Actual Shims Found**: {len(self.findings)}",
            "",
            f"**Risk Distribution:**",
            f"- 🔴 **High Risk**: {len(by_risk['high'])} items (active shims requiring careful migration)",
            f"- 🟡 **Medium Risk**: {len(by_risk['medium'])} items (import redirections and compatibility layers)",
            f"- 🟢 **Low Risk**: {len(by_risk['low'])} items (backup files and cleanup items)",
            "",
            "## Summary by Category",
            "",
        ]

        for category, items in by_type.items():
            report_lines.extend([
                f"### {category} ({len(items)} items)",
                "",
            ])
            
            for item in sorted(items, key=lambda x: x.risk_level, reverse=True):
                risk_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[item.risk_level]
                imports_info = f" ({item.active_imports} imports)" if item.active_imports > 0 else ""
                report_lines.append(f"- {risk_icon} `{item.file_path}`{imports_info} - {item.description}")
            report_lines.append("")

        # Detailed findings by risk level
        report_lines.extend([
            "## Detailed Analysis",
            "",
        ])

        for risk_level in ["high", "medium", "low"]:
            items = by_risk[risk_level]
            if not items:
                continue

            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[risk_level]
            report_lines.extend([
                f"### {icon} {risk_level.upper()} RISK SHIMS ({len(items)} items)",
                "",
            ])

            for i, item in enumerate(items, 1):
                report_lines.extend([
                    f"**{i}. {Path(item.file_path).name}**",
                    f"- **File**: `{item.file_path}`",
                    f"- **Description**: {item.description}",
                    f"- **Purpose**: {item.purpose}",
                    f"- **Suggested Action**: {item.suggested_action}",
                ])
                if item.replacement_path:
                    report_lines.append(f"- **Replacement**: `{item.replacement_path}`")
                if item.active_imports > 0:
                    report_lines.append(f"- **Active Imports**: {item.active_imports} files importing this shim")
                if item.evidence:
                    report_lines.append(f"- **Evidence**: {'; '.join(item.evidence)}")
                report_lines.append("")

        # Specific recommendations
        high_risk_items = by_risk["high"]
        active_import_items = [f for f in self.findings if f.active_imports > 0]
        
        report_lines.extend([
            "## Specific Recommendations",
            "",
            "### High Priority Actions",
            "",
        ])
        
        if high_risk_items:
            report_lines.extend([
                f"1. **Review {len(high_risk_items)} high-risk shims** - These require immediate attention",
                f"2. **Migrate {len(active_import_items)} actively imported shims** - Update import statements first",
                "3. **Remove backup files** - These can likely be safely deleted",
                "",
            ])

        report_lines.extend([
            "### Migration Strategy",
            "",
            "1. **Phase 1**: Update import statements for actively used shims",
            "2. **Phase 2**: Remove or replace deprecated shims with warnings",
            "3. **Phase 3**: Clean up backup files and unused legacy code",
            "4. **Phase 4**: Validate no broken imports remain",
            "",
            "### Safety Guidelines",
            "",
            "- **Never remove a shim with active imports without migration**",
            "- **Test after each shim removal**",
            "- **Keep migration atomic - one shim at a time**",
            "- **Document replacement paths for team awareness**",
            "",
            "---",
            "",
            f"**Generated**: January 2025",
            "**Scope**: Actual shims and compatibility layers only",
            "**Issue**: #492",
            "**Tool**: scripts/refined_shim_auditor.py",
        ])

        # Write report
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        print(f"✅ Focused report generated: {output_file}")


def main() -> None:
    """Main entry point."""
    auditor = RefinedShimAuditor()
    findings = auditor.audit_actual_shims()
    auditor.generate_report()

    print(f"\n📊 Refined Audit Summary:")
    print(f"   Actual shims found: {len(findings)}")
    print(f"   High risk: {len([f for f in findings if f.risk_level == 'high'])}")
    print(f"   Medium risk: {len([f for f in findings if f.risk_level == 'medium'])}")
    print(f"   Low risk: {len([f for f in findings if f.risk_level == 'low'])}")
    print(f"   With active imports: {len([f for f in findings if f.active_imports > 0])}")


if __name__ == "__main__":
    main()