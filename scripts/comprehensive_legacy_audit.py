#!/usr/bin/env python3
"""Comprehensive Legacy & Deprecation Audit Tool

This script performs an exhaustive audit of the alchemiser-quant codebase to identify:
1. Shims & Compatibility Layers
2. Deprecated Features
3. Archived or Obsolete Code
4. Legacy Files
5. Non-conforming files

Generates a master audit report with risk levels and actionable recommendations.
"""

from __future__ import annotations

import ast
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

@dataclass
class AuditFinding:
    """Represents a single audit finding."""
    file_path: str
    finding_type: str  # "shim", "deprecated", "archive", "legacy"
    description: str
    risk_level: str  # "high", "medium", "low"
    suggested_action: str
    details: dict[str, Any] = field(default_factory=dict)
    line_number: int | None = None

class ComprehensiveLegacyAuditor:
    """Comprehensive auditor for legacy code patterns."""
    
    def __init__(self, root_path: str | Path) -> None:
        self.root_path = Path(root_path)
        self.findings: list[AuditFinding] = []
        
        # Patterns to identify different types of legacy code
        self.shim_patterns = [
            r"import.*warnings",
            r"warnings\.warn.*deprecated",
            r"DeprecationWarning",
            r"This module has moved",
            r"backward compatibility",
            r"compatibility layer",
            r"Import all symbols from the new location",
            r"Import redirected"
        ]
        
        self.deprecated_patterns = [
            r"@deprecated",
            r"# TODO: remove",
            r"# DEPRECATED",
            r"# FIXME: remove",
            r"Status: legacy",
            r"DEPRECATED:",
            r"# Legacy",
            r"marked for removal"
        ]
        
        self.archive_patterns = [
            r"/archived/",
            r"/backup/",
            r"/old/",
            r"/legacy/",
            r"\.backup$",
            r"\.old$",
            r"_backup\.",
            r"_old\.",
            r"_archive\.",
            r"_deprecated\."
        ]
        
        # File extensions to scan
        self.scan_extensions = {'.py', '.yaml', '.yml', '.json', '.md', '.txt', '.sh'}
        
        # Directories to skip
        self.skip_dirs = {
            '.git', '.venv', '__pycache__', '.mypy_cache', '.ruff_cache',
            'node_modules', 'dist', 'build', '.aws-sam'
        }

    def scan_file_for_shims(self, file_path: Path) -> list[AuditFinding]:
        """Scan a file for shim and compatibility layer patterns."""
        findings = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Check for shim patterns
            for i, line in enumerate(lines, 1):
                for pattern in self.shim_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Additional analysis for shims
                        is_shim = self._analyze_shim_content(content, file_path)
                        if is_shim:
                            findings.append(AuditFinding(
                                file_path=str(file_path.relative_to(self.root_path)),
                                finding_type="shim",
                                description=f"Compatibility shim detected: {line.strip()}",
                                risk_level="medium",
                                suggested_action="Migrate imports and remove shim",
                                line_number=i,
                                details={"pattern_matched": pattern, "line_content": line.strip()}
                            ))
                        break
                        
            # Check for star imports from other locations (typical in shims)
            if re.search(r'from .* import \*', content):
                if any(pattern in content.lower() for pattern in ['deprecated', 'moved', 'compatibility']):
                    findings.append(AuditFinding(
                        file_path=str(file_path.relative_to(self.root_path)),
                        finding_type="shim",
                        description="Star import compatibility shim",
                        risk_level="medium",
                        suggested_action="Replace with direct imports and remove shim",
                        details={"star_import": True}
                    ))
                    
        except (UnicodeDecodeError, OSError):
            pass  # Skip binary or unreadable files
            
        return findings

    def scan_file_for_deprecated(self, file_path: Path) -> list[AuditFinding]:
        """Scan a file for deprecated features."""
        findings = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                for pattern in self.deprecated_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        risk_level = self._assess_deprecation_risk(line, content)
                        findings.append(AuditFinding(
                            file_path=str(file_path.relative_to(self.root_path)),
                            finding_type="deprecated",
                            description=f"Deprecated code or comment: {line.strip()}",
                            risk_level=risk_level,
                            suggested_action=self._suggest_deprecation_action(line),
                            line_number=i,
                            details={"pattern_matched": pattern, "line_content": line.strip()}
                        ))
                        break
                        
            # Check for deprecated Python AST patterns
            if file_path.suffix == '.py':
                deprecated_ast_findings = self._scan_ast_for_deprecated(file_path, content)
                findings.extend(deprecated_ast_findings)
                
        except (UnicodeDecodeError, OSError, SyntaxError):
            pass  # Skip binary, unreadable, or malformed files
            
        return findings

    def scan_for_archived_code(self, file_path: Path) -> list[AuditFinding]:
        """Scan for archived, backup, or obsolete code patterns."""
        findings = []
        relative_path = str(file_path.relative_to(self.root_path))
        
        # Check file path patterns
        for pattern in self.archive_patterns:
            if re.search(pattern, relative_path, re.IGNORECASE):
                risk_level = self._assess_archive_risk(file_path)
                findings.append(AuditFinding(
                    file_path=relative_path,
                    finding_type="archive",
                    description=f"Archived/backup file pattern in path: {pattern}",
                    risk_level=risk_level,
                    suggested_action=self._suggest_archive_action(file_path),
                    details={"path_pattern": pattern}
                ))
                break
                
        # Check for backup-like content
        if file_path.suffix in {'.py', '.yaml', '.yml', '.json'}:
            backup_content_findings = self._scan_for_backup_content(file_path)
            findings.extend(backup_content_findings)
            
        return findings

    def scan_for_legacy_patterns(self, file_path: Path) -> list[AuditFinding]:
        """Scan for files that don't conform to current project structure."""
        findings = []
        relative_path = str(file_path.relative_to(self.root_path))
        
        # Check for non-conforming directory structures
        legacy_structure_findings = self._check_legacy_structure(file_path)
        findings.extend(legacy_structure_findings)
        
        # Check for old naming conventions
        naming_findings = self._check_naming_conventions(file_path)
        findings.extend(naming_findings)
        
        # Check for legacy imports
        if file_path.suffix == '.py':
            legacy_import_findings = self._scan_for_legacy_imports(file_path)
            findings.extend(legacy_import_findings)
            
        return findings

    def _analyze_shim_content(self, content: str, file_path: Path) -> bool:
        """Analyze if a file is actually a shim."""
        # Look for typical shim characteristics
        shim_indicators = [
            'warnings.warn',
            'import *',
            'from .* import *',
            'deprecated',
            'moved to',
            'backward compatibility',
            'This module has moved'
        ]
        
        shim_score = sum(1 for indicator in shim_indicators if indicator in content.lower())
        
        # Also check if file is very short (typical of shims)
        line_count = len([line for line in content.split('\n') if line.strip()])
        
        return shim_score >= 2 or (shim_score >= 1 and line_count <= 20)

    def _scan_ast_for_deprecated(self, file_path: Path, content: str) -> list[AuditFinding]:
        """Scan Python AST for deprecated patterns."""
        findings = []
        
        try:
            tree = ast.parse(content)
            
            # Look for deprecated decorators
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name) and 'deprecated' in decorator.id.lower():
                            findings.append(AuditFinding(
                                file_path=str(file_path.relative_to(self.root_path)),
                                finding_type="deprecated",
                                description=f"Function {node.name} has deprecated decorator",
                                risk_level="high",
                                suggested_action="Remove or replace deprecated function",
                                line_number=node.lineno,
                                details={"function_name": node.name, "decorator": decorator.id}
                            ))
                            
        except SyntaxError:
            pass  # Skip files with syntax errors
            
        return findings

    def _scan_for_backup_content(self, file_path: Path) -> list[AuditFinding]:
        """Scan for content that looks like backups."""
        findings = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Look for comments indicating backup status
            backup_comments = [
                'backup copy',
                'original implementation',
                'old version',
                'archived version',
                'backup of'
            ]
            
            for comment in backup_comments:
                if comment in content.lower():
                    findings.append(AuditFinding(
                        file_path=str(file_path.relative_to(self.root_path)),
                        finding_type="archive",
                        description=f"File contains backup-related content: {comment}",
                        risk_level="low",
                        suggested_action="Review and remove if no longer needed",
                        details={"backup_indicator": comment}
                    ))
                    break
                    
        except (UnicodeDecodeError, OSError):
            pass
            
        return findings

    def _check_legacy_structure(self, file_path: Path) -> list[AuditFinding]:
        """Check for legacy directory structure patterns."""
        findings = []
        relative_path = str(file_path.relative_to(self.root_path))
        
        # Based on the copilot instructions, these are legacy patterns
        legacy_structures = [
            'application/',
            'domain/',
            'infrastructure/',
            'interfaces/',
            'services/',
            'utils/'
        ]
        
        for legacy_pattern in legacy_structures:
            if legacy_pattern in relative_path:
                findings.append(AuditFinding(
                    file_path=relative_path,
                    finding_type="legacy",
                    description=f"File in legacy DDD structure: {legacy_pattern}",
                    risk_level="high",
                    suggested_action="Migrate to new modular structure (strategy/portfolio/execution/shared)",
                    details={"legacy_structure": legacy_pattern}
                ))
                break
                
        return findings

    def _check_naming_conventions(self, file_path: Path) -> list[AuditFinding]:
        """Check for old naming conventions."""
        findings = []
        relative_path = str(file_path.relative_to(self.root_path))
        
        # Check for snake_case vs kebab-case mismatches
        old_naming_patterns = [
            r'.*_service\.py$',  # Old service naming
            r'.*_adapter\.py$',  # Old adapter naming
            r'.*_facade\.py$',   # Old facade naming
        ]
        
        for pattern in old_naming_patterns:
            if re.match(pattern, file_path.name) and 'the_alchemiser' in relative_path:
                findings.append(AuditFinding(
                    file_path=relative_path,
                    finding_type="legacy",
                    description=f"File uses old naming convention: {file_path.name}",
                    risk_level="low",
                    suggested_action="Consider renaming to match current conventions",
                    details={"naming_pattern": pattern}
                ))
                break
                
        return findings

    def _scan_for_legacy_imports(self, file_path: Path) -> list[AuditFinding]:
        """Scan for legacy import patterns."""
        findings = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Legacy import patterns based on old DDD structure
            legacy_import_patterns = [
                r'from.*\.application\.',
                r'from.*\.domain\.',
                r'from.*\.infrastructure\.',
                r'from.*\.interfaces\.',
                r'from.*\.services\.',
                r'from.*\.utils\.'
            ]
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                for pattern in legacy_import_patterns:
                    if re.search(pattern, line):
                        findings.append(AuditFinding(
                            file_path=str(file_path.relative_to(self.root_path)),
                            finding_type="legacy",
                            description=f"Legacy import pattern: {line.strip()}",
                            risk_level="medium",
                            suggested_action="Update import to use new modular structure",
                            line_number=i,
                            details={"import_pattern": pattern, "import_line": line.strip()}
                        ))
                        break
                        
        except (UnicodeDecodeError, OSError):
            pass
            
        return findings

    def _assess_deprecation_risk(self, line: str, content: str) -> str:
        """Assess the risk level of a deprecated item."""
        line_lower = line.lower()
        
        if any(word in line_lower for word in ['critical', 'remove immediately', 'breaking']):
            return "high"
        elif any(word in line_lower for word in ['todo', 'fixme', 'status: legacy']):
            return "medium"
        else:
            return "low"

    def _assess_archive_risk(self, file_path: Path) -> str:
        """Assess the risk level of an archived item."""
        relative_path = str(file_path)
        
        if any(pattern in relative_path for pattern in ['/backup/', '.backup']):
            return "low"  # Backup files are usually safe to remove
        elif '/archived/' in relative_path:
            return "medium"  # Archived might have references
        else:
            return "low"

    def _suggest_deprecation_action(self, line: str) -> str:
        """Suggest an action for deprecated code."""
        line_lower = line.lower()
        
        if 'todo: remove' in line_lower:
            return "Remove deprecated code as planned"
        elif 'status: legacy' in line_lower:
            return "Migrate to new modular structure"
        elif 'deprecated' in line_lower:
            return "Replace with modern alternative"
        else:
            return "Review and remove if no longer needed"

    def _suggest_archive_action(self, file_path: Path) -> str:
        """Suggest an action for archived code."""
        relative_path = str(file_path)
        
        if '.backup' in relative_path:
            return "Compare with current version and remove if identical"
        elif '/archived/' in relative_path:
            return "Verify no active imports then remove"
        else:
            return "Review and remove if obsolete"

    def scan_directory(self, directory: Path) -> None:
        """Recursively scan a directory for legacy patterns."""
        for item in directory.iterdir():
            if item.is_dir() and item.name not in self.skip_dirs:
                self.scan_directory(item)
            elif item.is_file() and item.suffix in self.scan_extensions:
                # Scan for all types of findings
                self.findings.extend(self.scan_file_for_shims(item))
                self.findings.extend(self.scan_file_for_deprecated(item))
                self.findings.extend(self.scan_for_archived_code(item))
                self.findings.extend(self.scan_for_legacy_patterns(item))

    def generate_report(self) -> str:
        """Generate a comprehensive audit report."""
        # Group findings by type and risk level
        by_type = {}
        by_risk = {"high": [], "medium": [], "low": []}
        
        for finding in self.findings:
            if finding.finding_type not in by_type:
                by_type[finding.finding_type] = []
            by_type[finding.finding_type].append(finding)
            by_risk[finding.risk_level].append(finding)
        
        # Generate report
        report_lines = [
            "# Comprehensive Legacy & Deprecation Audit Report",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Findings**: {len(self.findings)}",
            "",
            "## Executive Summary",
            "",
            f"This comprehensive audit identified **{len(self.findings)} items** requiring attention:",
            ""
        ]
        
        # Add summary by type
        for finding_type, findings in by_type.items():
            report_lines.append(f"- **{finding_type.title()}**: {len(findings)} items")
        
        report_lines.extend([
            "",
            "## Risk Level Distribution",
            "",
            f"- **HIGH RISK**: {len(by_risk['high'])} items - Require immediate attention",
            f"- **MEDIUM RISK**: {len(by_risk['medium'])} items - Should be addressed soon", 
            f"- **LOW RISK**: {len(by_risk['low'])} items - Can be addressed as time permits",
            "",
            "## Detailed Findings",
            ""
        ])
        
        # Add detailed findings by risk level (high first)
        for risk_level in ["high", "medium", "low"]:
            if by_risk[risk_level]:
                report_lines.extend([
                    f"### {risk_level.upper()} RISK ITEMS ({len(by_risk[risk_level])} items)",
                    ""
                ])
                
                # Group by type within risk level
                risk_by_type = {}
                for finding in by_risk[risk_level]:
                    if finding.finding_type not in risk_by_type:
                        risk_by_type[finding.finding_type] = []
                    risk_by_type[finding.finding_type].append(finding)
                
                for finding_type, findings in risk_by_type.items():
                    report_lines.extend([
                        f"#### {finding_type.title()} Items",
                        "",
                        "| File Path | Description | Suggested Action | Line |",
                        "|-----------|-------------|------------------|------|"
                    ])
                    
                    for finding in findings:
                        line_info = str(finding.line_number) if finding.line_number else "-"
                        report_lines.append(
                            f"| `{finding.file_path}` | {finding.description} | {finding.suggested_action} | {line_info} |"
                        )
                    
                    report_lines.append("")
        
        # Add recommendations
        report_lines.extend([
            "## Recommendations",
            "",
            "### Immediate Actions (High Risk)",
            "1. **Legacy Structure Migration**: Migrate files from legacy DDD structure to new modular structure",
            "2. **Deprecated Function Removal**: Remove functions marked with deprecated decorators", 
            "3. **Import Updates**: Update legacy import paths to new module structure",
            "",
            "### Medium-Term Actions (Medium Risk)",
            "1. **Shim Removal**: Update imports and remove compatibility shims",
            "2. **Legacy Pattern Cleanup**: Replace old naming conventions and patterns",
            "3. **Documentation Updates**: Update all references to old structure",
            "",
            "### Low-Priority Actions (Low Risk)",
            "1. **Backup File Cleanup**: Remove backup files that are no longer needed",
            "2. **Comment Cleanup**: Remove TODO/FIXME comments for completed migrations",
            "3. **Archive Review**: Review archived files for potential removal",
            "",
            "## Implementation Strategy",
            "",
            "1. **Phase 1**: Address all HIGH risk items first",
            "2. **Phase 2**: Tackle MEDIUM risk items in batches",
            "3. **Phase 3**: Clean up LOW risk items as time permits",
            "4. **Testing**: Run full test suite after each phase",
            "5. **Documentation**: Update all documentation to reflect changes",
            "",
            f"---",
            f"*Report generated by comprehensive_legacy_audit.py on {datetime.now().strftime('%Y-%m-%d')}*"
        ])
        
        return "\n".join(report_lines)

    def run_audit(self) -> None:
        """Run the complete audit."""
        print("🔍 Starting comprehensive legacy & deprecation audit...")
        print(f"📂 Scanning directory: {self.root_path}")
        
        # Scan the entire the_alchemiser directory
        alchemiser_path = self.root_path / "the_alchemiser"
        if alchemiser_path.exists():
            self.scan_directory(alchemiser_path)
        
        print(f"✅ Audit complete! Found {len(self.findings)} items")
        print(f"📊 Risk distribution:")
        
        risk_counts = {"high": 0, "medium": 0, "low": 0}
        for finding in self.findings:
            risk_counts[finding.risk_level] += 1
            
        for risk, count in risk_counts.items():
            print(f"   - {risk.upper()}: {count} items")

def main() -> None:
    """Main entry point."""
    import sys
    
    root_path = sys.argv[1] if len(sys.argv) > 1 else "."
    auditor = ComprehensiveLegacyAuditor(root_path)
    
    auditor.run_audit()
    
    # Generate and save report
    report = auditor.generate_report()
    report_path = Path(root_path) / "COMPREHENSIVE_LEGACY_AUDIT_REPORT.md"
    
    report_path.write_text(report, encoding='utf-8')
    print(f"📄 Report saved to: {report_path}")
    
    # Also save raw findings as JSON for further analysis
    json_path = Path(root_path) / "legacy_audit_findings.json"
    findings_data = [
        {
            "file_path": f.file_path,
            "finding_type": f.finding_type,
            "description": f.description,
            "risk_level": f.risk_level,
            "suggested_action": f.suggested_action,
            "line_number": f.line_number,
            "details": f.details
        }
        for f in auditor.findings
    ]
    
    json_path.write_text(json.dumps(findings_data, indent=2), encoding='utf-8')
    print(f"📊 Raw findings saved to: {json_path}")

if __name__ == "__main__":
    main()