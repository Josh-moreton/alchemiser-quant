#!/usr/bin/env python3
"""
Migration script for UnifiedDataProvider refactoring.

This script helps migrate from the monolithic UnifiedDataProvider to the
service-based architecture. It can be run in stages to ensure a smooth transition.
"""

import os
import re
import sys
from pathlib import Path


class DataProviderMigrator:
    """Handles migration from monolithic to service-based architecture."""

    def __init__(self, project_root: str):
        """
        Initialize migrator.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.backup_suffix = ".migration_backup"

    def find_usage_files(self) -> list[Path]:
        """
        Find all Python files that import UnifiedDataProvider.

        Returns:
            List of file paths that use UnifiedDataProvider
        """
        usage_files = []

        # Search pattern for UnifiedDataProvider imports
        import_pattern = re.compile(r"from\s+.*data_provider\s+import\s+.*UnifiedDataProvider")

        # Walk through Python files
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith(".") or "migration" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                    if import_pattern.search(content):
                        usage_files.append(py_file)
            except Exception as e:
                print(f"Warning: Could not read {py_file}: {e}")

        return usage_files

    def analyze_usage(self, file_path: Path) -> dict:
        """
        Analyze how UnifiedDataProvider is used in a file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Dictionary with usage information
        """
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        analysis = {
            "file_path": file_path,
            "import_lines": [],
            "instantiation_lines": [],
            "method_calls": [],
            "constructor_patterns": [],
        }

        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Find import statements
            if "UnifiedDataProvider" in line and ("import" in line or "from" in line):
                analysis["import_lines"].append((i, line.strip()))

            # Find instantiations
            if "UnifiedDataProvider(" in line:
                analysis["instantiation_lines"].append((i, line.strip()))

                # Extract constructor parameters
                constructor_match = re.search(r"UnifiedDataProvider\((.*?)\)", line)
                if constructor_match:
                    params = constructor_match.group(1)
                    analysis["constructor_patterns"].append(params)

            # Find method calls (looking for common patterns)
            method_patterns = [
                "get_data",
                "get_current_price",
                "get_account_info",
                "get_positions",
                "get_latest_quote",
                "get_orders",
                "place_order",
            ]

            for method in method_patterns:
                if f".{method}(" in line:
                    analysis["method_calls"].append((i, method, line.strip()))

        return analysis

    def create_backup(self, file_path: Path) -> Path:
        """
        Create a backup of the original file.

        Args:
            file_path: Path to file to backup

        Returns:
            Path to backup file
        """
        backup_path = file_path.with_suffix(file_path.suffix + self.backup_suffix)

        with open(file_path, encoding="utf-8") as original:
            content = original.read()

        with open(backup_path, "w", encoding="utf-8") as backup:
            backup.write(content)

        return backup_path

    def migrate_to_facade(self, file_path: Path, dry_run: bool = True) -> bool:
        """
        Migrate a file to use the facade instead of the original.

        Args:
            file_path: Path to file to migrate
            dry_run: If True, only show what would be changed

        Returns:
            True if migration was successful
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Replace import statement
            old_import = re.compile(
                r"from\s+the_alchemiser\.core\.data\.data_provider\s+import\s+UnifiedDataProvider"
            )
            new_import = "from the_alchemiser.core.data.unified_data_provider_facade import UnifiedDataProvider"

            new_content = old_import.sub(new_import, content)

            if dry_run:
                if new_content != content:
                    print(f"Would update import in: {file_path}")
                    print(f"  From: {old_import.pattern}")
                    print(f"  To:   {new_import}")
                return True
            else:
                if new_content != content:
                    # Create backup first
                    backup_path = self.create_backup(file_path)
                    print(f"Created backup: {backup_path}")

                    # Write updated content
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Updated: {file_path}")
                    return True
                else:
                    print(f"No changes needed: {file_path}")
                    return False

        except Exception as e:
            print(f"Error migrating {file_path}: {e}")
            return False

    def migrate_to_services(self, file_path: Path, dry_run: bool = True) -> bool:
        """
        Migrate a file to use individual services (advanced migration).

        Args:
            file_path: Path to file to migrate
            dry_run: If True, only show what would be changed

        Returns:
            True if migration was successful
        """
        analysis = self.analyze_usage(file_path)

        if dry_run:
            print(f"\nAdvanced migration analysis for: {file_path}")
            print(f"  Constructor patterns: {analysis['constructor_patterns']}")
            print(f"  Method calls: {[method for _, method, _ in analysis['method_calls']]}")

            # Suggest specific services based on usage
            methods_used = {method for _, method, _ in analysis["method_calls"]}

            suggested_services = []
            if any(
                m in methods_used for m in ["get_data", "get_current_price", "get_latest_quote"]
            ):
                suggested_services.append("MarketDataClient")
            if any(m in methods_used for m in ["get_account_info", "get_positions"]):
                suggested_services.append("AccountService")
            if any(m in methods_used for m in ["get_orders", "place_order"]):
                suggested_services.append("TradingClientService")

            print(f"  Suggested services: {suggested_services}")
            return True
        else:
            print(f"Advanced migration not implemented yet for: {file_path}")
            return False

    def generate_migration_report(self) -> str:
        """
        Generate a comprehensive migration report.

        Returns:
            Formatted migration report
        """
        usage_files = self.find_usage_files()

        report = []
        report.append("# UnifiedDataProvider Migration Report")
        report.append(f"Generated: {os.popen('date').read().strip()}")
        report.append(f"Project root: {self.project_root}")
        report.append(f"Files found: {len(usage_files)}")
        report.append("")

        for file_path in usage_files:
            analysis = self.analyze_usage(file_path)

            report.append(f"## {file_path.relative_to(self.project_root)}")
            report.append("")

            if analysis["import_lines"]:
                report.append("### Imports")
                for line_num, line in analysis["import_lines"]:
                    report.append(f"- Line {line_num}: `{line}`")
                report.append("")

            if analysis["instantiation_lines"]:
                report.append("### Instantiations")
                for line_num, line in analysis["instantiation_lines"]:
                    report.append(f"- Line {line_num}: `{line}`")
                report.append("")

            if analysis["method_calls"]:
                report.append("### Method Calls")
                methods_summary = {}
                for line_num, method, line in analysis["method_calls"]:
                    if method not in methods_summary:
                        methods_summary[method] = []
                    methods_summary[method].append(line_num)

                for method, lines in methods_summary.items():
                    report.append(f"- `{method}()`: Lines {', '.join(map(str, lines))}")
                report.append("")

            report.append("---")
            report.append("")

        return "\n".join(report)


def main():
    """Main migration script entry point."""
    if len(sys.argv) < 2:
        print("Usage: python migration_script.py <command> [options]")
        print("Commands:")
        print("  analyze     - Analyze current usage")
        print("  report      - Generate migration report")
        print("  facade      - Migrate to facade (safe)")
        print("  services    - Migrate to individual services (advanced)")
        print("  dry-run     - Show what would be changed")
        return

    command = sys.argv[1]
    project_root = os.getcwd()

    migrator = DataProviderMigrator(project_root)

    if command == "analyze":
        usage_files = migrator.find_usage_files()
        print(f"Found {len(usage_files)} files using UnifiedDataProvider:")
        for file_path in usage_files:
            print(f"  {file_path.relative_to(migrator.project_root)}")

    elif command == "report":
        report = migrator.generate_migration_report()
        report_file = Path("migration_report.md")
        with open(report_file, "w") as f:
            f.write(report)
        print(f"Migration report saved to: {report_file}")

    elif command == "facade":
        dry_run = "--dry-run" in sys.argv
        usage_files = migrator.find_usage_files()
        print(f"Migrating {len(usage_files)} files to facade...")

        for file_path in usage_files:
            migrator.migrate_to_facade(file_path, dry_run=dry_run)

    elif command == "services":
        dry_run = "--dry-run" in sys.argv
        usage_files = migrator.find_usage_files()
        print(f"Analyzing {len(usage_files)} files for service migration...")

        for file_path in usage_files:
            migrator.migrate_to_services(file_path, dry_run=dry_run)

    elif command == "dry-run":
        usage_files = migrator.find_usage_files()
        print("=== DRY RUN: Facade Migration ===")
        for file_path in usage_files:
            migrator.migrate_to_facade(file_path, dry_run=True)

        print("\n=== DRY RUN: Service Migration Analysis ===")
        for file_path in usage_files:
            migrator.migrate_to_services(file_path, dry_run=True)

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
