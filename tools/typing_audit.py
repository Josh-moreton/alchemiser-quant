#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Typing architecture audit tool for the Alchemiser Trading System.

Performs comprehensive static analysis to enforce the typing architecture 
rules defined in .github/copilot-instructions.md. Detects violations of 
layer-specific type ownership, ANN401 misuse, and naming conventions.

Key Features:
- AST-based analysis for precise type annotation inspection
- Layer-specific type ownership validation
- Cross-module import boundary checking
- Integration with existing ruff/mypy toolchain
- JSON and Markdown report generation
"""

from __future__ import annotations

import ast
import json
import logging
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ViolationSeverity(Enum):
    """Severity levels for typing violations."""
    
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ViolationType(Enum):
    """Types of typing architecture violations."""
    
    # ANN401: Any usage violations
    ANN401_PARAM = "ANN401_PARAM"
    ANN401_RETURN = "ANN401_RETURN"
    ANN401_DTO_FIELD = "ANN401_DTO_FIELD"
    ANN401_PROTOCOL_METHOD = "ANN401_PROTOCOL_METHOD"
    
    # Layer-specific type ownership
    RAW_DICT_IN_BUSINESS_LOGIC = "RAW_DICT_IN_BUSINESS_LOGIC"
    SDK_OBJECT_IN_ORCHESTRATION = "SDK_OBJECT_IN_ORCHESTRATION"
    WRONG_TYPE_ACROSS_LAYERS = "WRONG_TYPE_ACROSS_LAYERS"
    
    # Naming conventions
    INCORRECT_NAMING_PATTERN = "INCORRECT_NAMING_PATTERN"
    MISSING_DTO_SUFFIX = "MISSING_DTO_SUFFIX"
    
    # Cross-module imports
    FORBIDDEN_CROSS_MODULE_IMPORT = "FORBIDDEN_CROSS_MODULE_IMPORT"
    DEEP_IMPORT_VIOLATION = "DEEP_IMPORT_VIOLATION"


@dataclass
class TypeViolation:
    """Represents a typing architecture violation."""
    
    file_path: str
    line_number: int
    column: int
    violation_type: ViolationType
    severity: ViolationSeverity
    message: str
    suggested_fix: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass 
class AuditReport:
    """Complete audit report with violations and statistics."""
    
    violations: list[TypeViolation] = field(default_factory=list)
    file_count: int = 0
    total_lines: int = 0
    violations_by_type: dict[ViolationType, int] = field(default_factory=dict)
    violations_by_severity: dict[ViolationSeverity, int] = field(default_factory=dict)
    

class TypeAnnotationVisitor(ast.NodeVisitor):
    """AST visitor for analyzing type annotations and detecting violations."""
    
    def __init__(self, file_path: str, source_lines: list[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: list[TypeViolation] = []
        self.current_class: Optional[str] = None
        self.in_dto_class = False
        self.in_protocol_class = False
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions to track context."""
        prev_class = self.current_class
        prev_dto = self.in_dto_class
        prev_protocol = self.in_protocol_class
        
        self.current_class = node.name
        self.in_dto_class = self._is_dto_class(node)
        self.in_protocol_class = self._is_protocol_class(node)
        
        # Check DTO naming conventions
        if self.in_dto_class and not node.name.endswith("DTO"):
            self.violations.append(TypeViolation(
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                violation_type=ViolationType.MISSING_DTO_SUFFIX,
                severity=ViolationSeverity.MEDIUM,
                message=f"DTO class '{node.name}' should end with 'DTO' suffix",
                suggested_fix=f"Rename to '{node.name}DTO'"
            ))
        
        self.generic_visit(node)
        
        # Restore previous context
        self.current_class = prev_class
        self.in_dto_class = prev_dto
        self.in_protocol_class = prev_protocol
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions to check parameters and return types."""
        # Check parameters for Any usage
        for arg in node.args.args:
            if arg.annotation:
                self._check_annotation_for_any(arg.annotation, arg.lineno, arg.col_offset, 
                                                f"parameter '{arg.arg}'")
        
        # Check return type for Any usage  
        if node.returns:
            self._check_annotation_for_any(node.returns, node.lineno, node.col_offset,
                                           "return type")
            
        # Check naming conventions for SDK methods
        self._check_method_naming_conventions(node)
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit annotated assignments (for DTO fields)."""
        if self.in_dto_class and node.annotation:
            target_name = ""
            if isinstance(node.target, ast.Name):
                target_name = node.target.id
            
            self._check_annotation_for_any(node.annotation, node.lineno, node.col_offset,
                                           f"DTO field '{target_name}'")
        
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import) -> None:
        """Check import statements for cross-module violations."""
        for alias in node.names:
            self._check_import_boundaries(alias.name, node.lineno)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check from-import statements for cross-module violations."""
        if node.module:
            self._check_import_boundaries(node.module, node.lineno)
        self.generic_visit(node)
    
    def _is_dto_class(self, node: ast.ClassDef) -> bool:
        """Check if class is a DTO based on inheritance and naming."""
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "BaseModel":
                return True
            if isinstance(base, ast.Attribute) and base.attr == "BaseModel":
                return True
        return node.name.endswith("DTO")
    
    def _is_protocol_class(self, node: ast.ClassDef) -> bool:
        """Check if class is a Protocol."""
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Protocol":
                return True
            if isinstance(base, ast.Attribute) and base.attr == "Protocol":
                return True
        return False
    
    def _check_annotation_for_any(self, annotation: ast.AST, line: int, col: int, context: str) -> None:
        """Check if annotation contains unbounded Any usage."""
        any_usage = self._find_any_usage(annotation)
        if any_usage:
            severity = self._get_any_violation_severity(context)
            
            self.violations.append(TypeViolation(
                file_path=self.file_path,
                line_number=line,
                column=col,
                violation_type=self._get_any_violation_type(context),
                severity=severity,
                message=f"Unbounded 'Any' usage in {context}",
                suggested_fix=self._suggest_any_replacement(annotation, context),
                context={"annotation": ast.unparse(annotation), "context": context}
            ))
    
    def _find_any_usage(self, node: ast.AST) -> bool:
        """Recursively find Any usage in type annotations."""
        if isinstance(node, ast.Name) and node.id == "Any":
            return True
        elif isinstance(node, ast.Attribute) and node.attr == "Any":
            return True
        elif hasattr(node, "_fields"):
            for field_name in node._fields:
                field_value = getattr(node, field_name, None)
                if isinstance(field_value, list):
                    for item in field_value:
                        if isinstance(item, ast.AST) and self._find_any_usage(item):
                            return True
                elif isinstance(field_value, ast.AST) and self._find_any_usage(field_value):
                    return True
        return False
    
    def _get_any_violation_severity(self, context: str) -> ViolationSeverity:
        """Determine severity based on context of Any usage."""
        if "DTO field" in context:
            return ViolationSeverity.HIGH
        elif "protocol" in context.lower():
            return ViolationSeverity.HIGH  
        elif "return type" in context:
            return ViolationSeverity.MEDIUM
        else:
            return ViolationSeverity.MEDIUM
    
    def _get_any_violation_type(self, context: str) -> ViolationType:
        """Determine violation type based on context."""
        if "parameter" in context:
            return ViolationType.ANN401_PARAM
        elif "return type" in context:
            return ViolationType.ANN401_RETURN
        elif "DTO field" in context:
            return ViolationType.ANN401_DTO_FIELD
        elif "protocol" in context.lower():
            return ViolationType.ANN401_PROTOCOL_METHOD
        else:
            return ViolationType.ANN401_PARAM
    
    def _suggest_any_replacement(self, annotation: ast.AST, context: str) -> str:
        """Suggest concrete replacement for Any usage."""
        if "DTO field" in context:
            return "Use concrete types: str | int | bool or dict[str, str] instead of Any"
        elif "parameter" in context:
            return "Use Union types or specific interfaces instead of Any"
        elif "return type" in context:
            return "Return specific DTO types or Optional[ConcreteType] instead of Any"
        else:
            return "Replace Any with concrete type annotations"
    
    def _check_method_naming_conventions(self, node: ast.FunctionDef) -> None:
        """Check method naming conventions for SDK adapters."""
        # Check for _get_*_raw pattern
        if node.name.startswith("_get_") and node.name.endswith("_raw"):
            # This is correct pattern for SDK methods
            return
            
        # Check for get_* methods that should return DTOs
        if node.name.startswith("get_") and not node.name.endswith("_dict"):
            if node.returns and self._returns_any_or_dict(node.returns):
                self.violations.append(TypeViolation(
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column=node.col_offset,
                    violation_type=ViolationType.INCORRECT_NAMING_PATTERN,
                    severity=ViolationSeverity.MEDIUM,
                    message=f"Method '{node.name}' should return DTO, not Any/dict",
                    suggested_fix="Return specific DTO type or rename to get_*_dict() for serialization"
                ))
    
    def _returns_any_or_dict(self, return_annotation: ast.AST) -> bool:
        """Check if return annotation is Any or generic dict."""
        return (
            self._find_any_usage(return_annotation) or
            self._is_generic_dict(return_annotation)
        )
    
    def _is_generic_dict(self, annotation: ast.AST) -> bool:
        """Check if annotation is dict[str, Any] or similar generic dict."""
        if isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name) and annotation.value.id == "dict":
                # Check if it's dict[str, Any]
                if isinstance(annotation.slice, ast.Tuple) and len(annotation.slice.elts) == 2:
                    _, value_type = annotation.slice.elts
                    return self._find_any_usage(value_type)
        return False
    
    def _check_import_boundaries(self, module_name: str, line_number: int) -> None:
        """Check for forbidden cross-module imports."""
        if not module_name.startswith("the_alchemiser"):
            return
            
        file_module = self._get_module_from_path(self.file_path)
        imported_module = self._get_module_from_import(module_name)
        
        if self._is_forbidden_import(file_module, imported_module):
            self.violations.append(TypeViolation(
                file_path=self.file_path,
                line_number=line_number,
                column=0,
                violation_type=ViolationType.FORBIDDEN_CROSS_MODULE_IMPORT,
                severity=ViolationSeverity.HIGH,
                message=f"Forbidden import from {file_module} to {imported_module}",
                suggested_fix="Use shared DTOs/events for cross-module communication",
                context={"from_module": file_module, "to_module": imported_module}
            ))
    
    def _get_module_from_path(self, file_path: str) -> str:
        """Extract module name from file path."""
        path = Path(file_path)
        if "the_alchemiser" in path.parts:
            idx = path.parts.index("the_alchemiser")
            if idx + 1 < len(path.parts):
                return path.parts[idx + 1]
        return "unknown"
    
    def _get_module_from_import(self, import_name: str) -> str:
        """Extract module name from import statement."""
        parts = import_name.split(".")
        if len(parts) >= 2 and parts[0] == "the_alchemiser":
            return parts[1]
        return "unknown"
    
    def _is_forbidden_import(self, from_module: str, to_module: str) -> bool:
        """Check if import violates module boundary rules."""
        business_modules = {"strategy_v2", "portfolio_v2", "execution_v2"}
        
        # Shared module cannot import from business modules
        if from_module == "shared" and to_module in business_modules:
            return True
            
        # Business modules cannot import from each other (except orchestration)
        if (from_module in business_modules and 
            to_module in business_modules and 
            from_module != to_module):
            return True
            
        return False


class TypingAuditor:
    """Main typing architecture auditor."""
    
    def __init__(self, root_path: str | Path):
        self.root_path = Path(root_path)
        self.report = AuditReport()
    
    def audit_directory(self, directory: str = "the_alchemiser") -> AuditReport:
        """Perform comprehensive typing audit on directory."""
        target_dir = self.root_path / directory
        
        if not target_dir.exists():
            logger.error(f"Directory {target_dir} does not exist")
            return self.report
        
        python_files = list(target_dir.rglob("*.py"))
        self.report.file_count = len(python_files)
        
        logger.info(f"Auditing {self.report.file_count} Python files in {target_dir}")
        
        for file_path in python_files:
            self._audit_file(file_path)
        
        self._calculate_statistics()
        return self.report
    
    def _audit_file(self, file_path: Path) -> None:
        """Audit a single Python file for typing violations."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
                source_lines = source_code.splitlines()
                
            self.report.total_lines += len(source_lines)
            
            # Parse AST and run visitor
            tree = ast.parse(source_code, filename=str(file_path))
            visitor = TypeAnnotationVisitor(str(file_path), source_lines)
            visitor.visit(tree)
            
            self.report.violations.extend(visitor.violations)
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
    
    def _calculate_statistics(self) -> None:
        """Calculate violation statistics."""
        for violation in self.report.violations:
            # Count by type
            if violation.violation_type in self.report.violations_by_type:
                self.report.violations_by_type[violation.violation_type] += 1
            else:
                self.report.violations_by_type[violation.violation_type] = 1
                
            # Count by severity
            if violation.severity in self.report.violations_by_severity:
                self.report.violations_by_severity[violation.severity] += 1
            else:
                self.report.violations_by_severity[violation.severity] = 1


class ReportGenerator:
    """Generate violation reports in multiple formats."""
    
    def __init__(self, report: AuditReport):
        self.report = report
    
    def generate_json_report(self, output_path: str | Path) -> None:
        """Generate JSON violation report."""
        output_path = Path(output_path)
        
        report_data = {
            "summary": {
                "total_violations": len(self.report.violations),
                "files_analyzed": self.report.file_count,
                "lines_analyzed": self.report.total_lines,
                "violations_by_severity": {
                    sev.value: count for sev, count in self.report.violations_by_severity.items()
                },
                "violations_by_type": {
                    vtype.value: count for vtype, count in self.report.violations_by_type.items()
                }
            },
            "violations": [
                {
                    "file": v.file_path,
                    "line": v.line_number,
                    "column": v.column,
                    "type": v.violation_type.value,
                    "severity": v.severity.value,
                    "message": v.message,
                    "suggested_fix": v.suggested_fix,
                    "context": v.context
                }
                for v in self.report.violations
            ]
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"JSON report written to {output_path}")
    
    def generate_markdown_report(self, output_path: str | Path) -> None:
        """Generate Markdown summary report."""
        output_path = Path(output_path)
        
        with open(output_path, "w", encoding="utf-8") as f:
            self._write_markdown_header(f)
            self._write_summary_stats(f)
            self._write_violations_by_severity(f)
            self._write_violations_by_type(f)
            self._write_detailed_violations(f)
        
        logger.info(f"Markdown report written to {output_path}")
    
    def _write_markdown_header(self, f) -> None:
        """Write markdown header."""
        f.write("# Typing Architecture Audit Report\n\n")
        f.write("Comprehensive analysis of typing architecture compliance across the codebase.\n\n")
    
    def _write_summary_stats(self, f) -> None:
        """Write summary statistics."""
        f.write("## Summary\n\n")
        f.write(f"- **Total Violations**: {len(self.report.violations)}\n")
        f.write(f"- **Files Analyzed**: {self.report.file_count}\n")
        f.write(f"- **Lines of Code**: {self.report.total_lines:,}\n\n")
    
    def _write_violations_by_severity(self, f) -> None:
        """Write violations grouped by severity."""
        f.write("## Violations by Severity\n\n")
        
        for severity in [ViolationSeverity.CRITICAL, ViolationSeverity.HIGH, 
                        ViolationSeverity.MEDIUM, ViolationSeverity.LOW]:
            count = self.report.violations_by_severity.get(severity, 0)
            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}[severity.value]
            f.write(f"- {emoji} **{severity.value}**: {count}\n")
        f.write("\n")
    
    def _write_violations_by_type(self, f) -> None:
        """Write violations grouped by type."""
        f.write("## Violations by Type\n\n")
        
        for vtype, count in sorted(self.report.violations_by_type.items(), 
                                  key=lambda x: x[1], reverse=True):
            f.write(f"- **{vtype.value}**: {count}\n")
        f.write("\n")
    
    def _write_detailed_violations(self, f) -> None:
        """Write detailed violation list."""
        f.write("## Detailed Violations\n\n")
        
        # Group by severity for display
        by_severity = {}
        for violation in self.report.violations:
            if violation.severity not in by_severity:
                by_severity[violation.severity] = []
            by_severity[violation.severity].append(violation)
        
        for severity in [ViolationSeverity.CRITICAL, ViolationSeverity.HIGH,
                        ViolationSeverity.MEDIUM, ViolationSeverity.LOW]:
            violations = by_severity.get(severity, [])
            if not violations:
                continue
                
            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}[severity.value]
            f.write(f"### {emoji} {severity.value} Violations\n\n")
            
            for v in violations[:10]:  # Limit to first 10 per severity
                f.write(f"**{v.file_path}:{v.line_number}**\n")
                f.write(f"- Type: `{v.violation_type.value}`\n")
                f.write(f"- Message: {v.message}\n")
                f.write(f"- Fix: {v.suggested_fix}\n\n")
            
            if len(violations) > 10:
                f.write(f"... and {len(violations) - 10} more\n\n")


def main() -> int:
    """Main entry point for typing audit."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Setup paths
    root_path = Path(__file__).parent.parent
    report_dir = root_path / "report"
    report_dir.mkdir(exist_ok=True)
    
    # Run audit
    auditor = TypingAuditor(root_path)
    report = auditor.audit_directory("the_alchemiser")
    
    # Generate reports
    generator = ReportGenerator(report)
    generator.generate_json_report(report_dir / "typing_violations.json")
    generator.generate_markdown_report(report_dir / "typing_summary.md")
    
    # Print summary
    print(f"\n📊 Typing Architecture Audit Complete")
    print(f"Files analyzed: {report.file_count}")
    print(f"Total violations: {len(report.violations)}")
    
    if report.violations_by_severity.get(ViolationSeverity.CRITICAL, 0) > 0:
        print(f"🔴 CRITICAL violations: {report.violations_by_severity[ViolationSeverity.CRITICAL]}")
        return 1
    elif report.violations_by_severity.get(ViolationSeverity.HIGH, 0) > 0:
        print(f"🟠 HIGH violations: {report.violations_by_severity[ViolationSeverity.HIGH]}")
        return 1
    else:
        print("✅ No critical or high-severity violations found")
        return 0


if __name__ == "__main__":
    sys.exit(main())