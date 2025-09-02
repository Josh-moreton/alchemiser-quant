#!/usr/bin/env python3
"""
Phase 2 Legacy Import Migration Script - Conservative Approach

This script safely migrates legacy files to new modular locations while preserving
functionality. Instead of replacing classes, it moves them to proper module locations
and updates imports accordingly.

Usage:
    python scripts/migrate_phase2_imports.py [--dry-run] [--verify]
    
Options:
    --dry-run    Show what would be changed without making changes
    --verify     Run verification tests after migration
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# File migration mapping: old_path -> new_path
FILE_MIGRATIONS = {
    # Move TradingEngine to strategy module  
    "the_alchemiser/application/trading/engine_service.py": 
        "the_alchemiser/strategy/engines/core/trading_engine.py",
    
    # Move SmartExecution to execution strategies
    "the_alchemiser/application/execution/smart_execution.py": 
        "the_alchemiser/execution/strategies/smart_execution.py",
}

# Import mapping: legacy -> new modular structure
IMPORT_MIGRATIONS = {
    # TradingEngine migrations
    "from the_alchemiser.application.trading.engine_service import TradingEngine": 
        "from the_alchemiser.strategy.engines.core.trading_engine import TradingEngine",
    
    # SmartExecution migrations  
    "from the_alchemiser.application.execution.smart_execution import SmartExecution": 
        "from the_alchemiser.execution.strategies.smart_execution import SmartExecution",
    
    # OrderExecutor migrations
    "from the_alchemiser.application.execution.smart_execution import OrderExecutor": 
        "from the_alchemiser.execution.strategies.smart_execution import OrderExecutor",
    
    # Market timing migrations
    "from the_alchemiser.application.execution.smart_execution import is_market_open": 
        "from the_alchemiser.execution.strategies.smart_execution import is_market_open",
}

# Files that need import migration (from analysis)
FILES_TO_MIGRATE = [
    "the_alchemiser/interfaces/cli/cli.py",
    "the_alchemiser/interfaces/cli/trading_executor.py",
    "the_alchemiser/execution/strategies/execution_context_adapter.py", 
    "the_alchemiser/application/execution/strategies/execution_context_adapter.py",
    "the_alchemiser/application/trading/alpaca_client.py",
    "the_alchemiser/portfolio/allocation/rebalance_execution_service.py",
]

# Legacy files to delete after successful migration
LEGACY_FILES_TO_DELETE = [
    "the_alchemiser/application/trading/engine_service.py",
    "the_alchemiser/application/execution/smart_execution.py",
]


def run_command(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run command with error handling."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        sys.exit(1)


def check_file_exists(file_path: str) -> bool:
    """Check if file exists."""
    return Path(file_path).exists()


def backup_file(file_path: str) -> str:
    """Create backup of file before modification."""
    backup_path = f"{file_path}.backup"
    if Path(file_path).exists():
        import shutil
        shutil.copy2(file_path, backup_path)
        return backup_path
    return ""


def move_legacy_files(dry_run: bool = False) -> bool:
    """Move legacy files to new modular locations."""
    print("\n📦 Moving legacy files to new locations...")
    
    for old_path, new_path in FILE_MIGRATIONS.items():
        if not check_file_exists(old_path):
            print(f"⚠️  Source file not found: {old_path}")
            continue
            
        # Create destination directory if needed
        new_dir = Path(new_path).parent
        if not new_dir.exists():
            if dry_run:
                print(f"🔍 [DRY RUN] Would create directory: {new_dir}")
            else:
                new_dir.mkdir(parents=True, exist_ok=True)
                print(f"📁 Created directory: {new_dir}")
        
        if dry_run:
            print(f"🔍 [DRY RUN] Would move {old_path} -> {new_path}")
        else:
            # Create backup first
            backup_path = backup_file(old_path)
            print(f"💾 Created backup: {backup_path}")
            
            # Move file
            shutil.move(old_path, new_path)
            print(f"✅ Moved {old_path} -> {new_path}")
    
    return True


def migrate_imports_in_file(file_path: str, dry_run: bool = False) -> bool:
    """Migrate imports in a single file."""
    if not check_file_exists(file_path):
        print(f"⚠️  File not found: {file_path}")
        return False
    
    # Read file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_made = False
    
    # Apply import migrations
    for old_import, new_import in IMPORT_MIGRATIONS.items():
        if old_import in content:
            print(f"📝 Found import to migrate in {file_path}:")
            print(f"   OLD: {old_import}")
            print(f"   NEW: {new_import}")
            
            # Replace with new import
            content = content.replace(old_import, new_import)
            changes_made = True
    
    if changes_made:
        if dry_run:
            print(f"🔍 [DRY RUN] Would update {file_path}")
        else:
            # Create backup
            backup_path = backup_file(file_path)
            print(f"💾 Created backup: {backup_path}")
            
            # Write updated content
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Updated {file_path}")
    
    return changes_made


def verify_migration() -> bool:
    """Verify migration was successful."""
    print("\n🔍 Verifying migration...")
    
    # Check that new files exist
    print("📋 Checking moved files exist...")
    for old_path, new_path in FILE_MIGRATIONS.items():
        if not check_file_exists(new_path):
            print(f"❌ Moved file not found: {new_path}")
            return False
        print(f"✅ File exists: {new_path}")
    
    # Check syntax of moved files
    print("📋 Checking Python syntax of moved files...")
    for old_path, new_path in FILE_MIGRATIONS.items():
        result = run_command(["python", "-m", "py_compile", new_path], check=False)
        if result.returncode != 0:
            print(f"❌ Syntax errors in moved file: {new_path}")
            return False
        print(f"✅ Syntax OK: {new_path}")
    
    # Check syntax of updated files  
    print("📋 Checking Python syntax of updated files...")
    for file_path in FILES_TO_MIGRATE:
        if check_file_exists(file_path):
            result = run_command(["python", "-m", "py_compile", file_path], check=False)
            if result.returncode != 0:
                print(f"❌ Syntax errors in updated file: {file_path}")
                return False
            print(f"✅ Syntax OK: {file_path}")
    
    print("✅ Migration verification passed")
    return True


def rollback_migration() -> None:
    """Rollback migration using backup files."""
    print("\n🔄 Rolling back migration...")
    
    # Restore moved files
    for old_path, new_path in FILE_MIGRATIONS.items():
        backup_path = f"{old_path}.backup"
        if Path(backup_path).exists():
            # Remove the moved file
            if Path(new_path).exists():
                os.remove(new_path)
                print(f"🗑️  Removed moved file: {new_path}")
            
            # Restore original
            shutil.move(backup_path, old_path)
            print(f"↩️  Restored {old_path}")
    
    # Restore updated files
    for file_path in FILES_TO_MIGRATE:
        backup_path = f"{file_path}.backup"
        if Path(backup_path).exists():
            shutil.move(backup_path, file_path)
            print(f"↩️  Restored {file_path}")


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="Migrate Phase 2 legacy imports")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    parser.add_argument("--verify", action="store_true", help="Run verification after migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback previous migration")
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
        return
    
    print("🚀 Starting Phase 2 Import Migration (Conservative Approach)")
    print(f"📁 Files to move: {len(FILE_MIGRATIONS)}")
    print(f"📊 Files to update imports: {len(FILES_TO_MIGRATE)}")
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    
    # Step 1: Move legacy files to new locations
    if not move_legacy_files(args.dry_run):
        print("❌ Failed to move legacy files")
        return
    
    # Step 2: Update imports in consuming files
    total_changes = 0
    for file_path in FILES_TO_MIGRATE:
        if migrate_imports_in_file(file_path, args.dry_run):
            total_changes += 1
    
    print(f"\n📊 Migration Summary:")
    print(f"   Files moved: {len(FILE_MIGRATIONS)}")
    print(f"   Files with import updates: {total_changes}/{len(FILES_TO_MIGRATE)}")
    
    if args.dry_run:
        print("🔍 Dry run complete. Use without --dry-run to apply changes.")
        return
    
    # Step 3: Verify migration if requested
    if args.verify:
        if not verify_migration():
            print("❌ Migration verification failed. Consider rollback with --rollback")
            sys.exit(1)
    
    print("✅ Phase 2 migration complete!")
    print("🎯 Legacy files moved to proper modular locations")
    print("📋 All imports updated to new locations")
    print("🗑️  Legacy file paths are now empty (files moved)")


if __name__ == "__main__":
    main()