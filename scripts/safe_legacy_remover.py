#!/usr/bin/env python3
"""Safe Legacy File Remover

This script performs the safest legacy cleanup operations based on the comprehensive audit.
It only removes files that are confirmed to be backup copies or truly obsolete.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

class SafeLegacyRemover:
    """Safe removal of legacy files with minimal risk."""
    
    def __init__(self, root_path: str | Path, dry_run: bool = True) -> None:
        self.root_path = Path(root_path)
        self.dry_run = dry_run
        self.removed_files: list[str] = []
    
    def load_audit_findings(self) -> list[dict[str, Any]]:
        """Load the audit findings from JSON."""
        findings_file = self.root_path / "legacy_audit_findings.json"
        if not findings_file.exists():
            raise FileNotFoundError("Run comprehensive_legacy_audit.py first to generate findings")
        
        with findings_file.open() as f:
            return json.load(f)
    
    def get_safe_backup_files(self, findings: list[dict[str, Any]]) -> list[str]:
        """Get backup files that are definitely safe to remove."""
        safe_files = []
        
        # First check findings from audit
        for finding in findings:
            file_path = finding["file_path"]
            
            # Only consider files with .backup extension (safest)
            if (finding["finding_type"] == "archive" and 
                finding["risk_level"] == "low" and
                file_path.endswith(".backup")):
                
                # Double-check the file exists and looks like a backup
                full_path = self.root_path / file_path
                if full_path.exists() and self._is_safe_backup(full_path):
                    safe_files.append(file_path)
        
        # Also manually check for .backup files that might not be in findings
        for backup_file in self.root_path.rglob("*.backup"):
            relative_path = str(backup_file.relative_to(self.root_path))
            if relative_path not in safe_files and self._is_safe_backup(backup_file):
                safe_files.append(relative_path)
        
        return safe_files
    
    def _is_safe_backup(self, backup_path: Path) -> bool:
        """Verify this is actually a safe backup file."""
        # Check if there's a corresponding non-backup file
        original_path = backup_path.with_suffix(backup_path.suffix.replace('.backup', ''))
        
        if not original_path.exists():
            # No original file, might not be safe
            return False
            
        # Check if files are similar size (indicating they might be copies)
        try:
            backup_size = backup_path.stat().st_size
            original_size = original_path.stat().st_size
            
            # If backup is much larger or much smaller, might not be a simple backup
            if backup_size == 0 or abs(backup_size - original_size) > min(backup_size, original_size) * 0.5:
                return False
                
            return True
            
        except OSError:
            return False
    
    def remove_backup_files(self) -> None:
        """Remove safe backup files."""
        findings = self.load_audit_findings()
        safe_backups = self.get_safe_backup_files(findings)
        
        print(f"🔍 Found {len(safe_backups)} safe backup files to remove")
        
        for backup_file in safe_backups:
            backup_path = self.root_path / backup_file
            
            if self.dry_run:
                print(f"  [DRY RUN] Would remove: {backup_file}")
            else:
                try:
                    backup_path.unlink()
                    self.removed_files.append(backup_file)
                    print(f"  ✅ Removed: {backup_file}")
                except OSError as e:
                    print(f"  ❌ Failed to remove {backup_file}: {e}")
    
    def clean_empty_directories(self) -> None:
        """Remove empty directories that might be left after file removal."""
        if self.dry_run:
            print("  [DRY RUN] Would clean empty directories")
            return
            
        # Look for empty directories in common legacy locations
        legacy_dirs = [
            "the_alchemiser/execution/strategies",
            "the_alchemiser/portfolio/analytics", 
            "the_alchemiser/portfolio/rebalancing"
        ]
        
        for dir_path in legacy_dirs:
            full_dir_path = self.root_path / dir_path
            if full_dir_path.exists() and full_dir_path.is_dir():
                try:
                    # Only remove if truly empty
                    if not any(full_dir_path.iterdir()):
                        full_dir_path.rmdir()
                        print(f"  ✅ Removed empty directory: {dir_path}")
                except OSError:
                    pass  # Directory not empty or other issue
    
    def generate_removal_report(self) -> str:
        """Generate a report of what was removed."""
        if not self.removed_files:
            return "No files were removed in this run."
        
        report_lines = [
            "# Safe Legacy File Removal Report",
            "",
            f"**Files Removed**: {len(self.removed_files)}",
            f"**Date**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Removed Files",
            ""
        ]
        
        for file_path in self.removed_files:
            report_lines.append(f"- `{file_path}`")
        
        report_lines.extend([
            "",
            "## Safety Notes",
            "",
            "- All removed files were backup copies with .backup extension",
            "- Original files still exist for all removed backups",
            "- File sizes were verified to be reasonable",
            "- Changes are tracked in version control for easy rollback",
            "",
            "## Next Steps",
            "",
            "1. Run tests to verify nothing is broken",
            "2. Review the comprehensive audit report for next cleanup phase",
            "3. Consider removing compatibility shims after import migration",
            "",
            "---",
            "*Generated by safe_legacy_remover.py*"
        ])
        
        return "\n".join(report_lines)

def main() -> None:
    """Main entry point."""
    import sys
    
    # Check if --execute flag is provided
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("🔍 Running in DRY RUN mode. Use --execute to actually remove files.")
    else:
        print("⚠️  EXECUTE mode: Files will be permanently removed!")
        
    root_path = "."
    remover = SafeLegacyRemover(root_path, dry_run=dry_run)
    
    try:
        remover.remove_backup_files()
        
        if not dry_run:
            remover.clean_empty_directories()
            
            # Generate removal report
            report = remover.generate_removal_report()
            report_path = Path(root_path) / "SAFE_REMOVAL_REPORT.md"
            report_path.write_text(report, encoding='utf-8')
            print(f"📄 Removal report saved: {report_path}")
        
        print("\n✅ Safe legacy cleanup complete!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Run comprehensive_legacy_audit.py first to generate audit findings.")
        sys.exit(1)

if __name__ == "__main__":
    main()