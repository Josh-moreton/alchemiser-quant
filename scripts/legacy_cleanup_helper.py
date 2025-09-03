#!/usr/bin/env python3
"""Legacy Cleanup Helper Script

This script provides utilities to help with legacy cleanup based on the comprehensive audit.
It focuses on safe, low-risk cleanup operations that can be automated.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

class LegacyCleanupHelper:
    """Helper class for legacy cleanup operations."""
    
    def __init__(self, root_path: str | Path) -> None:
        self.root_path = Path(root_path)
        
    def load_audit_findings(self) -> list[dict[str, Any]]:
        """Load the audit findings from JSON."""
        findings_file = self.root_path / "legacy_audit_findings.json"
        if not findings_file.exists():
            raise FileNotFoundError("Run comprehensive_legacy_audit.py first to generate findings")
        
        with findings_file.open() as f:
            return json.load(f)
    
    def get_backup_files(self, findings: list[dict[str, Any]]) -> list[str]:
        """Get list of backup files that are safe to remove."""
        backup_files = []
        
        for finding in findings:
            file_path = finding["file_path"]
            if (finding["finding_type"] == "archive" and 
                finding["risk_level"] == "low" and
                any(pattern in file_path for pattern in [".backup", "_backup", "/backup/"])):
                backup_files.append(file_path)
        
        return backup_files
    
    def get_deprecated_comments(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Get list of deprecated comments that can be cleaned up."""
        deprecated_comments = []
        
        for finding in findings:
            if (finding["finding_type"] == "deprecated" and 
                finding["risk_level"] == "low" and
                finding["line_number"] is not None):
                
                # Filter for simple comment cleanup
                description = finding["description"].lower()
                if any(pattern in description for pattern in [
                    "legacy", "deprecated", "todo", "fixme", "old"
                ]):
                    deprecated_comments.append(finding)
        
        return deprecated_comments
    
    def get_shim_files(self, findings: list[dict[str, Any]]) -> list[str]:
        """Get list of shim files with their targets."""
        shim_files = []
        
        for finding in findings:
            if finding["finding_type"] == "shim":
                file_path = finding["file_path"]
                # Only include files that are clearly shims
                if any(pattern in finding["description"] for pattern in [
                    "DEPRECATED: This module has moved",
                    "backward compatibility"
                ]):
                    shim_files.append(file_path)
        
        return shim_files
    
    def analyze_import_dependencies(self, shim_file: str) -> list[str]:
        """Analyze what imports from a shim file."""
        shim_path = self.root_path / shim_file
        if not shim_path.exists():
            return []
        
        importing_files = []
        
        # Search for imports of this file
        module_path = shim_file.replace("/", ".").replace(".py", "")
        search_patterns = [
            f"from {module_path} import",
            f"import {module_path}",
        ]
        
        for py_file in self.root_path.rglob("*.py"):
            if py_file == shim_path:
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                for pattern in search_patterns:
                    if pattern in content:
                        importing_files.append(str(py_file.relative_to(self.root_path)))
                        break
            except (UnicodeDecodeError, OSError):
                continue
        
        return importing_files
    
    def generate_cleanup_plan(self) -> str:
        """Generate a cleanup plan based on audit findings."""
        findings = self.load_audit_findings()
        
        # Categorize findings
        backup_files = self.get_backup_files(findings)
        deprecated_comments = self.get_deprecated_comments(findings)
        shim_files = self.get_shim_files(findings)
        
        plan_lines = [
            "# Legacy Cleanup Plan",
            "",
            f"Based on comprehensive audit findings, this plan addresses {len(findings)} total findings.",
            "",
            "## Phase 1: Safe Deletions (Low Risk)",
            "",
            "### Backup Files to Remove",
            f"Found {len(backup_files)} backup files safe for removal:",
            ""
        ]
        
        for backup_file in backup_files:
            plan_lines.append(f"- `{backup_file}`")
        
        plan_lines.extend([
            "",
            "### Deprecated Comments to Clean",
            f"Found {len(deprecated_comments)} deprecated comments to review:",
            ""
        ])
        
        for comment in deprecated_comments[:10]:  # Show first 10
            file_path = comment["file_path"]
            line_num = comment["line_number"]
            description = comment["description"]
            plan_lines.append(f"- `{file_path}:{line_num}` - {description}")
        
        if len(deprecated_comments) > 10:
            plan_lines.append(f"- ... and {len(deprecated_comments) - 10} more")
        
        plan_lines.extend([
            "",
            "## Phase 2: Shim Analysis and Removal",
            "",
            "### Compatibility Shims Requiring Import Migration",
            f"Found {len(shim_files)} shim files requiring import updates:",
            ""
        ])
        
        for shim_file in shim_files[:10]:  # Show first 10
            importers = self.analyze_import_dependencies(shim_file)
            plan_lines.append(f"- `{shim_file}` - {len(importers)} importing files")
            for importer in importers[:3]:  # Show first 3 importers
                plan_lines.append(f"  - `{importer}`")
            if len(importers) > 3:
                plan_lines.append(f"  - ... and {len(importers) - 3} more")
        
        if len(shim_files) > 10:
            plan_lines.append(f"- ... and {len(shim_files) - 10} more shims")
        
        plan_lines.extend([
            "",
            "## Phase 3: Legacy Structure Migration",
            "",
            "### High Priority: utils/ and services/ directories",
            "These directories should be migrated to the new modular structure:",
            ""
        ])
        
        # Find legacy structure files
        legacy_structure_files = []
        for finding in findings:
            if (finding["finding_type"] == "legacy" and 
                finding["risk_level"] == "high" and
                "legacy DDD structure" in finding["description"]):
                legacy_structure_files.append(finding["file_path"])
        
        # Group by directory
        legacy_dirs = {}
        for file_path in legacy_structure_files:
            if "/utils/" in file_path:
                dir_key = "utils/"
            elif "/services/" in file_path:
                dir_key = "services/"
            else:
                dir_key = "other"
                
            if dir_key not in legacy_dirs:
                legacy_dirs[dir_key] = []
            legacy_dirs[dir_key].append(file_path)
        
        for dir_name, files in legacy_dirs.items():
            plan_lines.extend([
                f"#### {dir_name} ({len(files)} files)",
                ""
            ])
            for file_path in files[:5]:  # Show first 5
                plan_lines.append(f"- `{file_path}`")
            if len(files) > 5:
                plan_lines.append(f"- ... and {len(files) - 5} more files")
            plan_lines.append("")
        
        plan_lines.extend([
            "## Recommended Implementation Order",
            "",
            "1. **Start with backup file removal** (zero risk)",
            "2. **Clean deprecated comments** (documentation cleanup)",
            "3. **Analyze shim dependencies** (prepare for import migration)",
            "4. **Migrate legacy structure files** (requires careful planning)",
            "5. **Remove shims after import migration** (final cleanup)",
            "",
            "## Safety Recommendations",
            "",
            "- Always test after each phase",
            "- Use version control for easy rollback",
            "- Consider creating a staging branch for cleanup work",
            "- Run import-linter to validate module boundaries",
            "- Update documentation as you go",
            "",
            "---",
            "*Generated by legacy_cleanup_helper.py*"
        ])
        
        return "\n".join(plan_lines)

def main() -> None:
    """Main entry point."""
    import sys
    
    root_path = sys.argv[1] if len(sys.argv) > 1 else "."
    helper = LegacyCleanupHelper(root_path)
    
    try:
        plan = helper.generate_cleanup_plan()
        
        plan_path = Path(root_path) / "LEGACY_CLEANUP_PLAN.md"
        plan_path.write_text(plan, encoding='utf-8')
        
        print(f"✅ Cleanup plan generated: {plan_path}")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Run comprehensive_legacy_audit.py first to generate audit findings.")
        sys.exit(1)

if __name__ == "__main__":
    main()