#!/usr/bin/env python3
"""Business Unit: shared | Status: current

Comprehensive Legacy & Deprecation Audit for The Alchemiser Quantitative Trading System.

This script performs a complete audit of the codebase to identify:
1. Shims & Compatibility Layers
2. Deprecated Features
3. Archived or Obsolete Code
4. Legacy Files
5. Non-conforming files

Consolidates findings from all previous specialized audits and provides
a master report with actionable recommendations.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LegacyItem:
    """Information about a legacy, deprecated, or problematic item."""

    file_path: str
    category: str  # "shim", "deprecated", "archive", "legacy", "non_conforming"
    description: str
    risk_level: str  # "high", "medium", "low"
    suggested_action: str
    evidence: list[str] = field(default_factory=list)
    active_imports: int = 0
    replacement_path: str | None = None
    dependencies: list[str] = field(default_factory=list)


class ComprehensiveLegacyAuditor:
    """Comprehensive auditor for all legacy and deprecated items."""

    def __init__(self, root_path: str = ".") -> None:
        """Initialize the auditor."""
        self.root_path = Path(root_path)
        self.findings: list[LegacyItem] = []
        self.exclude_patterns = [
            ".venv",
            "__pycache__",
            ".git",
            ".aws-sam",
            "node_modules",
        ]

    def run_comprehensive_audit(self) -> list[LegacyItem]:
        """Run complete audit across all categories."""
        print("🔍 Starting comprehensive legacy & deprecation audit...")
        
        # Load existing audit findings
        self._load_existing_audit_findings()
        
        # Find additional items not covered by existing audits
        self._audit_build_artifacts()
        self._audit_configuration_files()
        self._audit_scripts_and_utilities()
        self._audit_documentation_legacy()
        self._audit_vendor_code()
        self._audit_naming_conventions()
        
        # Enhanced audits based on deep analysis
        self._audit_deprecated_code_markers()
        self._audit_legacy_imports()
        self._audit_status_legacy_markers()
        
        print(f"✅ Audit complete. Found {len(self.findings)} total items.")
        return self.findings

    def _load_existing_audit_findings(self) -> None:
        """Load and consolidate findings from existing audit reports."""
        print("📋 Loading existing audit findings...")
        
        # Load shims audit findings
        self._load_shims_findings()
        
        # Load legacy DDD architecture findings
        self._load_legacy_ddd_findings()
        
        # Load strategy legacy findings
        self._load_strategy_legacy_findings()

    def _load_shims_findings(self) -> None:
        """Load findings from shims audit reports."""
        shims_summary_path = self.root_path / "SHIMS_AUDIT_SUMMARY.md"
        if shims_summary_path.exists():
            # Parse key shim findings from existing report
            content = shims_summary_path.read_text()
            
            # Extract high-risk shims mentioned in summary
            if "symbol_legacy.py" in content:
                self.findings.append(LegacyItem(
                    file_path="the_alchemiser/shared/types/symbol_legacy.py",
                    category="shim",
                    description="Legacy symbol implementation with active imports",
                    risk_level="high",
                    suggested_action="migrate_imports_then_remove",
                    evidence=["Explicitly named 'legacy'", "Active imports: 7"],
                    active_imports=7
                ))
            
            if "legacy_position_manager.py" in content:
                self.findings.append(LegacyItem(
                    file_path="the_alchemiser/portfolio/positions/legacy_position_manager.py",
                    category="shim",
                    description="Legacy position manager with active imports",
                    risk_level="high",
                    suggested_action="migrate_imports_then_remove",
                    evidence=["Explicitly named 'legacy'", "Active imports: 1"],
                    active_imports=1
                ))

    def _load_legacy_ddd_findings(self) -> None:
        """Load findings from legacy DDD architecture audit."""
        legacy_audit_path = self.root_path / "LEGACY_AUDIT_REPORT.md"
        if legacy_audit_path.exists():
            content = legacy_audit_path.read_text()
            
            # Extract key statistics
            if "Files remaining: 33" in content:
                self.findings.append(LegacyItem(
                    file_path="legacy_ddd_architecture",
                    category="archive",
                    description="33 remaining legacy DDD architecture files",
                    risk_level="medium",
                    suggested_action="complete_migration",
                    evidence=["Legacy DDD architecture cleanup 86% complete"]
                ))

    def _load_strategy_legacy_findings(self) -> None:
        """Load findings from strategy module legacy audit."""
        strategy_audit_path = self.root_path / "STRATEGY_LEGACY_AUDIT_REPORT.md"
        if strategy_audit_path.exists():
            content = strategy_audit_path.read_text()
            
            # Extract remaining items
            if "Status.*legacy" in content:
                for file_path in self._find_all_python_files():
                    if "strategy" in str(file_path):
                        file_content = self._safe_read_file(file_path)
                        if file_content and "Status.*legacy" in file_content:
                            self.findings.append(LegacyItem(
                                file_path=str(file_path),
                                category="deprecated",
                                description="Strategy file marked with legacy status",
                                risk_level="medium",
                                suggested_action="review_for_migration",
                                evidence=["Status: legacy marker found"]
                            ))

    def _audit_build_artifacts(self) -> None:
        """Find build artifacts and cache files."""
        print("🔧 Auditing build artifacts...")
        
        artifact_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            "**/.mypy_cache",
            "**/.pytest_cache",
            "**/dist",
            "**/build",
            "**/*.egg-info",
        ]
        
        for pattern in artifact_patterns:
            for path in self.root_path.rglob(pattern):
                if self._should_exclude_path(path):
                    continue
                    
                self.findings.append(LegacyItem(
                    file_path=str(path),
                    category="archive",
                    description="Build artifact or cache directory",
                    risk_level="low",
                    suggested_action="safe_to_delete",
                    evidence=[f"Matches pattern: {pattern}"]
                ))

    def _audit_configuration_files(self) -> None:
        """Find old or redundant configuration files."""
        print("⚙️ Auditing configuration files...")
        
        old_config_patterns = [
            "*.old",
            "*.backup",
            "*.bak",
            "*~",
            "*.orig",
            ".DS_Store",
        ]
        
        for pattern in old_config_patterns:
            for path in self.root_path.rglob(pattern):
                if self._should_exclude_path(path):
                    continue
                    
                self.findings.append(LegacyItem(
                    file_path=str(path),
                    category="archive",
                    description="Backup or temporary file",
                    risk_level="low",
                    suggested_action="safe_to_delete",
                    evidence=[f"Backup file pattern: {pattern}"]
                ))

    def _audit_scripts_and_utilities(self) -> None:
        """Audit scripts directory for deprecated utilities."""
        print("📜 Auditing scripts and utilities...")
        
        scripts_dir = self.root_path / "scripts"
        if scripts_dir.exists():
            for script_path in scripts_dir.iterdir():
                if script_path.is_file() and script_path.suffix == ".py":
                    content = self._safe_read_file(script_path)
                    if content:
                        # Check for deprecated or one-time scripts
                        if any(keyword in content.lower() for keyword in [
                            "legacy", "deprecated", "remove", "cleanup", "migration"
                        ]):
                            risk_level = "medium" if "legacy" in script_path.name else "low"
                            self.findings.append(LegacyItem(
                                file_path=str(script_path),
                                category="legacy",
                                description="Utility script for legacy/migration tasks",
                                risk_level=risk_level,
                                suggested_action="review_for_removal",
                                evidence=["Contains legacy/migration keywords"]
                            ))

    def _audit_documentation_legacy(self) -> None:
        """Find outdated documentation and reports."""
        print("📚 Auditing documentation for legacy items...")
        
        migration_report_patterns = [
            "BATCH_*_MIGRATION_*.md",
            "*_AUDIT_REPORT.md",
            "*_MIGRATION_*.md",
        ]
        
        for pattern in migration_report_patterns:
            for path in self.root_path.glob(pattern):
                if "COMPREHENSIVE" not in path.name:  # Don't flag our new report
                    self.findings.append(LegacyItem(
                        file_path=str(path),
                        category="archive",
                        description="Migration or audit report documentation",
                        risk_level="low",
                        suggested_action="archive_or_remove",
                        evidence=["Historical migration/audit documentation"]
                    ))

    def _audit_vendor_code(self) -> None:
        """Check for vendor or third-party code that might be outdated."""
        print("📦 Auditing vendor and third-party code...")
        
        # Look for vendor directories or old dependency management
        vendor_patterns = [
            "**/vendor",
            "**/third_party", 
            "**/lib",
            "**/libs",
        ]
        
        for pattern in vendor_patterns:
            for path in self.root_path.rglob(pattern):
                if path.is_dir() and not self._should_exclude_path(path):
                    self.findings.append(LegacyItem(
                        file_path=str(path),
                        category="legacy",
                        description="Potential vendor or third-party code directory",
                        risk_level="medium",
                        suggested_action="review_dependencies",
                        evidence=[f"Vendor directory pattern: {pattern}"]
                    ))

    def _audit_naming_conventions(self) -> None:
        """Find files not conforming to current naming conventions."""
        print("📝 Auditing naming conventions...")
        
        # Check for non-snake_case Python files
        for py_file in self._find_all_python_files():
            if self._should_exclude_path(py_file):
                continue
                
            filename = py_file.stem
            
            # Check naming conventions
            if not self._follows_python_naming_convention(filename):
                self.findings.append(LegacyItem(
                    file_path=str(py_file),
                    category="non_conforming",
                    description="File name doesn't follow Python naming conventions",
                    risk_level="low",
                    suggested_action="consider_rename",
                    evidence=["Non-snake_case filename"]
                ))

    def _find_all_python_files(self) -> list[Path]:
        """Find all Python files in the repository."""
        return list(self.root_path.rglob("*.py"))

    def _should_exclude_path(self, path: Path) -> bool:
        """Check if path should be excluded from audit."""
        path_str = str(path)
        return any(pattern in path_str for pattern in self.exclude_patterns)

    def _safe_read_file(self, file_path: Path) -> str | None:
        """Safely read file content."""
        try:
            return file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError, FileNotFoundError):
            return None

    def _follows_python_naming_convention(self, filename: str) -> bool:
        """Check if filename follows Python naming conventions."""
        # Allow common patterns
        if filename in ["__init__", "__main__", "conftest"]:
            return True
            
        # Check for snake_case
        return re.match(r"^[a-z][a-z0-9_]*$", filename) is not None

    def _audit_deprecated_code_markers(self) -> None:
        """Find files with explicit deprecation markers."""
        print("⚠️ Auditing for deprecation markers...")
        
        deprecation_patterns = [
            r"DEPRECATED",
            r"TODO.*remove",
            r"@deprecated",
            r"warnings\.warn.*DeprecationWarning",
        ]
        
        for py_file in self._find_all_python_files():
            if self._should_exclude_path(py_file):
                continue
                
            content = self._safe_read_file(py_file)
            if not content:
                continue
                
            found_patterns = []
            for pattern in deprecation_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found_patterns.append(pattern)
            
            if found_patterns:
                self.findings.append(LegacyItem(
                    file_path=str(py_file),
                    category="deprecated",
                    description="Contains explicit deprecation markers",
                    risk_level="high",
                    suggested_action="review_for_removal",
                    evidence=found_patterns
                ))

    def _audit_legacy_imports(self) -> None:
        """Find files importing from legacy modules."""
        print("📥 Auditing legacy import patterns...")
        
        legacy_import_patterns = [
            r"import.*legacy",
            r"from.*legacy.*import",
            r"from.*deprecated.*import",
        ]
        
        for py_file in self._find_all_python_files():
            if self._should_exclude_path(py_file):
                continue
                
            content = self._safe_read_file(py_file)
            if not content:
                continue
                
            found_imports = []
            for pattern in legacy_import_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                found_imports.extend(matches)
            
            if found_imports:
                self.findings.append(LegacyItem(
                    file_path=str(py_file),
                    category="deprecated",
                    description="Imports from legacy or deprecated modules",
                    risk_level="medium",
                    suggested_action="update_imports",
                    evidence=found_imports[:5]  # First 5 matches
                ))

    def _audit_status_legacy_markers(self) -> None:
        """Find files explicitly marked with 'Status: legacy'."""
        print("📋 Auditing Status: legacy markers...")
        
        for py_file in self._find_all_python_files():
            if self._should_exclude_path(py_file):
                continue
                
            content = self._safe_read_file(py_file)
            if not content:
                continue
                
            if re.search(r"Status.*legacy", content, re.IGNORECASE):
                # Extract the status line for evidence
                status_match = re.search(r"(.{0,50}Status.*legacy.{0,50})", content, re.IGNORECASE)
                evidence = [status_match.group(1).strip()] if status_match else ["Status: legacy marker found"]
                
                self.findings.append(LegacyItem(
                    file_path=str(py_file),
                    category="deprecated",
                    description="Explicitly marked with 'Status: legacy'",
                    risk_level="high",
                    suggested_action="review_for_migration",
                    evidence=evidence
                ))

    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive audit report."""
        findings_by_category = {}
        for finding in self.findings:
            category = finding.category
            if category not in findings_by_category:
                findings_by_category[category] = []
            findings_by_category[category].append(finding)

        # Sort by risk level and category
        risk_order = {"high": 0, "medium": 1, "low": 2}
        for category in findings_by_category:
            findings_by_category[category].sort(
                key=lambda x: (risk_order.get(x.risk_level, 3), x.file_path)
            )

        report = self._generate_report_content(findings_by_category)
        return report

    def _generate_report_content(self, findings_by_category: dict[str, list[LegacyItem]]) -> str:
        """Generate the actual report content."""
        total_findings = sum(len(items) for items in findings_by_category.values())
        high_risk = sum(1 for finding in self.findings if finding.risk_level == "high")
        medium_risk = sum(1 for finding in self.findings if finding.risk_level == "medium")
        low_risk = sum(1 for finding in self.findings if finding.risk_level == "low")

        report = f"""# Comprehensive Legacy & Deprecation Audit Report

**Issue**: #482 - Comprehensive Legacy & Deprecation Audit  
**Generated**: January 2025  
**Status**: Complete  

## Executive Summary

This comprehensive audit consolidates ALL legacy, deprecated, archived, and non-conforming items across the entire codebase. The audit covers shims, compatibility layers, deprecated features, archived code, legacy files, build artifacts, and naming convention violations.

**Total Items Found**: {total_findings}

## Risk Distribution

- 🔴 **High Risk**: {high_risk} items - Require immediate attention before removal
- 🟡 **Medium Risk**: {medium_risk} items - Need review and planning
- 🟢 **Low Risk**: {low_risk} items - Generally safe to clean up

## Summary by Category

"""

        for category, items in findings_by_category.items():
            report += f"### {category.title()} ({len(items)} items)\n\n"
            
            for item in items[:10]:  # Show first 10 items per category
                risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}[item.risk_level]
                imports_info = f" ({item.active_imports} imports)" if item.active_imports > 0 else ""
                report += f"- {risk_emoji} `{item.file_path}`{imports_info} - {item.description}\n"
            
            if len(items) > 10:
                report += f"- ... and {len(items) - 10} more items\n"
            
            report += "\n"

        report += """## Detailed Recommendations

### Phase 1: Immediate Actions (Low Risk)
1. **Remove build artifacts** - Cache and build directories
2. **Delete backup files** - .backup, .old, .bak files
3. **Clean up migration reports** - Historical audit documentation

### Phase 2: Import Migration (Medium Risk)
1. **Update import statements** for actively used shims
2. **Test after each change** to ensure functionality
3. **Focus on high-usage items first** (more active imports)

### Phase 3: Legacy Code Review (High Risk)
1. **Review legacy status files** - Strategy module items marked as legacy
2. **Migrate or remove shims** - symbol_legacy.py, legacy_position_manager.py
3. **Complete DDD architecture cleanup** - Remaining 33 legacy architecture files

### Phase 4: Code Quality Improvements
1. **Review naming conventions** - Non-snake_case files
2. **Update configuration** - Old or redundant config files
3. **Clean up scripts** - Remove one-time migration utilities

## Cross-Reference with Existing Work

This audit consolidates findings from:
- **LEGACY_AUDIT_REPORT.md** - DDD architecture cleanup (307 files processed)
- **SHIMS_AUDIT_SUMMARY.md** - Shims and compatibility layers (38 items)
- **STRATEGY_LEGACY_AUDIT_REPORT.md** - Strategy module cleanup (23 files)
- **REFINED_SHIMS_AUDIT_REPORT.md** - Detailed shim analysis (178 items)

## Implementation Guidelines

### Safety Rules
- ⚠️ **Never remove files with active imports without migration**
- ✅ **Test after each deletion or change**
- 📋 **Update import statements before removing shims**
- 👥 **Coordinate with team for high-usage items**

### Cleanup Priority
1. Build artifacts and backup files (safe)
2. Historical documentation (low impact)
3. Import redirections (requires testing)
4. Legacy business logic (requires analysis)

## Success Metrics

### Completion Targets
- [ ] Remove all build artifacts and cache directories
- [ ] Delete all backup and temporary files
- [ ] Migrate or remove all high-risk shims
- [ ] Complete legacy DDD architecture cleanup
- [ ] Update naming conventions for consistency

### Quality Goals
- Clear modular architecture boundaries
- No legacy import paths remaining
- Consistent naming conventions
- Minimal technical debt

---

**Generated by**: scripts/comprehensive_legacy_auditor.py  
**Scope**: Complete codebase audit  
**Next Steps**: Execute cleanup phases in order of risk level  
"""

        return report


def main() -> None:
    """Run comprehensive legacy audit and generate report."""
    auditor = ComprehensiveLegacyAuditor()
    findings = auditor.run_comprehensive_audit()
    
    # Generate master report
    report = auditor.generate_comprehensive_report()
    
    # Save report
    report_path = Path("COMPREHENSIVE_LEGACY_AUDIT_REPORT.md")
    report_path.write_text(report)
    
    print(f"📄 Comprehensive audit report saved to: {report_path}")
    print(f"📊 Total findings: {len(findings)}")
    
    # Save detailed findings as JSON for further analysis
    findings_data = [
        {
            "file_path": f.file_path,
            "category": f.category,
            "description": f.description,
            "risk_level": f.risk_level,
            "suggested_action": f.suggested_action,
            "evidence": f.evidence,
            "active_imports": f.active_imports,
            "replacement_path": f.replacement_path,
            "dependencies": f.dependencies,
        }
        for f in findings
    ]
    
    json_path = Path("comprehensive_legacy_audit_findings.json")
    json_path.write_text(json.dumps(findings_data, indent=2))
    print(f"📋 Detailed findings saved to: {json_path}")


if __name__ == "__main__":
    main()