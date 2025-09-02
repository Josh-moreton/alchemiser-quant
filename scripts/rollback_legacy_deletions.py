#!/usr/bin/env python3
"""
Legacy Deletion Rollback Script

This script can rollback the safe deletions if needed by restoring files
from git history.

Usage:
    python scripts/rollback_legacy_deletions.py [--commit HASH] [--file-list]
    
Options:
    --commit       Git commit hash to restore from (default: HEAD~1)
    --file-list    Show list of files that can be restored
    --dry-run      Show what would be restored without actually doing it
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List

# Files that were safely deleted (can be restored)
DELETED_LEGACY_FILES = [
    "the_alchemiser/application/__init__.py",
    "the_alchemiser/application/execution/__init__.py",
    "the_alchemiser/application/execution/strategies/__init__.py",
    "the_alchemiser/application/mapping/__init__.py",
    "the_alchemiser/application/mapping/models/__init__.py",
    "the_alchemiser/application/orders/__init__.py",
    "the_alchemiser/application/orders/progressive_order_utils.py",
    "the_alchemiser/application/policies/__init__.py",
    "the_alchemiser/application/portfolio/__init__.py",
    "the_alchemiser/application/portfolio/services/__init__.py",
    # Add more files as they get deleted
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

def check_git_status(repo_path: str) -> bool:
    """Check if we're in a git repository with a clean working directory."""
    # Check if we're in a git repo
    returncode, stdout, stderr = run_command(["git", "rev-parse", "--git-dir"], cwd=repo_path)
    if returncode != 0:
        print("❌ Not in a git repository")
        return False
    
    # Check for uncommitted changes
    returncode, stdout, stderr = run_command(["git", "status", "--porcelain"], cwd=repo_path)
    if returncode != 0:
        print("❌ Could not check git status")
        return False
    
    if stdout.strip():
        print("⚠️  Warning: Working directory has uncommitted changes")
        return True  # Allow but warn
    
    return True

def file_exists_in_commit(file_path: str, commit: str, repo_path: str) -> bool:
    """Check if a file exists in a specific commit."""
    returncode, stdout, stderr = run_command(
        ["git", "cat-file", "-e", f"{commit}:{file_path}"],
        cwd=repo_path
    )
    return returncode == 0

def restore_file(file_path: str, commit: str, repo_path: str, dry_run: bool = False) -> bool:
    """Restore a file from a specific commit."""
    if not file_exists_in_commit(file_path, commit, repo_path):
        print(f"⚠️  File {file_path} not found in commit {commit}")
        return False
    
    if dry_run:
        print(f"🔍 Would restore: {file_path} from {commit}")
        return True
    
    # Create directory if it doesn't exist
    full_path = Path(repo_path) / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Restore the file
    returncode, stdout, stderr = run_command(
        ["git", "checkout", commit, "--", file_path],
        cwd=repo_path
    )
    
    if returncode == 0:
        print(f"✅ Restored: {file_path}")
        return True
    else:
        print(f"❌ Failed to restore {file_path}: {stderr}")
        return False

def get_recent_commits(repo_path: str, count: int = 10) -> List[tuple[str, str]]:
    """Get recent commits with their hashes and messages."""
    returncode, stdout, stderr = run_command(
        ["git", "log", f"--oneline", f"-{count}"],
        cwd=repo_path
    )
    
    if returncode != 0:
        return []
    
    commits = []
    for line in stdout.strip().split('\n'):
        if line.strip():
            parts = line.split(' ', 1)
            if len(parts) >= 2:
                commits.append((parts[0], parts[1]))
            else:
                commits.append((parts[0], ""))
    
    return commits

def main():
    parser = argparse.ArgumentParser(description="Rollback safe legacy file deletions")
    parser.add_argument("--commit", default="HEAD~1", help="Git commit to restore from")
    parser.add_argument("--file-list", action="store_true", help="Show files that can be restored")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be restored")
    parser.add_argument("--repo-path", default=".", help="Repository root path")
    parser.add_argument("--interactive", action="store_true", help="Interactively select files to restore")
    
    args = parser.parse_args()
    
    repo_path = os.path.abspath(args.repo_path)
    
    print("🔄 Legacy Deletion Rollback Script")
    print("=" * 50)
    print(f"Repository: {repo_path}")
    print(f"Target commit: {args.commit}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE RESTORE'}")
    print()
    
    # Check git status
    if not check_git_status(repo_path):
        return 1
    
    # Show recent commits for context
    print("📋 Recent commits:")
    recent_commits = get_recent_commits(repo_path)
    for i, (hash_short, message) in enumerate(recent_commits[:5]):
        marker = "→" if hash_short == args.commit[:len(hash_short)] else " "
        print(f"  {marker} {hash_short} {message}")
    print()
    
    # Show available files for restoration
    if args.file_list:
        print("📁 Files that can be restored:")
        for file_path in DELETED_LEGACY_FILES:
            exists_in_commit = file_exists_in_commit(file_path, args.commit, repo_path)
            exists_now = (Path(repo_path) / file_path).exists()
            
            status = ""
            if exists_now:
                status = "EXISTS"
            elif exists_in_commit:
                status = "CAN RESTORE"
            else:
                status = "NOT FOUND IN COMMIT"
            
            print(f"  {file_path} - {status}")
        return 0
    
    # Find files that can be restored
    restorable_files = []
    for file_path in DELETED_LEGACY_FILES:
        current_path = Path(repo_path) / file_path
        if not current_path.exists() and file_exists_in_commit(file_path, args.commit, repo_path):
            restorable_files.append(file_path)
    
    print(f"📁 Found {len(restorable_files)} files that can be restored")
    
    if not restorable_files:
        print("✅ No files need to be restored")
        return 0
    
    # Interactive file selection
    files_to_restore = restorable_files
    if args.interactive:
        print("\n📋 Select files to restore:")
        selected = []
        for i, file_path in enumerate(restorable_files):
            response = input(f"Restore {file_path}? [y/N]: ")
            if response.lower() == 'y':
                selected.append(file_path)
        files_to_restore = selected
        
        if not files_to_restore:
            print("❌ No files selected for restoration")
            return 0
    
    print(f"\n🔄 Will restore {len(files_to_restore)} files from {args.commit}")
    
    if not args.dry_run:
        confirm = input(f"\nProceed with restoring {len(files_to_restore)} files? [y/N]: ")
        if confirm.lower() != 'y':
            print("❌ Aborted by user")
            return 1
    
    # Restore files
    restored_count = 0
    failed_count = 0
    
    for file_path in files_to_restore:
        if restore_file(file_path, args.commit, repo_path, args.dry_run):
            restored_count += 1
        else:
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("ROLLBACK SUMMARY")
    print("=" * 50)
    
    if args.dry_run:
        print("Mode: DRY RUN - no files actually restored")
        print(f"Would restore: {restored_count} files")
    else:
        print(f"Successfully restored: {restored_count} files")
        
    if failed_count > 0:
        print(f"Failed to restore: {failed_count} files")
    
    if not args.dry_run and restored_count > 0:
        print("\n📝 Next steps:")
        print("1. Run tests to verify system works with restored files")
        print("2. Consider committing the restoration if intentional")
        print("3. Or reset changes if this was just a test")
        print("\nTo commit the restoration:")
        print("  git add .")
        print('  git commit -m "Restore legacy files"')
        print("\nTo discard the restoration:")
        print("  git checkout -- .")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())