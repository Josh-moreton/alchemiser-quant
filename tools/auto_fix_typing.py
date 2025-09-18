#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Auto-fix script for common typing violations.

Applies automated fixes for simple, mechanical typing violations that 
follow predictable patterns, reducing manual remediation effort.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Tuple


def fix_dict_any_metadata_fields(file_path: Path) -> bool:
    """Fix dict[str, Any] → dict[str, str | int | bool | None] for metadata fields."""
    if not file_path.exists():
        return False
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_content = content
        
        # Pattern for metadata fields with dict[str, Any]
        metadata_pattern = re.compile(
            r'(\s+)(\w*metadata\w*|constraints|context|details|raw):\s*dict\[str,\s*Any\](\s*\|?\s*None)?\s*=\s*Field\(',
            re.IGNORECASE
        )
        
        def replace_metadata(match):
            indent = match.group(1)
            field_name = match.group(2)
            optional = match.group(3) or ""
            
            return f'{indent}{field_name}: dict[str, str | int | bool | None]{optional} = Field('
        
        content = metadata_pattern.sub(replace_metadata, content)
        
        # If changes were made, write back
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Fixed metadata fields in {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        
    return False


def fix_any_unions(file_path: Path) -> bool:
    """Fix Union types that include Any unnecessarily."""
    if not file_path.exists():
        return False
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_content = content
        
        # Pattern for | Any unions (remove the | Any part)
        any_union_pattern = re.compile(r'\s*\|\s*Any(?=\s*[,\]\)\n])', re.MULTILINE)
        content = any_union_pattern.sub('', content)
        
        # Pattern for Any | other (remove Any | part)  
        any_first_pattern = re.compile(r'Any\s*\|\s*', re.MULTILINE)
        content = any_first_pattern.sub('', content)
        
        # If changes were made, write back
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Fixed Any unions in {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        
    return False


def fix_lambda_handler_types(file_path: Path) -> bool:
    """Fix lambda handler event/context parameters to use proper AWS types."""
    if not file_path.exists() or "lambda" not in file_path.name.lower():
        return False
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_content = content
        
        # Fix lambda handler event parameter
        lambda_pattern = re.compile(
            r'def\s+lambda_handler\s*\(\s*event:\s*Any\s*,\s*context:\s*Any\s*\)',
            re.MULTILINE
        )
        
        if lambda_pattern.search(content):
            # Add AWS types import if not present
            if 'from aws_lambda_typing' not in content:
                import_pattern = re.compile(r'(from __future__ import annotations\n)')
                content = import_pattern.sub(
                    r'\1\nfrom aws_lambda_typing import context as lambda_context\nfrom typing import Dict\n',
                    content
                )
            
            # Replace the lambda handler signature
            content = lambda_pattern.sub(
                'def lambda_handler(event: Dict[str, any], context: lambda_context.LambdaContext)',
                content
            )
        
        # If changes were made, write back
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Fixed lambda handler types in {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        
    return False


def fix_method_any_parameters(file_path: Path) -> bool:
    """Fix simple method parameters typed as Any to more specific types."""
    if not file_path.exists():
        return False
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_content = content
        
        # Common parameter name patterns that can be improved
        patterns = [
            # dict[str, Any] parameters
            (re.compile(r'(\w+):\s*dict\[str,\s*Any\]'), r'\1: dict[str, str | int | bool | None]'),
            # list[Any] parameters  
            (re.compile(r'(\w+):\s*list\[Any\]'), r'\1: list[str | int | bool]'),
            # Optional[Any] parameters
            (re.compile(r'(\w+):\s*Any\s*\|\s*None'), r'\1: str | int | bool | None'),
        ]
        
        changes_made = False
        for pattern, replacement in patterns:
            new_content = pattern.sub(replacement, content)
            if new_content != content:
                content = new_content
                changes_made = True
        
        # If changes were made, write back
        if changes_made:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Fixed method parameters in {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        
    return False


def apply_auto_fixes(directory: str = "the_alchemiser") -> Tuple[int, int]:
    """Apply all auto-fixes to Python files in directory."""
    target_dir = Path(directory)
    
    if not target_dir.exists():
        print(f"❌ Directory {target_dir} does not exist")
        return 0, 0
    
    python_files = list(target_dir.rglob("*.py"))
    files_processed = 0
    files_changed = 0
    
    print(f"🔧 Applying auto-fixes to {len(python_files)} Python files...")
    
    for file_path in python_files:
        files_processed += 1
        
        # Apply all fixes
        fixes_applied = [
            fix_dict_any_metadata_fields(file_path),
            fix_any_unions(file_path),
            fix_lambda_handler_types(file_path),
            fix_method_any_parameters(file_path),
        ]
        
        if any(fixes_applied):
            files_changed += 1
    
    return files_processed, files_changed


def main() -> int:
    """Main entry point for auto-fix script."""
    print("🤖 Auto-fixing common typing violations...")
    
    files_processed, files_changed = apply_auto_fixes()
    
    print(f"\n📊 Auto-fix Results:")
    print(f"Files processed: {files_processed}")
    print(f"Files changed: {files_changed}")
    
    if files_changed > 0:
        print("\n✅ Auto-fixes applied successfully!")
        print("ℹ️  Run 'make typing-audit' to see updated violation counts")
        print("ℹ️  Review changes and run tests before committing")
    else:
        print("\n✅ No auto-fixable violations found")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())