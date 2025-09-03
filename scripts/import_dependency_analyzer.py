#!/usr/bin/env python3
"""Import Dependency Analyzer

This script analyzes which legacy files are still actively imported
to help prioritize migration efforts and avoid breaking changes.
"""

from __future__ import annotations

import ast
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

class ImportDependencyAnalyzer:
    """Analyzes import dependencies to identify migration priorities."""
    
    def __init__(self, root_path: str | Path) -> None:
        self.root_path = Path(root_path)
        self.import_graph: dict[str, list[str]] = defaultdict(list)
        self.reverse_import_graph: dict[str, list[str]] = defaultdict(list)
    
    def analyze_file_imports(self, file_path: Path) -> list[str]:
        """Extract all import statements from a Python file."""
        imports = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        if node.level > 0:  # Relative import
                            # Handle relative imports
                            module_parts = str(file_path.relative_to(self.root_path)).replace('/', '.').replace('.py', '').split('.')
                            if node.level == 1:
                                base_module = '.'.join(module_parts[:-1])
                            else:
                                base_module = '.'.join(module_parts[:-(node.level)])
                            
                            if node.module:
                                full_module = f"{base_module}.{node.module}"
                            else:
                                full_module = base_module
                            imports.append(full_module)
                        else:
                            imports.append(node.module)
                            
        except (SyntaxError, UnicodeDecodeError, OSError):
            pass  # Skip files with syntax errors or encoding issues
            
        return imports
    
    def build_import_graph(self) -> None:
        """Build a graph of all imports in the codebase."""
        print("🔍 Building import dependency graph...")
        
        for py_file in self.root_path.rglob("*.py"):
            if any(skip_dir in str(py_file) for skip_dir in ['.venv', '__pycache__', '.git']):
                continue
                
            file_module = str(py_file.relative_to(self.root_path)).replace('/', '.').replace('.py', '')
            imports = self.analyze_file_imports(py_file)
            
            for imported_module in imports:
                # Only track internal imports (start with the_alchemiser)
                if imported_module.startswith('the_alchemiser'):
                    self.import_graph[file_module].append(imported_module)
                    self.reverse_import_graph[imported_module].append(file_module)
        
        print(f"✅ Analyzed {len(self.import_graph)} modules")
    
    def find_legacy_import_targets(self) -> dict[str, list[str]]:
        """Find legacy files that are still being imported."""
        legacy_patterns = [
            'utils.',
            'services.',
            'application.',
            'domain.',
            'infrastructure.',
            'interfaces.'
        ]
        
        legacy_imports = {}
        
        for imported_module, importing_files in self.reverse_import_graph.items():
            # Check if this is a legacy module pattern
            if any(pattern in imported_module for pattern in legacy_patterns):
                legacy_imports[imported_module] = importing_files
        
        return legacy_imports
    
    def find_shim_dependencies(self) -> dict[str, list[str]]:
        """Find files that import from known shim files."""
        audit_findings_file = self.root_path / "legacy_audit_findings.json"
        if not audit_findings_file.exists():
            return {}
        
        with audit_findings_file.open() as f:
            findings = json.load(f)
        
        # Get shim files from audit
        shim_files = []
        for finding in findings:
            if finding["finding_type"] == "shim":
                file_path = finding["file_path"]
                module_path = file_path.replace("/", ".").replace(".py", "")
                shim_files.append(module_path)
        
        shim_dependencies = {}
        for shim_module in shim_files:
            if shim_module in self.reverse_import_graph:
                shim_dependencies[shim_module] = self.reverse_import_graph[shim_module]
        
        return shim_dependencies
    
    def prioritize_migration_targets(self) -> dict[str, Any]:
        """Create a prioritized list of migration targets."""
        legacy_imports = self.find_legacy_import_targets()
        shim_dependencies = self.find_shim_dependencies()
        
        priorities = {}
        
        # High priority: Legacy files with many importers
        high_priority = {}
        for module, importers in legacy_imports.items():
            if len(importers) >= 3:  # 3+ files importing it
                high_priority[module] = {
                    "importers": importers,
                    "count": len(importers),
                    "type": "legacy_heavy_use"
                }
        
        # Medium priority: Legacy files with few importers
        medium_priority = {}
        for module, importers in legacy_imports.items():
            if 1 <= len(importers) < 3:
                medium_priority[module] = {
                    "importers": importers,
                    "count": len(importers),
                    "type": "legacy_light_use"
                }
        
        # Low priority: Shims that can be removed after import updates
        low_priority = {}
        for module, importers in shim_dependencies.items():
            low_priority[module] = {
                "importers": importers,
                "count": len(importers),
                "type": "shim"
            }
        
        return {
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority
        }
    
    def generate_migration_report(self) -> str:
        """Generate a comprehensive migration priority report."""
        priorities = self.prioritize_migration_targets()
        
        report_lines = [
            "# Import Dependency Migration Report",
            "",
            f"**Generated**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Modules Analyzed**: {len(self.import_graph)}",
            "",
            "## Executive Summary",
            "",
            f"- **HIGH PRIORITY**: {len(priorities['high_priority'])} heavily-used legacy modules",
            f"- **MEDIUM PRIORITY**: {len(priorities['medium_priority'])} lightly-used legacy modules", 
            f"- **LOW PRIORITY**: {len(priorities['low_priority'])} shim modules for cleanup",
            "",
            "## Migration Priority Analysis",
            ""
        ]
        
        # High priority section
        if priorities['high_priority']:
            report_lines.extend([
                "### 🔴 HIGH PRIORITY: Heavily-Used Legacy Modules",
                "",
                "These modules are imported by 3+ files and should be migrated first:",
                "",
                "| Module | Importers | Files Importing |",
                "|--------|-----------|-----------------|"
            ])
            
            for module, info in sorted(priorities['high_priority'].items(), 
                                     key=lambda x: x[1]['count'], reverse=True):
                importers_str = ", ".join(f"`{imp}`" for imp in info['importers'][:3])
                if len(info['importers']) > 3:
                    importers_str += f" + {len(info['importers']) - 3} more"
                
                report_lines.append(f"| `{module}` | {info['count']} | {importers_str} |")
            
            report_lines.append("")
        
        # Medium priority section
        if priorities['medium_priority']:
            report_lines.extend([
                "### 🟡 MEDIUM PRIORITY: Lightly-Used Legacy Modules",
                "",
                "These modules have 1-2 importers and can be migrated after high priority:",
                "",
                "| Module | Importers | Files Importing |",
                "|--------|-----------|-----------------|"
            ])
            
            for module, info in sorted(priorities['medium_priority'].items(), 
                                     key=lambda x: x[1]['count'], reverse=True):
                importers_str = ", ".join(f"`{imp}`" for imp in info['importers'])
                report_lines.append(f"| `{module}` | {info['count']} | {importers_str} |")
            
            report_lines.append("")
        
        # Low priority section
        if priorities['low_priority']:
            report_lines.extend([
                "### 🟢 LOW PRIORITY: Shim Cleanup",
                "",
                "These shim modules can be removed after updating import statements:",
                "",
                "| Module | Importers | Files Importing |",
                "|--------|-----------|-----------------|"
            ])
            
            for module, info in sorted(priorities['low_priority'].items(), 
                                     key=lambda x: x[1]['count'], reverse=True):
                importers_str = ", ".join(f"`{imp}`" for imp in info['importers'][:3])
                if len(info['importers']) > 3:
                    importers_str += f" + {len(info['importers']) - 3} more"
                
                report_lines.append(f"| `{module}` | {info['count']} | {importers_str} |")
            
            report_lines.append("")
        
        report_lines.extend([
            "## Recommended Migration Strategy",
            "",
            "### Phase 1: High Priority Migration",
            "1. Create new modular implementations for heavily-used legacy modules",
            "2. Update import statements in all importing files",
            "3. Test thoroughly after each module migration",
            "4. Remove legacy module after successful migration",
            "",
            "### Phase 2: Medium Priority Migration", 
            "1. Handle lightly-used legacy modules",
            "2. Combine similar modules where possible",
            "3. Update documentation and examples",
            "",
            "### Phase 3: Shim Cleanup",
            "1. Update import statements to use new module locations",
            "2. Remove shim files after import migration",
            "3. Run import-linter to verify clean module boundaries",
            "",
            "## Safety Recommendations",
            "",
            "- Always migrate modules with fewer dependencies first when possible",
            "- Create tests for new modular implementations before migration",
            "- Use deprecation warnings during transition period",
            "- Keep legacy modules temporarily for rollback safety",
            "- Monitor CI/CD pipeline for import-related failures",
            "",
            "---",
            "*Generated by import_dependency_analyzer.py*"
        ])
        
        return "\n".join(report_lines)

def main() -> None:
    """Main entry point."""
    import sys
    
    root_path = sys.argv[1] if len(sys.argv) > 1 else "."
    analyzer = ImportDependencyAnalyzer(root_path)
    
    analyzer.build_import_graph()
    
    # Generate migration report
    report = analyzer.generate_migration_report()
    report_path = Path(root_path) / "IMPORT_MIGRATION_PRIORITY_REPORT.md"
    
    report_path.write_text(report, encoding='utf-8')
    print(f"📄 Migration priority report saved: {report_path}")
    
    # Also save raw dependency data
    dependency_data = {
        "import_graph": dict(analyzer.import_graph),
        "reverse_import_graph": dict(analyzer.reverse_import_graph),
        "priorities": analyzer.prioritize_migration_targets()
    }
    
    json_path = Path(root_path) / "import_dependencies.json"
    json_path.write_text(json.dumps(dependency_data, indent=2), encoding='utf-8')
    print(f"📊 Raw dependency data saved: {json_path}")

if __name__ == "__main__":
    main()