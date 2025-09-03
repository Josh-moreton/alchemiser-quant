#!/usr/bin/env python3
"""Business Unit: shared | Status: current

Legacy audit verification script.

This script validates the findings from the comprehensive legacy audit
and provides quick verification of cleanup progress.
"""

from __future__ import annotations

from pathlib import Path


def verify_audit_findings() -> None:
    """Verify key findings from the legacy audit."""
    print("🔍 Verifying comprehensive legacy audit findings...\n")
    
    # Check for key legacy files
    legacy_files = [
        "the_alchemiser/shared/types/symbol_legacy.py",
        "the_alchemiser/portfolio/positions/legacy_position_manager.py",
    ]
    
    print("🎯 High Priority Legacy Files:")
    for file_path in legacy_files:
        path = Path(file_path)
        status = "✅ EXISTS" if path.exists() else "❌ NOT FOUND"
        print(f"  {status}: {file_path}")
    
    print()
    
    # Check for build artifacts
    cache_dirs = list(Path(".").rglob("__pycache__"))
    print(f"🗂️ Build Artifacts: {len(cache_dirs)} __pycache__ directories found")
    
    # Check for backup files
    backup_files = list(Path(".").glob("*.backup")) + list(Path(".").glob("*.old"))
    print(f"💾 Backup Files: {len(backup_files)} backup files found")
    
    # Check for migration reports
    migration_reports = list(Path(".").glob("BATCH_*_MIGRATION_*.md"))
    print(f"📋 Migration Reports: {len(migration_reports)} historical reports found")
    
    # Check for strategy legacy status
    strategy_legacy_files = []
    strategy_dir = Path("the_alchemiser/strategy")
    if strategy_dir.exists():
        for py_file in strategy_dir.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "Status.*legacy" in content:
                    strategy_legacy_files.append(str(py_file))
            except (UnicodeDecodeError, PermissionError):
                continue
    
    print(f"📊 Strategy Legacy Files: {len(strategy_legacy_files)} files marked 'Status: legacy'")
    
    # Summary
    print(f"\n📈 Cleanup Progress Summary:")
    total_items = len(legacy_files) + len(cache_dirs) + len(backup_files) + len(migration_reports) + len(strategy_legacy_files)
    print(f"  Total items identified: {total_items}")
    
    if total_items == 0:
        print("  🎉 All legacy items cleaned up!")
    elif total_items < 10:
        print("  🟡 Good progress - few items remaining")
    else:
        print("  🔴 Significant cleanup opportunity")


def check_import_health() -> None:
    """Check for broken imports and legacy import patterns."""
    print("\n🔗 Import Health Check:")
    
    try:
        import subprocess
        result = subprocess.run(
            ["python", "-c", "import the_alchemiser"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("  ✅ Main module imports successfully")
        else:
            print("  ❌ Import issues detected:")
            print(f"    {result.stderr}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("  ⚠️ Could not test imports (python not found or timeout)")


def main() -> None:
    """Run verification checks."""
    verify_audit_findings()
    check_import_health()
    
    print("\n🚀 Next Steps:")
    print("  1. Review MASTER_LEGACY_CLEANUP_ACTION_PLAN.md")
    print("  2. Execute Phase 1 safe deletions")
    print("  3. Plan import migration for high-priority items")


if __name__ == "__main__":
    main()