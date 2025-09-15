"""Business Unit: orchestration | Status: current.

Shared module usage auditing script for identifying dead code and re-export cleanup.

This script performs static analysis of imports across the repository targeting 
the_alchemiser.shared.* to identify unused files/symbols and messy re-exports,
without changing runtime behavior.
"""

from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

# Type aliases for clarity
FileCount = dict[str, int]  
ModuleUsage = dict[str, "UsageInfo"]
PublicSymbols = set[str]


@dataclass
class UsageInfo:
    """Usage information for a shared module file."""
    
    file_path: str
    public_symbols: PublicSymbols = field(default_factory=set)
    imported_symbols: FileCount = field(default_factory=dict)
    importers: list[str] = field(default_factory=list)
    confidence: str = "high"
    
    @property
    def importer_count(self) -> int:
        """Number of files importing from this module."""
        return len(self.importers)
    
    @property
    def unused_symbols(self) -> set[str]:
        """Symbols exported but never imported."""
        return self.public_symbols - set(self.imported_symbols.keys())


class SharedUsageAnalyzer:
    """Analyzer for shared module usage across the repository."""
    
    def __init__(self, repo_root: Path) -> None:
        """Initialize analyzer with repository root."""
        self.repo_root = repo_root
        self.shared_root = repo_root / "the_alchemiser" / "shared"
        self.module_usage: ModuleUsage = {}
        self.re_export_map: dict[str, str] = {}
        
    def extract_public_symbols(self, file_path: Path) -> PublicSymbols:
        """Extract public symbols from a Python file.
        
        Prefers __all__ if present, otherwise uses top-level non-underscore definitions.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Set of public symbol names
            
        """
        try:
            with file_path.open(encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except (OSError, SyntaxError):
            return set()
        
        # Look for __all__ first
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and 
                any(isinstance(target, ast.Name) and target.id == "__all__" 
                    for target in node.targets)):
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    result_symbols: set[str] = set()
                    for elt in node.value.elts:
                        if hasattr(elt, "s") and isinstance(elt.s, str):  # ast.Str
                            result_symbols.add(elt.s)
                        elif isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            result_symbols.add(elt.value)
                    return result_symbols
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, list):
                    return {item for item in node.value.value if isinstance(item, str)}
        
        # Fallback: extract top-level definitions
        fallback_symbols: set[str] = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    fallback_symbols.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        fallback_symbols.add(target.id)
        
        return fallback_symbols
    
    def build_re_export_map(self) -> None:
        """Build mapping of re-exported symbols to their original modules."""
        init_files = list(self.shared_root.rglob("__init__.py"))
        
        for init_path in init_files:
            try:
                with init_path.open(encoding="utf-8") as f:
                    tree = ast.parse(f.read())
            except (OSError, SyntaxError):
                continue
                
            module_prefix = str(init_path.parent.relative_to(self.repo_root)).replace("/", ".")
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for alias in node.names:
                        symbol_name = alias.asname or alias.name
                        if alias.name != "*":  # Skip star imports
                            source_module = f"{module_prefix}.{node.module}"
                            self.re_export_map[f"{module_prefix}.{symbol_name}"] = source_module
    
    def scan_file_imports(self, file_path: Path) -> list[tuple[str, str]]:
        """Scan a file for imports from the_alchemiser.shared.
        
        Args:
            file_path: Path to Python file to scan
            
        Returns:
            List of (module_path, symbol) tuples
            
        """
        try:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)
        except (OSError, SyntaxError):
            return []
        
        imports = []
        
        # AST-based import detection
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("the_alchemiser.shared"):
                    for alias in node.names:
                        if alias.name == "*":
                            imports.append((node.module, "*"))
                        else:
                            imports.append((node.module, alias.name))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("the_alchemiser.shared"):
                        imports.append((alias.name, ""))
        
        # Heuristic string-based detection for dynamic imports
        shared_pattern = re.compile(r"the_alchemiser\.shared\.[\w.]+")
        for match in shared_pattern.finditer(content):
            module_path = match.group()
            imports.append((module_path, ""))
        
        return imports
    
    def analyze_shared_files(self) -> None:
        """Analyze all Python files in the shared module."""
        python_files = list(self.shared_root.rglob("*.py"))
        
        for file_path in python_files:
            if file_path.name == "__init__.py":
                continue  # Skip init files in this phase
                
            relative_path = str(file_path.relative_to(self.repo_root))
            module_path = relative_path.replace("/", ".").replace(".py", "")
            
            public_symbols = self.extract_public_symbols(file_path)
            
            self.module_usage[module_path] = UsageInfo(
                file_path=relative_path,
                public_symbols=public_symbols
            )
    
    def scan_repository_imports(self) -> None:
        """Scan all Python files in the repository for shared imports."""
        python_files = list(self.repo_root.rglob("*.py"))
        
        for file_path in python_files:
            if self.shared_root in file_path.parents:
                continue  # Skip shared module itself
                
            relative_path = str(file_path.relative_to(self.repo_root))
            imports = self.scan_file_imports(file_path)
            
            for module_path, symbol in imports:
                # Resolve re-exports
                if symbol and symbol != "*":
                    full_symbol_path = f"{module_path}.{symbol}"
                    original_module = self.re_export_map.get(full_symbol_path, module_path)
                else:
                    original_module = module_path
                
                # Map to our tracked modules
                if original_module in self.module_usage:
                    usage_info = self.module_usage[original_module]
                    
                    if relative_path not in usage_info.importers:
                        usage_info.importers.append(relative_path)
                    
                    if symbol and symbol != "*":
                        usage_info.imported_symbols[symbol] = usage_info.imported_symbols.get(symbol, 0) + 1
                    
                    # Lower confidence for star imports or package-only imports
                    if symbol in ("*", ""):
                        usage_info.confidence = "low"
    
    def calculate_confidence(self) -> None:
        """Calculate confidence scores for usage analysis."""
        for usage_info in self.module_usage.values():
            if not usage_info.importers:
                usage_info.confidence = "high"  # High confidence it's unused
            elif not usage_info.imported_symbols:
                usage_info.confidence = "low"   # Only package-level imports
            else:
                usage_info.confidence = "high"  # Direct symbol imports
    
    def generate_report(self, output_path: Path) -> None:
        """Generate markdown usage report."""
        total_files = len(self.module_usage)
        unused_files = sum(1 for u in self.module_usage.values() if u.importer_count == 0)
        total_symbols = sum(len(u.public_symbols) for u in self.module_usage.values())
        unused_symbols = sum(len(u.unused_symbols) for u in self.module_usage.values())
        
        with output_path.open("w", encoding="utf-8") as f:
            f.write("# Shared Module Usage Report\n\n")
            f.write("Static analysis of `the_alchemiser.shared` module usage across the repository.\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Total shared files analyzed**: {total_files}\n")
            f.write(f"- **Files with no importers**: {unused_files}\n")
            f.write(f"- **Total public symbols**: {total_symbols}\n")
            f.write(f"- **Unused symbols**: {unused_symbols}\n\n")
            
            # Unused files section
            unused_modules = [m for m in self.module_usage.values() if m.importer_count == 0]
            if unused_modules:
                f.write("## Potentially Unused Files\n\n")
                for usage in sorted(unused_modules, key=lambda x: x.file_path):
                    f.write(f"- `{usage.file_path}` ({len(usage.public_symbols)} public symbols)\n")
                f.write("\n")
            
            # Detailed usage
            f.write("## Detailed Usage Analysis\n\n")
            for module_path in sorted(self.module_usage.keys()):
                usage = self.module_usage[module_path]
                f.write(f"### {module_path}\n\n")
                f.write(f"- **File**: `{usage.file_path}`\n")
                f.write(f"- **Importer count**: {usage.importer_count}\n")
                f.write(f"- **Confidence**: {usage.confidence}\n")
                f.write(f"- **Public symbols**: {len(usage.public_symbols)}\n")
                f.write(f"- **Imported symbols**: {len(usage.imported_symbols)}\n")
                f.write(f"- **Unused symbols**: {len(usage.unused_symbols)}\n")
                
                if usage.importers:
                    f.write(f"- **Importers** ({len(usage.importers)}):\n")
                    for importer in sorted(usage.importers[:10]):  # Cap at 10
                        f.write(f"  - `{importer}`\n")
                    if len(usage.importers) > 10:
                        f.write(f"  - _(and {len(usage.importers) - 10} more)_\n")
                
                if usage.unused_symbols:
                    f.write(f"- **Unused symbols**: {sorted(usage.unused_symbols)}\n")
                
                f.write("\n")
            
            # Re-export analysis
            if self.re_export_map:
                f.write("## Re-export Analysis\n\n")
                f.write(f"Found {len(self.re_export_map)} re-exported symbols.\n\n")
                for symbol, source in sorted(self.re_export_map.items())[:20]:  # Show first 20
                    f.write(f"- `{symbol}` → `{source}`\n")
                if len(self.re_export_map) > 20:
                    f.write(f"- _(and {len(self.re_export_map) - 20} more)_\n")
                f.write("\n")
    
    def run_analysis(self, output_path: Path) -> None:
        """Run complete usage analysis and generate report."""
        print("Building re-export map...")
        self.build_re_export_map()
        
        print("Analyzing shared module files...")
        self.analyze_shared_files()
        
        print("Scanning repository for imports...")
        self.scan_repository_imports()
        
        print("Calculating confidence scores...")
        self.calculate_confidence()
        
        print(f"Generating report: {output_path}")
        self.generate_report(output_path)
        
        print("Analysis complete!")


def main() -> None:
    """Run main entry point for the shared usage analysis script."""
    parser = argparse.ArgumentParser(
        description="Analyze shared module usage and generate report"
    )
    parser.add_argument(
        "--md", 
        type=str, 
        default="shared_usage_report.md",
        help="Output markdown file path (default: shared_usage_report.md)"
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        help="Repository root path (default: current directory)"
    )
    
    args = parser.parse_args()
    
    repo_root = Path(args.repo_root) if args.repo_root else Path.cwd()
    output_path = Path(args.md)
    
    if not (repo_root / "the_alchemiser" / "shared").exists():
        print(f"Error: shared module not found at {repo_root / 'the_alchemiser' / 'shared'}")
        return
    
    analyzer = SharedUsageAnalyzer(repo_root)
    analyzer.run_analysis(output_path)


if __name__ == "__main__":
    main()