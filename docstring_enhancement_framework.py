#!/usr/bin/env python3
"""Comprehensive docstring enhancement guide and tools for The Alchemiser.

This script provides tools and templates for continuing the systematic
docstring enhancement across the codebase.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List


def get_google_style_templates() -> Dict[str, str]:
    """Get templates for Google-style docstrings."""
    return {
        "module": '''"""Business Unit: {business_unit} | Status: current.

{short_description}

{detailed_description}
"""''',
        
        "class": '''"""Short description of the class.

Detailed description explaining the purpose, responsibilities,
and how this class fits into the overall system.

Attributes:
    attribute_name: Description of the attribute.
    another_attr: Description of another attribute.

Example:
    >>> instance = ClassName(param1, param2)
    >>> result = instance.method_name()
    >>> print(result)
"""''',

        "function": '''"""Short description of what the function does.

Detailed description explaining the purpose, algorithm,
and any important implementation details.

Args:
    param1: Description of first parameter.
    param2: Description of second parameter.
    optional_param: Description of optional parameter. Defaults to None.

Returns:
    Description of return value and its type.

Raises:
    ValueError: When input validation fails.
    TypeError: When wrong type is provided.

Example:
    >>> result = function_name(arg1, arg2)
    >>> print(result)
"""''',

        "method": '''"""Short description of what the method does.

Detailed description explaining the purpose and how it
interacts with the class state.

Args:
    param1: Description of parameter.

Returns:
    Description of return value.

Raises:
    Exception: When something goes wrong.
"""'''
    }


def get_business_unit_descriptions() -> Dict[str, str]:
    """Get standard descriptions for each business unit."""
    return {
        "strategy": "Signal generation and indicator calculation for trading strategies.",
        "portfolio": "Portfolio state management and rebalancing logic.",
        "execution": "Broker API integrations and order placement.",
        "shared": "DTOs, utilities, and cross-cutting concerns."
    }


def determine_business_unit(file_path: Path) -> str:
    """Determine business unit from file path."""
    parts = file_path.parts
    if "strategy" in parts:
        return "strategy"
    elif "portfolio" in parts:
        return "portfolio"
    elif "execution" in parts:
        return "execution"
    elif "shared" in parts:
        return "shared"
    return "shared"  # Default fallback


def analyze_python_file(file_path: Path) -> Dict:
    """Analyze a Python file for docstring enhancement opportunities."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        analysis = {
            "file_path": str(file_path),
            "business_unit": determine_business_unit(file_path),
            "has_module_docstring": bool(ast.get_docstring(tree)),
            "missing_docstrings": [],
            "existing_docstrings": [],
        }
        
        # Check module docstring
        if not analysis["has_module_docstring"]:
            analysis["missing_docstrings"].append({
                "type": "module",
                "name": file_path.name,
                "line": 1
            })
        
        # Check classes and functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node)
                if not docstring:
                    analysis["missing_docstrings"].append({
                        "type": "function",
                        "name": node.name,
                        "line": node.lineno
                    })
                else:
                    analysis["existing_docstrings"].append({
                        "type": "function",
                        "name": node.name,
                        "docstring": docstring[:100] + "..." if len(docstring) > 100 else docstring
                    })
            
            elif isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                if not docstring:
                    analysis["missing_docstrings"].append({
                        "type": "class",
                        "name": node.name,
                        "line": node.lineno
                    })
                else:
                    analysis["existing_docstrings"].append({
                        "type": "class",
                        "name": node.name,
                        "docstring": docstring[:100] + "..." if len(docstring) > 100 else docstring
                    })
        
        return analysis
        
    except Exception as e:
        return {
            "file_path": str(file_path),
            "error": str(e),
            "missing_docstrings": [],
            "existing_docstrings": []
        }


def find_priority_files(base_path: str = "the_alchemiser", limit: int = 20) -> List[Dict]:
    """Find files with the most missing docstrings."""
    base_path = Path(base_path)
    analyses = []
    
    for py_file in base_path.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        
        analysis = analyze_python_file(py_file)
        if analysis["missing_docstrings"]:
            analyses.append(analysis)
    
    # Sort by number of missing docstrings
    analyses.sort(key=lambda x: len(x["missing_docstrings"]), reverse=True)
    return analyses[:limit]


def generate_enhancement_report(output_file: str = "docstring_enhancement_report.md"):
    """Generate a comprehensive enhancement report."""
    priority_files = find_priority_files()
    templates = get_google_style_templates()
    business_units = get_business_unit_descriptions()
    
    with open(output_file, 'w') as f:
        f.write("# Docstring Enhancement Report\n\n")
        f.write("## Priority Files for Enhancement\n\n")
        
        for i, analysis in enumerate(priority_files, 1):
            f.write(f"### {i}. {analysis['file_path']}\n")
            f.write(f"**Business Unit**: {analysis['business_unit']}\n")
            f.write(f"**Missing Docstrings**: {len(analysis['missing_docstrings'])}\n\n")
            
            if analysis['missing_docstrings']:
                f.write("**Missing:**\n")
                for missing in analysis['missing_docstrings']:
                    f.write(f"- {missing['type'].title()}: `{missing['name']}` (line {missing['line']})\n")
                f.write("\n")
        
        f.write("\n## Google-Style Templates\n\n")
        for template_type, template in templates.items():
            f.write(f"### {template_type.title()} Template\n\n")
            f.write("```python\n")
            f.write(template)
            f.write("\n```\n\n")
        
        f.write("## Business Unit Descriptions\n\n")
        for unit, description in business_units.items():
            f.write(f"- **{unit}**: {description}\n")
    
    print(f"Enhancement report generated: {output_file}")
    return output_file


def validate_docstring_format(docstring: str) -> List[str]:
    """Validate docstring follows Google style format."""
    issues = []
    
    if not docstring:
        issues.append("Missing docstring")
        return issues
    
    lines = docstring.strip().split('\n')
    
    # Check for summary line
    if not lines[0].strip():
        issues.append("First line should be a summary")
    
    # Check for period at end of summary
    if lines[0].strip() and not lines[0].strip().endswith('.'):
        issues.append("Summary line should end with period")
    
    # Check for blank line after summary if there's more content
    if len(lines) > 1 and lines[1].strip():
        issues.append("Should have blank line after summary")
    
    # Check for common sections
    content = docstring.lower()
    if 'args:' in content or 'arguments:' in content:
        if 'returns:' not in content and 'yields:' not in content:
            issues.append("Has Args section but missing Returns section")
    
    return issues


def main():
    """Main function to run docstring analysis and generate report."""
    print("🔍 Analyzing codebase for docstring enhancement opportunities...")
    
    # Generate comprehensive report
    report_file = generate_enhancement_report()
    
    # Show summary
    priority_files = find_priority_files(limit=10)
    print(f"\n📊 Top 10 files needing docstring enhancement:")
    for i, analysis in enumerate(priority_files, 1):
        rel_path = analysis['file_path'].replace('the_alchemiser/', '')
        missing_count = len(analysis['missing_docstrings'])
        print(f"{i:2d}. {rel_path:<50} ({missing_count} missing)")
    
    print(f"\n📝 Full report generated: {report_file}")
    print("\n💡 Next steps:")
    print("1. Review the generated report")
    print("2. Use the templates to enhance high-priority files")
    print("3. Run 'poetry run ruff check --select D' to validate")
    print("4. Focus on files with 5+ missing docstrings first")


if __name__ == "__main__":
    main()