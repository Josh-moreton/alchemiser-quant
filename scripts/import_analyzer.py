#!/usr/bin/env python3
"""Business Unit: shared | Status: current

Import dependency analyzer for legacy audit.

This utility analyzes import dependencies to identify which files
are importing from legacy modules, helping prioritize migration efforts.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


class ImportAnalyzer:
    """Analyzes import dependencies for legacy audit."""
    
    def __init__(self, root_path: str = ".") -> None:
        """Initialize the analyzer."""
        self.root_path = Path(root_path)
        self.import_graph: dict[str, list[str]] = {}
        self.legacy_files = set()
        
    def find_legacy_imports(self) -> dict[str, list[str]]:
        """Find all files importing from legacy modules."""
        print("🔗 Analyzing import dependencies...")
        
        # First, identify legacy files
        self._identify_legacy_files()
        
        # Then find what imports them
        legacy_importers = {}
        
        for py_file in self._find_all_python_files():
            if self._should_exclude_file(py_file):
                continue
                
            imports = self._extract_imports(py_file)
            legacy_imports = []
            
            for import_path in imports:
                if self._is_legacy_import(import_path):
                    legacy_imports.append(import_path)
            
            if legacy_imports:
                legacy_importers[str(py_file)] = legacy_imports
        
        return legacy_importers
    
    def _identify_legacy_files(self) -> None:
        """Identify files that are considered legacy."""
        legacy_patterns = [
            r".*legacy.*\.py$",
            r".*deprecated.*\.py$",
            r".*shim.*\.py$",
        ]
        
        for py_file in self._find_all_python_files():
            file_str = str(py_file)
            
            # Check filename patterns
            if any(re.match(pattern, file_str, re.IGNORECASE) for pattern in legacy_patterns):
                self.legacy_files.add(file_str)
                continue
            
            # Check file content for legacy markers
            content = self._safe_read_file(py_file)
            if content and re.search(r"Status.*legacy", content, re.IGNORECASE):
                self.legacy_files.add(file_str)
    
    def _extract_imports(self, file_path: Path) -> list[str]:
        """Extract import statements from a Python file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            return imports
        except (SyntaxError, UnicodeDecodeError, PermissionError):
            # Fall back to regex-based extraction for problematic files
            return self._extract_imports_regex(file_path)
    
    def _extract_imports_regex(self, file_path: Path) -> list[str]:
        """Extract imports using regex as fallback."""
        content = self._safe_read_file(file_path)
        if not content:
            return []
        
        imports = []
        
        # Match import statements
        import_patterns = [
            r"^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)",
            r"^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import",
        ]
        
        for line in content.split("\n"):
            line = line.strip()
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    imports.append(match.group(1))
        
        return imports
    
    def _is_legacy_import(self, import_path: str) -> bool:
        """Check if an import path references a legacy module."""
        # Convert import path to potential file paths
        possible_paths = [
            f"{import_path.replace('.', '/')}.py",
            f"{import_path.replace('.', '/')}/__init__.py",
        ]
        
        for possible_path in possible_paths:
            full_path = str(self.root_path / possible_path)
            if full_path in self.legacy_files:
                return True
        
        # Also check for legacy keywords in import path
        legacy_keywords = ["legacy", "deprecated", "shim"]
        return any(keyword in import_path.lower() for keyword in legacy_keywords)
    
    def _find_all_python_files(self) -> list[Path]:
        """Find all Python files in the repository."""
        return list(self.root_path.rglob("*.py"))
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from analysis."""
        exclude_patterns = [".venv", "__pycache__", ".git"]
        return any(pattern in str(file_path) for pattern in exclude_patterns)
    
    def _safe_read_file(self, file_path: Path) -> str | None:
        """Safely read file content."""
        try:
            return file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError, FileNotFoundError):
            return None


def main() -> None:
    """Run import analysis."""
    analyzer = ImportAnalyzer()
    legacy_importers = analyzer.find_legacy_imports()
    
    print(f"\n📊 Found {len(legacy_importers)} files importing from legacy modules:")
    
    for file_path, imports in legacy_importers.items():
        print(f"\n📁 {file_path}")
        for import_path in imports:
            print(f"  └── imports {import_path}")


if __name__ == "__main__":
    main()