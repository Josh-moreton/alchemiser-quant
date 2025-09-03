#!/usr/bin/env python3
"""Focused Shims Audit - Only Obvious Shims.

This script identifies only the most obvious shims and compatibility layers:
1. Files explicitly named with "legacy", "shim", "deprecated"
2. Files with actual deprecation warnings
3. Files that explicitly redirect imports
4. Backup files
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


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


class FocusedShimAuditor:
    """Auditor that finds only obvious shims and compatibility layers."""

    def __init__(self, root_path: str = ".") -> None:
        """Initialize the auditor."""
        self.root_path = Path(root_path)
        self.findings: list[ShimInfo] = []
        self.exclude_patterns = [
            ".venv",
            "__pycache__",
            ".git",
            "scripts/",
        ]

    def audit_obvious_shims(self) -> list[ShimInfo]:
        """Find only the most obvious shims."""
        print("🔍 Starting focused audit for OBVIOUS shims only...")

        # 1. Files explicitly named legacy/shim/deprecated
        self._audit_obvious_legacy_filenames()

        # 2. Files with actual warnings.warn deprecation calls
        self._audit_actual_deprecation_warnings()

        # 3. Files with explicit Status: legacy markers
        self._audit_explicit_status_markers()

        # 4. Files that are obviously import redirections
        self._audit_obvious_import_redirections()

        # 5. Backup files (.backup, .bak, etc)
        self._audit_backup_files()

        # 6. Analyze active imports
        self._analyze_active_imports()

        print(f"✅ Found {len(self.findings)} obvious shims/compatibility layers.")
        return self.findings

    def _audit_obvious_legacy_filenames(self) -> None:
        """Find files explicitly named with legacy/deprecated/shim."""
        patterns = ["*legacy*.py", "*deprecated*.py", "*shim*.py"]

        for pattern in patterns:
            for file_path in self.root_path.rglob(pattern):
                if self._should_exclude_file(file_path):
                    continue

                # Skip false positives like "legacy_audit_report"
                if any(skip in str(file_path).lower() for skip in ["report", "audit", "plan", "matrix"]):
                    continue

                keyword = "legacy" if "legacy" in pattern else "deprecated" if "deprecated" in pattern else "shim"
                
                self.findings.append(
                    ShimInfo(
                        file_path=str(file_path),
                        description=f"File explicitly named with '{keyword}' keyword",
                        purpose=f"File explicitly indicating {keyword} status",
                        suggested_action="review_for_migration",
                        risk_level="high",
                        evidence=[f"Filename contains '{keyword}'"],
                    )
                )

    def _audit_actual_deprecation_warnings(self) -> None:
        """Find files with actual warnings.warn() calls."""
        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Look for actual warnings.warn calls
                if "warnings.warn" in content:
                    # Extract the warning message
                    warning_pattern = r"warnings\.warn\s*\(\s*[\"'](.*?)[\"']"
                    warning_matches = re.findall(warning_pattern, content, re.DOTALL)
                    
                    if warning_matches:
                        evidence = [f"Warning: {msg[:100]}..." for msg in warning_matches[:2]]
                        
                        self.findings.append(
                            ShimInfo(
                                file_path=str(file_path),
                                description="Contains actual deprecation warnings",
                                purpose="Issues runtime deprecation warnings",
                                suggested_action="review_for_removal",
                                risk_level="high",
                                evidence=evidence,
                            )
                        )

            except (UnicodeDecodeError, PermissionError):
                continue

    def _audit_explicit_status_markers(self) -> None:
        """Find files with explicit Status: legacy markers."""
        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Look for explicit status markers in module docstrings
                if re.search(r'Status.*legacy', content, re.IGNORECASE):
                    # Extract the status line
                    status_match = re.search(r'(.*Status.*legacy.*)', content, re.IGNORECASE)
                    evidence = [status_match.group(1).strip()] if status_match else ["Status: legacy marker found"]
                    
                    self.findings.append(
                        ShimInfo(
                            file_path=str(file_path),
                            description="Explicitly marked with 'Status: legacy'",
                            purpose="Module explicitly marked as legacy",
                            suggested_action="review_for_migration",
                            risk_level="high",
                            evidence=evidence,
                        )
                    )

            except (UnicodeDecodeError, PermissionError):
                continue

    def _audit_obvious_import_redirections(self) -> None:
        """Find files that are obviously import redirections."""
        for file_path in self._find_all_python_files():
            if self._should_exclude_file(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                lines = [line.strip() for line in content.split("\n") if line.strip()]
                
                # Skip long files - redirections should be short
                if len(lines) > 20:
                    continue

                # Look for files that:
                # 1. Have "import *" statements
                # 2. Have redirection language
                # 3. Are short (< 20 lines)
                
                has_star_import = any("import *" in line for line in lines)
                
                redirection_phrases = [
                    "moved to",
                    "redirect",
                    "shim maintains",
                    "backward compatibility",
                    "import everything from",
                    "import redirected",
                    "new location"
                ]
                
                has_redirection_language = any(
                    phrase in content.lower() for phrase in redirection_phrases
                )

                if has_star_import and has_redirection_language:
                    star_imports = [line for line in lines if "import *" in line]
                    
                    self.findings.append(
                        ShimInfo(
                            file_path=str(file_path),
                            description="Import redirection shim",
                            purpose="Redirects imports to new location",
                            suggested_action="migrate_imports",
                            risk_level="medium",
                            evidence=[
                                f"Star imports: {len(star_imports)}",
                                f"Redirection language found",
                                f"Short file: {len(lines)} lines"
                            ],
                        )
                    )

            except (UnicodeDecodeError, PermissionError):
                continue

    def _audit_backup_files(self) -> None:
        """Find backup files."""
        backup_patterns = ["*.backup", "*.bak", "*.orig"]

        for pattern in backup_patterns:
            for file_path in self.root_path.rglob(pattern):
                if self._should_exclude_file(file_path):
                    continue

                self.findings.append(
                    ShimInfo(
                        file_path=str(file_path),
                        description=f"Backup file ({pattern})",
                        purpose="Backup file that should be cleaned up",
                        suggested_action="remove",
                        risk_level="low",
                        evidence=[f"Backup pattern: {pattern}"],
                    )
                )

    def _analyze_active_imports(self) -> None:
        """Count active imports for each shim."""
        for finding in self.findings:
            if finding.file_path.endswith(".py"):
                import_path = self._file_path_to_import_path(finding.file_path)
                finding.active_imports = self._count_imports_of_module(import_path)

                if finding.active_imports > 0:
                    if finding.risk_level != "high":
                        finding.risk_level = "medium"
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
            if self._should_exclude_file(file_path) or str(file_path) == module_path.replace(".", "/") + ".py":
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

    def _find_all_python_files(self) -> list[Path]:
        """Find all Python files in the repository."""
        return [p for p in self.root_path.rglob("*.py")]

    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from analysis."""
        path_str = str(file_path)
        return any(pattern in path_str for pattern in self.exclude_patterns)

    def generate_report(self, output_file: str = "SHIMS_COMPATIBILITY_AUDIT_FINAL.md") -> None:
        """Generate the final audit report."""
        print(f"📝 Generating final audit report: {output_file}")

        # Sort findings by risk level and active imports
        def sort_key(item):
            risk_priority = {"high": 3, "medium": 2, "low": 1}
            return (risk_priority[item.risk_level], item.active_imports)

        sorted_findings = sorted(self.findings, key=sort_key, reverse=True)

        # Categorize findings
        by_risk = {"high": [], "medium": [], "low": []}
        for finding in sorted_findings:
            by_risk[finding.risk_level].append(finding)

        # Generate report content
        report_lines = [
            "# Shims & Compatibility Layers Audit Report",
            "",
            "## Executive Summary",
            "",
            f"This report identifies **{len(self.findings)} confirmed shims and compatibility layers** in the codebase that require attention. This focused audit only includes files that are definitively shims, import redirections, or legacy compatibility code.",
            "",
            "**Risk Distribution:**",
            f"- 🔴 **High Risk**: {len(by_risk['high'])} items (explicit legacy code, deprecation warnings)",
            f"- 🟡 **Medium Risk**: {len(by_risk['medium'])} items (import redirections)", 
            f"- 🟢 **Low Risk**: {len(by_risk['low'])} items (backup files)",
            "",
            f"**Active Usage**: {len([f for f in self.findings if f.active_imports > 0])} shims are actively imported by other files",
            "",
            "## Detailed Findings",
            "",
        ]

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
                imports_text = f" **[{item.active_imports} imports]**" if item.active_imports > 0 else ""
                report_lines.extend([
                    f"**{i}. {Path(item.file_path).name}**{imports_text}",
                    f"- **File**: `{item.file_path}`",
                    f"- **Description**: {item.description}",
                    f"- **Purpose**: {item.purpose}",
                    f"- **Suggested Action**: {item.suggested_action}",
                ])
                if item.replacement_path:
                    report_lines.append(f"- **Replacement**: `{item.replacement_path}`")
                if item.evidence:
                    report_lines.append(f"- **Evidence**: {'; '.join(item.evidence)}")
                report_lines.append("")

        # Summary and recommendations
        high_risk_count = len(by_risk['high'])
        active_imports_count = len([f for f in self.findings if f.active_imports > 0])
        
        report_lines.extend([
            "## Recommendations",
            "",
            "### Immediate Actions Required",
            "",
        ])
        
        if high_risk_count > 0:
            report_lines.extend([
                f"1. **Review {high_risk_count} high-risk shims** - These are explicitly marked as legacy or deprecated",
                f"2. **Handle {active_imports_count} actively imported shims** - Must update import statements before removal",
                "3. **Remove backup files** - These can be safely deleted",
                "",
            ])

        report_lines.extend([
            "### Suggested Action Priority",
            "",
            "1. **Backup Files** → Safe to remove immediately",
            "2. **Import Redirections** → Update import statements, then remove shim",
            "3. **Legacy Code** → Review, migrate functionality, then remove",
            "4. **Deprecated Code** → Already marked for removal, coordinate timing",
            "",
            "### Risk Mitigation",
            "",
            "- **Test after each shim removal** to ensure no functionality is broken",
            "- **Update import statements before removing shims**",
            "- **Coordinate with team** for files with many active imports",
            "- **Document replacement paths** for future reference",
            "",
            "## Cross-Reference with Existing Work",
            "",
            "This audit complements existing migration reports:",
            "- `LEGACY_AUDIT_REPORT.md` - Broader legacy DDD architecture cleanup",
            "- `STRATEGY_LEGACY_AUDIT_REPORT.md` - Strategy module specific cleanup",  
            "- `DELETION_SAFETY_MATRIX.md` - Safe deletion guidelines",
            "",
            "The shims identified here are in addition to the legacy architecture cleanup already in progress.",
            "",
            "---",
            "",
            "**Generated**: January 2025  ",
            "**Scope**: Confirmed shims and compatibility layers only  ",
            "**Issue**: #492  ",
            "**Tool**: scripts/focused_shim_auditor.py  ",
        ])

        # Write report
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        print(f"✅ Final audit report generated: {output_file}")


def main() -> None:
    """Main entry point."""
    auditor = FocusedShimAuditor()
    findings = auditor.audit_obvious_shims()
    auditor.generate_report()

    print(f"\n📊 Final Audit Summary:")
    print(f"   Confirmed shims: {len(findings)}")
    print(f"   High risk: {len([f for f in findings if f.risk_level == 'high'])}")
    print(f"   Medium risk: {len([f for f in findings if f.risk_level == 'medium'])}")
    print(f"   Low risk: {len([f for f in findings if f.risk_level == 'low'])}")
    print(f"   With active imports: {len([f for f in findings if f.active_imports > 0])}")

    # Show summary of high-risk items
    high_risk = [f for f in findings if f.risk_level == 'high']
    if high_risk:
        print(f"\n🔴 High-risk shims found:")
        for finding in high_risk:
            imports_info = f" ({finding.active_imports} imports)" if finding.active_imports > 0 else ""
            print(f"   - {Path(finding.file_path).name}{imports_info}")


if __name__ == "__main__":
    main()