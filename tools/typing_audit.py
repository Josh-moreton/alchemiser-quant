#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Typing Architecture Audit Tool for Alchemiser Quant.

This script audits the entire codebase against typing architecture rules
defined in TYPING_ARCHITECTURE_RULES.md and generates comprehensive reports.

Key Features:
- AST-based violation detection
- Layer-specific type ownership validation
- ANN401 (Any) usage analysis
- Severity-based prioritization
- JSON and Markdown report generation

Part of the project-wide typing enforcement initiative.
"""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class Severity(Enum):
    """Violation severity levels."""
    
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleType(Enum):
    """Types of typing architecture rules."""
    
    ANN401_VIOLATION = "ANN401_VIOLATION"
    LAYER_TYPE_VIOLATION = "LAYER_TYPE_VIOLATION"
    CONVERSION_POINT_VIOLATION = "CONVERSION_POINT_VIOLATION"
    NAMING_CONVENTION_VIOLATION = "NAMING_CONVENTION_VIOLATION"
    PROTOCOL_TYPING_VIOLATION = "PROTOCOL_TYPING_VIOLATION"


@dataclass
class Violation:
    """Represents a typing architecture violation."""
    
    file_path: str
    line_number: int
    rule_type: RuleType
    severity: Severity
    description: str
    suggested_fix: str
    code_context: str


class TypeAnnotationVisitor(ast.NodeVisitor):
    """AST visitor to detect typing violations."""
    
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.violations: list[Violation] = []
        self.current_class: str | None = None
        self.in_protocol: bool = False
        self.source_lines: list[str] = []  # Will be set by auditor
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions to detect protocol classes."""
        self.current_class = node.name
        
        # Check if this is a Protocol class
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Protocol":
                self.in_protocol = True
            elif isinstance(base, ast.Attribute) and base.attr == "Protocol":
                self.in_protocol = True
                
        self.generic_visit(node)
        
        self.current_class = None
        self.in_protocol = False
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions to check type annotations."""
        # Check for Any in parameters
        for arg in node.args.args:
            if self._has_any_annotation(arg.annotation) and not self._is_explicitly_allowed(node.lineno):
                severity = self._get_any_severity(node.name, is_protocol=self.in_protocol)
                self.violations.append(Violation(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    rule_type=RuleType.ANN401_VIOLATION,
                    severity=severity,
                    description=f"Parameter '{arg.arg}' uses 'Any' type annotation",
                    suggested_fix=self._suggest_any_replacement(arg.arg, "parameter"),
                    code_context=self._extract_code_context(node),
                ))
                
        # Check for Any in return type
        if self._has_any_annotation(node.returns) and not self._is_explicitly_allowed(node.lineno):
            severity = self._get_any_severity(node.name, is_protocol=self.in_protocol, is_return=True)
            self.violations.append(Violation(
                file_path=self.file_path,
                line_number=node.lineno,
                rule_type=RuleType.ANN401_VIOLATION,
                severity=severity,
                description=f"Function '{node.name}' returns 'Any' type",
                suggested_fix=self._suggest_return_type_fix(node.name),
                code_context=self._extract_code_context(node),
            ))
            
        # Check for dict[str, Any] in business logic
        if self._returns_dict_str_any(node.returns) and self._is_business_logic_function(node.name):
            self.violations.append(Violation(
                file_path=self.file_path,
                line_number=node.lineno,
                rule_type=RuleType.LAYER_TYPE_VIOLATION,
                severity=Severity.HIGH,
                description=f"Business logic function '{node.name}' returns dict[str, Any] instead of DTO",
                suggested_fix=f"Return specific DTO type instead of dict[str, Any]",
                code_context=self._extract_code_context(node),
            ))
            
        self.generic_visit(node)
        
    def _has_any_annotation(self, annotation: ast.AST | None) -> bool:
        """Check if annotation uses Any type."""
        if annotation is None:
            return False
            
        if isinstance(annotation, ast.Name) and annotation.id == "Any":
            return True
            
        if isinstance(annotation, ast.Attribute) and annotation.attr == "Any":
            return True
            
        # Check for Union with Any
        if isinstance(annotation, ast.Subscript):
            if isinstance(annotation.slice, ast.Tuple):
                for elt in annotation.slice.elts:
                    if self._has_any_annotation(elt):
                        return True
                        
        return False
        
    def _returns_dict_str_any(self, annotation: ast.AST | None) -> bool:
        """Check if annotation is dict[str, Any]."""
        if annotation is None:
            return False
            
        if isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name) and annotation.value.id == "dict":
                if isinstance(annotation.slice, ast.Tuple) and len(annotation.slice.elts) == 2:
                    key_type, value_type = annotation.slice.elts
                    if (isinstance(key_type, ast.Name) and key_type.id == "str" and
                        self._has_any_annotation(value_type)):
                        return True
                        
        return False
        
    def _get_any_severity(self, func_name: str, is_protocol: bool = False, is_return: bool = False) -> Severity:
        """Determine severity of Any usage based on context."""
        # AWS Lambda handlers are acceptable
        if func_name == "lambda_handler":
            return Severity.LOW
            
        # Protocol methods with proper documentation are medium priority
        if is_protocol or self.file_path.endswith("protocol.py") or "protocol" in self.file_path:
            return Severity.MEDIUM if is_return else Severity.MEDIUM
            
        # Business logic methods are high priority
        if self._is_business_logic_function(func_name):
            return Severity.HIGH
            
        # Error handlers and utilities are medium priority
        if "error" in func_name.lower() or "handler" in func_name.lower():
            return Severity.MEDIUM
            
        return Severity.MEDIUM
        
    def _is_business_logic_function(self, func_name: str) -> bool:
        """Check if function is business logic that should use DTOs."""
        business_patterns = [
            "analyze_", "execute_", "process_", "calculate_", "generate_",
            "get_account", "get_portfolio", "get_signals", "get_positions"
        ]
        return any(pattern in func_name for pattern in business_patterns)
        
    def _suggest_any_replacement(self, param_name: str, context: str) -> str:
        """Suggest specific type replacement for Any."""
        if "signal" in param_name.lower():
            return "Use StrategySignalDTO for signal parameters"
        elif "account" in param_name.lower():
            return "Use AccountInfoDTO for account parameters"
        elif "portfolio" in param_name.lower():
            return "Use PortfolioStateDTO for portfolio parameters"
        elif "data" in param_name.lower():
            return "Use specific DTO or Union of known types instead of Any"
        else:
            return f"Replace Any with specific type or Union for {context}"
            
    def _suggest_return_type_fix(self, func_name: str) -> str:
        """Suggest specific return type fix."""
        if "analyze" in func_name or "account" in func_name:
            return "Return specific DTO (AccountInfoDTO, PortfolioStateDTO, etc.)"
        elif "execute" in func_name or "signal" in func_name:
            return "Return ExecutionReportDTO or StrategySignalDTO"
        else:
            return "Return specific DTO instead of Any"
            
    def _extract_code_context(self, node: ast.AST) -> str:
        """Extract code context for violation."""
        try:
            # This is a simplified version - in practice you'd want to 
            # read the actual source file to get the exact code
            return f"Line {node.lineno}: Function definition"
        except Exception:
            return "Code context unavailable"
            
    def _is_explicitly_allowed(self, line_number: int) -> bool:
        """Check if Any usage is explicitly allowed with noqa comment."""
        if not self.source_lines or line_number > len(self.source_lines):
            return False
            
        # Check the line itself and nearby lines for noqa comment
        for offset in [0, -1, 1]:  # Check current line and adjacent lines
            check_line = line_number + offset - 1  # Convert to 0-based index
            if 0 <= check_line < len(self.source_lines):
                line = self.source_lines[check_line]
                if "# noqa: ANN401" in line or "# type: ignore[misc]" in line:
                    return True
                    
        return False


class TypingAuditor:
    """Main typing architecture auditor."""
    
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path
        self.violations: list[Violation] = []
        
    def audit_file(self, file_path: Path) -> None:
        """Audit a single Python file for typing violations."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            visitor = TypeAnnotationVisitor(str(file_path.relative_to(self.root_path)))
            visitor.source_lines = content.split('\n')  # Pass source for context checking
            visitor.visit(tree)
            
            self.violations.extend(visitor.violations)
            
        except Exception as e:
            print(f"Error auditing {file_path}: {e}", file=sys.stderr)
            
    def audit_directory(self, directory: Path) -> None:
        """Recursively audit all Python files in directory."""
        for file_path in directory.rglob("*.py"):
            # Skip certain directories
            if any(part.startswith('.') for part in file_path.parts):
                continue
            if '__pycache__' in str(file_path):
                continue
                
            self.audit_file(file_path)
            
    def generate_report(self) -> dict[str, Any]:
        """Generate comprehensive audit report."""
        # Group violations by severity
        by_severity = {}
        for severity in Severity:
            by_severity[severity.value] = [
                v for v in self.violations if v.severity == severity
            ]
            
        # Group violations by rule type
        by_rule_type = {}
        for rule_type in RuleType:
            by_rule_type[rule_type.value] = [
                v for v in self.violations if v.rule_type == rule_type
            ]
            
        # Summary statistics
        total_violations = len(self.violations)
        files_with_violations = len(set(v.file_path for v in self.violations))
        
        return {
            "summary": {
                "total_violations": total_violations,
                "files_with_violations": files_with_violations,
                "by_severity": {k: len(v) for k, v in by_severity.items()},
                "by_rule_type": {k: len(v) for k, v in by_rule_type.items()},
            },
            "violations": [
                {
                    "file_path": v.file_path,
                    "line_number": v.line_number,
                    "rule_type": v.rule_type.value,
                    "severity": v.severity.value,
                    "description": v.description,
                    "suggested_fix": v.suggested_fix,
                    "code_context": v.code_context,
                }
                for v in sorted(self.violations, key=lambda x: (x.severity.value, x.file_path, x.line_number))
            ]
        }
        
    def save_json_report(self, output_path: Path) -> None:
        """Save audit report as JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.generate_report(), f, indent=2)
            
    def save_markdown_report(self, output_path: Path) -> None:
        """Save audit report as Markdown summary."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = self.generate_report()
        
        with open(output_path, 'w') as f:
            f.write("# Typing Architecture Audit Report\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Total Violations:** {report['summary']['total_violations']}\n")
            f.write(f"- **Files Affected:** {report['summary']['files_with_violations']}\n\n")
            
            # By Severity
            f.write("### Violations by Severity\n\n")
            for severity, count in report['summary']['by_severity'].items():
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
                f.write(f"- {icon} **{severity}:** {count}\n")
            f.write("\n")
            
            # By Rule Type
            f.write("### Violations by Rule Type\n\n")
            for rule_type, count in report['summary']['by_rule_type'].items():
                f.write(f"- **{rule_type.replace('_', ' ').title()}:** {count}\n")
            f.write("\n")
            
            # Top Violations by Severity
            for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                violations = [v for v in report['violations'] if v['severity'] == severity]
                if violations:
                    icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}[severity]
                    f.write(f"## {icon} {severity} Priority Violations\n\n")
                    
                    for v in violations[:10]:  # Show top 10 per severity
                        f.write(f"### {v['file_path']}:{v['line_number']}\n\n")
                        f.write(f"**Issue:** {v['description']}\n\n")
                        f.write(f"**Suggested Fix:** {v['suggested_fix']}\n\n")
                        f.write("---\n\n")


def main() -> None:
    """Main entry point for typing audit."""
    if len(sys.argv) < 2:
        print("Usage: python typing_audit.py <directory_path>")
        sys.exit(1)
        
    directory_path = Path(sys.argv[1])
    if not directory_path.exists():
        print(f"Directory not found: {directory_path}")
        sys.exit(1)
        
    auditor = TypingAuditor(directory_path)
    auditor.audit_directory(directory_path)
    
    # Generate reports
    report_dir = Path("report")
    auditor.save_json_report(report_dir / "typing_violations.json")
    auditor.save_markdown_report(report_dir / "typing_summary.md")
    
    print(f"Audit complete. Reports saved to {report_dir}/")
    
    # Print summary
    report = auditor.generate_report()
    print(f"\nSummary:")
    print(f"  Total violations: {report['summary']['total_violations']}")
    print(f"  Files affected: {report['summary']['files_with_violations']}")
    
    for severity, count in report['summary']['by_severity'].items():
        if count > 0:
            print(f"  {severity}: {count}")


if __name__ == "__main__":
    main()