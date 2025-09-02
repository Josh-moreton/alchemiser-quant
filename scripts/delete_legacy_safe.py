#!/usr/bin/env python3
"""
Legacy DDD Architecture Safe Deletion Script

This script safely deletes orphaned legacy files that have no active imports
and poses no risk to the system functionality.

Usage:
    python scripts/delete_legacy_safe.py [--dry-run] [--batch-size N]
    
Options:
    --dry-run      Show what would be deleted without actually deleting
    --batch-size   Number of files to delete in each batch (default: 10)
    --verify       Run verification tests after each batch
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List

# Safe files to delete (confirmed to have no active imports)
SAFE_LEGACY_FILES = [
    # Application layer - empty modules
    "the_alchemiser/application/reporting/__init__.py",
    "the_alchemiser/application/tracking/__init__.py", 
    "the_alchemiser/application/trading/__init__.py",
    "the_alchemiser/application/trading/lifecycle/__init__.py",
    
    # Domain layer - empty modules
    "the_alchemiser/domain/__init__.py",
    "the_alchemiser/domain/interfaces/__init__.py",
    "the_alchemiser/domain/market_data/__init__.py",
    "the_alchemiser/domain/math/__init__.py",
    "the_alchemiser/domain/math/protocols/__init__.py",
    "the_alchemiser/domain/models/__init__.py",
    "the_alchemiser/domain/policies/__init__.py",
    "the_alchemiser/domain/portfolio/__init__.py",
    "the_alchemiser/domain/portfolio/position/__init__.py",
    "the_alchemiser/domain/portfolio/rebalancing/__init__.py",
    "the_alchemiser/domain/portfolio/strategy_attribution/__init__.py",
    "the_alchemiser/domain/protocols/__init__.py",
    "the_alchemiser/domain/registry/__init__.py",
    "the_alchemiser/domain/services/__init__.py",
    "the_alchemiser/domain/shared_kernel/__init__.py",
    "the_alchemiser/domain/strategies_backup/__init__.py",
    "the_alchemiser/domain/strategies_backup/entities/__init__.py",
    "the_alchemiser/domain/strategies_backup/errors/__init__.py",
    "the_alchemiser/domain/strategies_backup/klm_workers/__init__.py",
    "the_alchemiser/domain/strategies_backup/models/__init__.py",
    "the_alchemiser/domain/trading/__init__.py",
    "the_alchemiser/domain/trading/errors/__init__.py",
    "the_alchemiser/domain/trading/lifecycle/__init__.py",
    "the_alchemiser/domain/trading/protocols/__init__.py",
    
    # Infrastructure layer - empty modules  
    "the_alchemiser/infrastructure/__init__.py",
    "the_alchemiser/infrastructure/adapters/__init__.py",
    "the_alchemiser/infrastructure/alerts/__init__.py",
    "the_alchemiser/infrastructure/config/__init__.py",
    "the_alchemiser/infrastructure/config/config_utils.py",
    "the_alchemiser/infrastructure/data_providers/__init__.py",
    "the_alchemiser/infrastructure/dependency_injection/__init__.py",
    "the_alchemiser/infrastructure/logging/__init__.py",
    "the_alchemiser/infrastructure/notifications/__init__.py",
    "the_alchemiser/infrastructure/notifications/templates/__init__.py",
    "the_alchemiser/infrastructure/s3/__init__.py",
    "the_alchemiser/infrastructure/secrets/__init__.py",
    "the_alchemiser/infrastructure/services/__init__.py",
    "the_alchemiser/infrastructure/validation/__init__.py",
    "the_alchemiser/infrastructure/websocket/__init__.py",
    
    # Interfaces layer - empty modules
    "the_alchemiser/interfaces/__init__.py",
    "the_alchemiser/interfaces/cli/__init__.py",
    "the_alchemiser/interfaces/schemas/__init__.py",
    
    # Services layer - empty modules
    "the_alchemiser/services/account/__init__.py",
    "the_alchemiser/services/errors/__init__.py",
    "the_alchemiser/services/repository/__init__.py",
    "the_alchemiser/services/shared/__init__.py",
    "the_alchemiser/services/trading/__init__.py",
]

def run_command(cmd: List[str], cwd: str = None) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def get_lint_count(repo_path: str) -> int:
    """Get current lint error count."""
    returncode, stdout, stderr = run_command(
        ["poetry", "run", "ruff", "check", "the_alchemiser/", "--quiet"],
        cwd=repo_path
    )
    if returncode != 0:
        return -1  # Error running linter
    
    lines = [line.strip() for line in stdout.strip().split('\n') if line.strip()]
    return len(lines)

def verify_system_health(repo_path: str) -> dict:
    """Run basic verification checks."""
    results = {}
    
    # Check linting
    lint_count = get_lint_count(repo_path)
    results['lint_count'] = lint_count
    results['lint_ok'] = lint_count >= 0
    
    # Check if Python can import the main module
    returncode, stdout, stderr = run_command(
        ["python", "-c", "import the_alchemiser; print('Import OK')"],
        cwd=repo_path
    )
    results['import_ok'] = returncode == 0
    results['import_error'] = stderr if returncode != 0 else None
    
    return results

def delete_files_batch(files: List[str], repo_path: str, dry_run: bool = False) -> List[str]:
    """Delete a batch of files and return list of successfully deleted files."""
    deleted = []
    
    for file_path in files:
        full_path = Path(repo_path) / file_path
        
        if not full_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
            
        if dry_run:
            print(f"🔍 Would delete: {file_path}")
            deleted.append(file_path)
        else:
            try:
                full_path.unlink()
                print(f"🗑️  Deleted: {file_path}")
                deleted.append(file_path)
            except Exception as e:
                print(f"❌ Failed to delete {file_path}: {e}")
    
    return deleted

def main():
    parser = argparse.ArgumentParser(description="Safely delete orphaned legacy DDD files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    parser.add_argument("--batch-size", type=int, default=10, help="Files to delete per batch")
    parser.add_argument("--verify", action="store_true", help="Run verification after each batch")
    parser.add_argument("--repo-path", default=".", help="Repository root path")
    
    args = parser.parse_args()
    
    repo_path = os.path.abspath(args.repo_path)
    
    print("🧹 Legacy DDD Architecture Safe Deletion")
    print("=" * 50)
    print(f"Repository: {repo_path}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE DELETION'}")
    print(f"Batch size: {args.batch_size}")
    print(f"Total files to process: {len(SAFE_LEGACY_FILES)}")
    print()
    
    # Get baseline health check
    print("🔍 Baseline system health check...")
    baseline = verify_system_health(repo_path)
    print(f"📊 Baseline lint count: {baseline['lint_count']}")
    print(f"🐍 Python import test: {'✅' if baseline['import_ok'] else '❌'}")
    if not baseline['import_ok']:
        print(f"⚠️  Import error: {baseline['import_error']}")
    print()
    
    # Find existing files
    existing_files = []
    for file_path in SAFE_LEGACY_FILES:
        full_path = Path(repo_path) / file_path
        if full_path.exists():
            existing_files.append(file_path)
    
    print(f"📁 Found {len(existing_files)} of {len(SAFE_LEGACY_FILES)} files to process")
    
    if not existing_files:
        print("✅ All safe legacy files already deleted!")
        return 0
    
    if not args.dry_run:
        confirm = input(f"\nProceed with deleting {len(existing_files)} files? [y/N]: ")
        if confirm.lower() != 'y':
            print("❌ Aborted by user")
            return 1
    
    # Process files in batches
    total_deleted = 0
    
    for i in range(0, len(existing_files), args.batch_size):
        batch = existing_files[i:i + args.batch_size]
        batch_num = (i // args.batch_size) + 1
        total_batches = (len(existing_files) + args.batch_size - 1) // args.batch_size
        
        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} files)")
        print("-" * 40)
        
        deleted = delete_files_batch(batch, repo_path, args.dry_run)
        total_deleted += len(deleted)
        
        if args.verify and not args.dry_run:
            print(f"\n🔍 Verifying system health after batch {batch_num}...")
            health = verify_system_health(repo_path)
            
            print(f"📊 Lint count: {health['lint_count']} (baseline: {baseline['lint_count']})")
            print(f"🐍 Python import: {'✅' if health['import_ok'] else '❌'}")
            
            # Check for significant issues
            lint_increase = health['lint_count'] - baseline['lint_count']
            if lint_increase > 50:  # Allow some small increases
                print(f"⚠️  Significant lint increase: +{lint_increase}")
                if not args.dry_run:
                    confirm = input("Continue despite lint increase? [y/N]: ")
                    if confirm.lower() != 'y':
                        print("❌ Stopping due to lint issues")
                        break
            
            if baseline['import_ok'] and not health['import_ok']:
                print("❌ Python import now failing!")
                if not args.dry_run:
                    print(f"Error: {health['import_error']}")
                    confirm = input("Continue despite import failure? [y/N]: ")
                    if confirm.lower() != 'y':
                        print("❌ Stopping due to import failure")
                        break
    
    # Summary
    print("\n" + "=" * 50)
    print("DELETION SUMMARY")
    print("=" * 50)
    print(f"Files processed: {total_deleted}/{len(existing_files)}")
    
    if args.dry_run:
        print("Mode: DRY RUN - no files actually deleted")
        print(f"Would delete {total_deleted} files")
    else:
        print(f"Successfully deleted: {total_deleted} files")
        remaining = len(existing_files) - total_deleted
        if remaining > 0:
            print(f"Remaining: {remaining} files (stopped early)")
    
    # Final health check
    if not args.dry_run and total_deleted > 0:
        print("\n🔍 Final system health check...")
        final = verify_system_health(repo_path)
        
        lint_change = final['lint_count'] - baseline['lint_count']
        print(f"📊 Lint count change: {lint_change}")
        print(f"🐍 Python import: {'✅' if final['import_ok'] else '❌'}")
        
        if final['import_ok'] and abs(lint_change) <= 50:
            print("✅ System health looks good!")
        else:
            print("⚠️  System health check shows issues")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())