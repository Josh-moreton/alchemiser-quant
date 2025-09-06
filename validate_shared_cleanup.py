#!/usr/bin/env python3
"""
Shared Module Validation Script
Validates that all imports are still working after cleanup.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def validate_imports():
    """Validate that all shared module imports still work."""
    print("Validating shared module imports...")
    
    # Test basic import
    success, stdout, stderr = run_command("python -c 'import the_alchemiser.shared'")
    if not success:
        print(f"ERROR: Basic shared import failed: {stderr}")
        return False
    
    print("✓ Basic shared import successful")
    
    # Test key imports that should still work
    key_imports = [
        "from the_alchemiser.shared.value_objects.symbol import Symbol",
        "from the_alchemiser.shared.types.money import Money",
        "from the_alchemiser.shared.types.quantity import Quantity",
        "from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler",
    ]
    
    for import_stmt in key_imports:
        success, stdout, stderr = run_command(f"python -c '{import_stmt}'")
        if not success:
            print(f"ERROR: Import failed: {import_stmt}")
            print(f"Error: {stderr}")
            return False
        print(f"✓ {import_stmt}")
    
    return True

def validate_module_structure():
    """Validate that the module structure is still intact."""
    print("\nValidating module structure...")
    
    required_dirs = [
        "the_alchemiser/shared/types",
        "the_alchemiser/shared/value_objects", 
        "the_alchemiser/shared/dto",
        "the_alchemiser/shared/errors",
        "the_alchemiser/shared/utils",
    ]
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"ERROR: Required directory missing: {dir_path}")
            return False
        print(f"✓ {dir_path}")
    
    return True

def main():
    """Main validation function."""
    print("=== Shared Module Validation ===\n")
    
    if not validate_module_structure():
        print("\n❌ Module structure validation failed")
        sys.exit(1)
    
    if not validate_imports():
        print("\n❌ Import validation failed")
        sys.exit(1)
    
    print("\n✅ All validations passed!")
    print("Shared module cleanup completed successfully.")

if __name__ == "__main__":
    main()
