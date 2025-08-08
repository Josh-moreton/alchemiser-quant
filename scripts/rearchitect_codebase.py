#!/usr/bin/env python3
"""
Comprehensive Rearchitecting Script

This script reorganizes the entire codebase according to the clean architecture plan:
- domain/: Pure trading domain logic
- services/: Application services
- infrastructure/: External integrations
- application/: Orchestration and use-cases
- interface/: Presentation layer
- utils/: Truly generic helpers

It handles duplicate files, logs all moves, and updates imports.
"""

import json
import os
import re
import shutil
from pathlib import Path


class CodebaseRearchitect:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.alchemiser_dir = self.root_dir / "the_alchemiser"
        self.move_log: list[dict[str, str]] = []
        self.import_updates: list[dict[str, str]] = []

        # Define the new architecture mapping (consolidated to avoid duplicate keys)
        self.architecture_mapping = {
            # Domain layer - Pure trading domain logic
            "domain/models/": [
                "the_alchemiser/core/models/account.py",
                "the_alchemiser/core/models/order.py",
                "the_alchemiser/core/models/position.py",
                "the_alchemiser/core/models/strategy.py",
                "the_alchemiser/core/models/market_data.py",
                "the_alchemiser/core/models/__init__.py",
            ],
            "domain/strategies/": [
                "the_alchemiser/core/trading/nuclear_signals.py",
                "the_alchemiser/core/trading/tecl_signals.py",
                "the_alchemiser/core/trading/tecl_strategy_engine.py",
                "the_alchemiser/core/trading/strategy_engine.py",
                "the_alchemiser/core/trading/strategy_manager.py",
                "the_alchemiser/core/trading/klm_ensemble_engine.py",
                "the_alchemiser/core/trading/klm_trading_bot.py",
                "the_alchemiser/core/trading/__init__.py",
            ],
            "domain/strategies/klm_workers/": [
                "the_alchemiser/core/trading/klm_workers/variant_506_38.py",
                "the_alchemiser/core/trading/klm_workers/variant_520_22.py",
                "the_alchemiser/core/trading/klm_workers/variant_410_38.py",
                "the_alchemiser/core/trading/klm_workers/variant_1200_28.py",
                "the_alchemiser/core/trading/klm_workers/variant_530_18.py",
                "the_alchemiser/core/trading/klm_workers/variant_1280_26.py",
                "the_alchemiser/core/trading/klm_workers/base_klm_variant.py",
                "the_alchemiser/core/trading/klm_workers/variant_nova.py",
                "the_alchemiser/core/trading/klm_workers/variant_830_21.py",
                "the_alchemiser/core/trading/klm_workers/__init__.py",
            ],
            "domain/registry/": [
                "the_alchemiser/core/registry/strategy_registry.py",
                "the_alchemiser/core/registry/__init__.py",
            ],
            "domain/math/": [
                "the_alchemiser/utils/trading_math.py",
                "the_alchemiser/utils/math_utils.py",
                "the_alchemiser/core/indicators/indicators.py",
                "the_alchemiser/core/indicators/__init__.py",
                "the_alchemiser/utils/indicator_utils.py",
                "the_alchemiser/utils/market_timing_utils.py",
                "the_alchemiser/utils/asset_info.py",
            ],
            "domain/": [
                "the_alchemiser/core/types.py",
            ],
            # Services layer - Application services
            "services/": [
                "the_alchemiser/core/services/config_service.py",
                "the_alchemiser/core/services/secrets_service.py",
                "the_alchemiser/core/services/market_data_client.py",
                "the_alchemiser/core/services/trading_client_service.py",
                "the_alchemiser/core/services/streaming_service.py",
                "the_alchemiser/core/services/cache_manager.py",
                "the_alchemiser/core/services/price_service.py",
                "the_alchemiser/core/services/error_handling.py",
                "the_alchemiser/core/services/__init__.py",
                # Domain-specific utils that should move to services
                "the_alchemiser/utils/position_manager.py",
                "the_alchemiser/utils/account_utils.py",
                "the_alchemiser/utils/price_fetching_utils.py",
                "the_alchemiser/utils/price_utils.py",
                # Error handling and core utilities
                "the_alchemiser/core/error_handler.py",
                "the_alchemiser/core/error_recovery.py",
                "the_alchemiser/core/error_reporter.py",
                "the_alchemiser/core/error_monitoring.py",
                "the_alchemiser/core/exceptions.py",
                "the_alchemiser/core/retry_decorator.py",
            ],
            # Infrastructure layer - External integrations
            "infrastructure/config/": [
                "the_alchemiser/core/config.py",
                "the_alchemiser/config/execution_config.py",
                "the_alchemiser/config/__init__.py",
                "the_alchemiser/utils/config_utils.py",
            ],
            "infrastructure/data_providers/": [
                "the_alchemiser/core/data/unified_data_provider_facade.py",
                "the_alchemiser/core/data/data_provider.py",
                "the_alchemiser/core/data/real_time_pricing.py",
                "the_alchemiser/core/data/__init__.py",
            ],
            "infrastructure/logging/": [
                "the_alchemiser/core/logging/logging_utils.py",
                "the_alchemiser/core/logging/__init__.py",
            ],
            "infrastructure/secrets/": [
                "the_alchemiser/core/secrets/secrets_manager.py",
                "the_alchemiser/core/secrets/__init__.py",
            ],
            "infrastructure/websocket/": [
                "the_alchemiser/utils/websocket_connection_manager.py",
                "the_alchemiser/utils/websocket_order_monitor.py",
            ],
            "infrastructure/s3/": [
                "the_alchemiser/core/utils/s3_utils.py",
            ],
            "infrastructure/alerts/": [
                "the_alchemiser/core/alerts/alert_service.py",
                "the_alchemiser/core/alerts/__init__.py",
            ],
            "infrastructure/validation/": [
                "the_alchemiser/core/validation/indicator_validator.py",
                "the_alchemiser/core/validation/__init__.py",
            ],
            # Application layer - Orchestration and use-cases
            "application/": [
                "the_alchemiser/execution/trading_engine.py",
                "the_alchemiser/execution/execution_manager.py",
                "the_alchemiser/execution/smart_execution.py",
                "the_alchemiser/execution/reporting.py",
                "the_alchemiser/execution/order_validation.py",
                "the_alchemiser/execution/types.py",
                "the_alchemiser/execution/__init__.py",
                "the_alchemiser/execution/alpaca_client.py",
                # Utils that belong in application layer
                "the_alchemiser/utils/order_validation_utils.py",
                "the_alchemiser/utils/smart_pricing_handler.py",
                "the_alchemiser/utils/asset_order_handler.py",
                "the_alchemiser/utils/limit_order_handler.py",
                "the_alchemiser/utils/progressive_order_utils.py",
                "the_alchemiser/utils/portfolio_pnl_utils.py",
                "the_alchemiser/utils/spread_assessment.py",
            ],
            "application/portfolio_rebalancer/": [
                "the_alchemiser/execution/portfolio_rebalancer.py",
            ],
            "application/tracking/": [
                "the_alchemiser/tracking/strategy_order_tracker.py",
                "the_alchemiser/tracking/integration.py",
                "the_alchemiser/tracking/__init__.py",
            ],
            # Interface layer - Presentation layer
            "interface/cli/": [
                "the_alchemiser/cli.py",
                "the_alchemiser/core/ui/cli_formatter.py",
                "the_alchemiser/utils/signal_display_utils.py",
                "the_alchemiser/utils/dashboard_utils.py",
            ],
            "interface/email/": [
                "the_alchemiser/core/ui/email_utils.py",
                "the_alchemiser/core/ui/email/client.py",
                "the_alchemiser/core/ui/email/config.py",
                "the_alchemiser/core/ui/email/__init__.py",
            ],
            "interface/email/templates/": [
                "the_alchemiser/core/ui/email/templates/trading_report.py",
                "the_alchemiser/core/ui/email/templates/base.py",
                "the_alchemiser/core/ui/email/templates/portfolio.py",
                "the_alchemiser/core/ui/email/templates/error_report.py",
                "the_alchemiser/core/ui/email/templates/performance.py",
                "the_alchemiser/core/ui/email/templates/multi_strategy.py",
                "the_alchemiser/core/ui/email/templates/signals.py",
                "the_alchemiser/core/ui/email/templates/__init__.py",
            ],
            # Utils layer - Truly generic helpers
            "utils/": [
                "the_alchemiser/core/utils/common.py",
                "the_alchemiser/utils/__init__.py",
            ],
            # Root level files
            "": [
                "the_alchemiser/main.py",
                "the_alchemiser/lambda_handler.py",
                "the_alchemiser/__init__.py",
            ],
        }

        # Files to archive (not move)
        self.archive_files = [
            "the_alchemiser/core/data/unified_data_provider_v2.py",
        ]

    def create_directory_structure(self) -> None:
        """Create the new directory structure."""
        print("Creating new directory structure...")

        new_dirs = [
            "domain/models",
            "domain/strategies/klm_workers",
            "domain/registry",
            "domain/math",
            "services",
            "infrastructure/config",
            "infrastructure/data_providers",
            "infrastructure/logging",
            "infrastructure/secrets",
            "infrastructure/websocket",
            "infrastructure/s3",
            "infrastructure/alerts",
            "infrastructure/validation",
            "application/portfolio_rebalancer",
            "application/tracking",
            "interface/cli",
            "interface/email/templates",
            "utils",
        ]

        for dir_path in new_dirs:
            full_path = self.alchemiser_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)

            # Create __init__.py files
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                self.move_log.append(
                    {
                        "action": "create",
                        "type": "init_file",
                        "path": str(init_file.relative_to(self.root_dir)),
                    }
                )

    def handle_account_service_merge(self) -> None:
        """Merge the two account_service.py files."""
        print("Merging account_service.py files...")

        core_service_path = self.alchemiser_dir / "core/services/account_service.py"
        execution_service_path = self.alchemiser_dir / "execution/account_service.py"
        merged_service_path = self.alchemiser_dir / "services/account_service.py"

        # Read both files
        with open(core_service_path) as f:
            core_content = f.read()

        # Create merged content - prioritize the core service
        merged_content = (
            '''"""
Account Service

Unified service for account information, positions and portfolio history.
Merges functionality from core.services.account_service and execution.account_service.
"""

import logging
from typing import Any, Protocol

import requests

from the_alchemiser.domain.models.account import AccountModel, PortfolioHistoryModel
from the_alchemiser.domain.models.position import PositionModel
from the_alchemiser.services.trading_client_service import TradingClientService
from the_alchemiser.domain.types import AccountInfo, PositionInfo, PositionsDict
from the_alchemiser.services.account_utils import extract_comprehensive_account_data


class DataProvider(Protocol):
    """Protocol defining the data provider interface needed by AccountService."""

    def get_positions(self) -> Any:
        """Get all positions."""
        ...

    def get_current_price(self, symbol: str) -> float | int | None:
        """Get current price for a symbol."""
        ...


class AccountService:
    """Unified service for account and position management operations."""

    def __init__(
        self,
        trading_client_service: TradingClientService,
        api_key: str,
        secret_key: str,
        api_endpoint: str,
        data_provider: DataProvider = None,
    ) -> None:
        """
        Initialize account service.

        Args:
            trading_client_service: Trading client service
            api_key: API key for direct API calls
            secret_key: Secret key for direct API calls
            api_endpoint: API endpoint for direct calls
            data_provider: Optional data provider for legacy compatibility
        """
        self._trading_client_service = trading_client_service
        self._api_key = api_key
        self._secret_key = secret_key
        self._api_endpoint = api_endpoint
        self._data_provider = data_provider
        
        # Pre-import the utility function to avoid runtime imports
        if data_provider:
            self._extract_account_data = extract_comprehensive_account_data

'''
            + core_content.split("class AccountService:")[1].split('"""')[2]
        )

        # Write merged file
        with open(merged_service_path, "w") as f:
            f.write(merged_content)

        self.move_log.append(
            {
                "action": "merge",
                "type": "account_service",
                "source1": str(core_service_path.relative_to(self.root_dir)),
                "source2": str(execution_service_path.relative_to(self.root_dir)),
                "destination": str(merged_service_path.relative_to(self.root_dir)),
            }
        )

    def move_files(self) -> None:
        """Move files according to the architecture mapping."""
        print("Moving files to new structure...")

        for target_dir, file_paths in self.architecture_mapping.items():
            for file_path in file_paths:
                source_path = self.alchemiser_dir / file_path.replace("the_alchemiser/", "")

                # Skip account_service.py as we handle it specially
                if source_path.name == "account_service.py":
                    continue

                if source_path.exists():
                    if target_dir:
                        target_path = self.alchemiser_dir / target_dir / source_path.name
                    else:
                        target_path = self.alchemiser_dir / source_path.name

                    # Ensure target directory exists
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # Move file
                    shutil.move(str(source_path), str(target_path))

                    self.move_log.append(
                        {
                            "action": "move",
                            "type": "file",
                            "source": str(source_path.relative_to(self.root_dir)),
                            "destination": str(target_path.relative_to(self.root_dir)),
                        }
                    )
                else:
                    print(f"Warning: Source file not found: {source_path}")

    def archive_legacy_files(self) -> None:
        """Archive legacy files that shouldn't be moved."""
        print("Archiving legacy files...")

        archive_dir = self.alchemiser_dir / "archived"
        archive_dir.mkdir(exist_ok=True)

        for file_path in self.archive_files:
            source_path = self.alchemiser_dir / file_path.replace("the_alchemiser/", "")
            if source_path.exists():
                target_path = archive_dir / source_path.name
                shutil.move(str(source_path), str(target_path))

                self.move_log.append(
                    {
                        "action": "archive",
                        "type": "file",
                        "source": str(source_path.relative_to(self.root_dir)),
                        "destination": str(target_path.relative_to(self.root_dir)),
                    }
                )

    def clean_empty_directories(self) -> None:
        """Remove empty directories after moving files."""
        print("Cleaning up empty directories...")

        # List of directories that might be empty after moves
        cleanup_dirs = [
            "core/models",
            "core/trading/klm_workers",
            "core/trading",
            "core/registry",
            "core/services",
            "core/logging",
            "core/secrets",
            "core/alerts",
            "core/validation",
            "core/indicators",
            "core/utils",
            "core/data",
            "core/ui/email/templates",
            "core/ui/email",
            "core/ui",
            "core",
            "execution",
            "tracking",
            "utils",
            "config",
        ]

        for dir_path in cleanup_dirs:
            full_path = self.alchemiser_dir / dir_path
            if full_path.exists() and full_path.is_dir():
                try:
                    # Try to remove if empty
                    if not any(full_path.iterdir()):
                        full_path.rmdir()
                        self.move_log.append(
                            {
                                "action": "remove",
                                "type": "empty_directory",
                                "path": str(full_path.relative_to(self.root_dir)),
                            }
                        )
                except OSError:
                    pass  # Directory not empty, leave it

    def generate_import_mapping(self) -> dict[str, str]:
        """Generate mapping of old imports to new imports."""
        print("Generating import mappings...")

        mappings = {}

        # Core model imports
        mappings.update(
            {
                "from the_alchemiser.domain.models.account import": "from the_alchemiser.domain.models.account import",
                "from the_alchemiser.domain.models.order import": "from the_alchemiser.domain.models.order import",
                "from the_alchemiser.domain.models.position import": "from the_alchemiser.domain.models.position import",
                "from the_alchemiser.domain.models.strategy import": "from the_alchemiser.domain.models.strategy import",
                "from the_alchemiser.domain.models.market_data import": "from the_alchemiser.domain.models.market_data import",
                "from the_alchemiser.domain.models import": "from the_alchemiser.domain.models import",
            }
        )

        # Trading/strategy imports
        mappings.update(
            {
                "from the_alchemiser.domain.strategies.": "from the_alchemiser.domain.strategies.",
                "from the_alchemiser.domain.registry.": "from the_alchemiser.domain.registry.",
                "from the_alchemiser.domain.math.": "from the_alchemiser.domain.math.",
            }
        )

        # Service imports
        mappings.update(
            {
                "from the_alchemiser.services.account_service import": "from the_alchemiser.services.account_service import",
                "from the_alchemiser.services.account_service import": "from the_alchemiser.services.account_service import",
                "from the_alchemiser.services.": "from the_alchemiser.services.",
            }
        )

        # Infrastructure imports
        mappings.update(
            {
                "from the_alchemiser.infrastructure.config import": "from the_alchemiser.infrastructure.config import",
                "from the_alchemiser.infrastructure.config.": "from the_alchemiser.infrastructure.config.",
                "from the_alchemiser.infrastructure.data_providers.": "from the_alchemiser.infrastructure.data_providers.",
                "from the_alchemiser.infrastructure.logging.": "from the_alchemiser.infrastructure.logging.",
                "from the_alchemiser.infrastructure.secrets.": "from the_alchemiser.infrastructure.secrets.",
                "from the_alchemiser.infrastructure.alerts.": "from the_alchemiser.infrastructure.alerts.",
                "from the_alchemiser.infrastructure.validation.": "from the_alchemiser.infrastructure.validation.",
                "from the_alchemiser.infrastructure.s3.s3_utils import": "from the_alchemiser.infrastructure.s3.s3_utils import",
            }
        )

        # Application imports
        mappings.update(
            {
                "from the_alchemiser.application.": "from the_alchemiser.application.",
                "from the_alchemiser.application.tracking.": "from the_alchemiser.application.tracking.",
            }
        )

        # Interface imports
        mappings.update(
            {
                "from the_alchemiser.interface.cli.cli import": "from the_alchemiser.interface.cli.cli import",
                "from the_alchemiser.interface.": "from the_alchemiser.interface.",
            }
        )

        # Domain and utils imports
        mappings.update(
            {
                "from the_alchemiser.domain.types import": "from the_alchemiser.domain.types import",
                "from the_alchemiser.domain.math.trading_math import": "from the_alchemiser.domain.math.trading_math import",
                "from the_alchemiser.domain.math.math_utils import": "from the_alchemiser.domain.math.math_utils import",
                "from the_alchemiser.services.account_utils import": "from the_alchemiser.services.account_utils import",
            }
        )

        return mappings

    def update_imports_in_file(self, file_path: Path, import_mappings: dict[str, str]) -> None:
        """Update imports in a single file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Apply import mappings
            for old_import, new_import in import_mappings.items():
                content = re.sub(re.escape(old_import), new_import, content)

            # Write back if changed
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                self.import_updates.append(
                    {
                        "file": str(file_path.relative_to(self.root_dir)),
                        "updates": str(
                            len([k for k in import_mappings.keys() if k in original_content])
                        ),
                    }
                )

        except Exception as e:
            print(f"Error updating imports in {file_path}: {e}")

    def update_all_imports(self) -> None:
        """Update imports in all Python files."""
        print("Updating imports in all Python files...")

        import_mappings = self.generate_import_mapping()

        # Find all Python files
        for py_file in self.alchemiser_dir.rglob("*.py"):
            if py_file.name != "__pycache__":
                self.update_imports_in_file(py_file, import_mappings)

        # Also update scripts and tests
        for py_file in self.root_dir.rglob("*.py"):
            if "the_alchemiser" in str(py_file) and py_file.is_file():
                continue  # Already handled above
            if py_file.name.endswith(".py") and "__pycache__" not in str(py_file):
                self.update_imports_in_file(py_file, import_mappings)

    def save_logs(self) -> dict[str, int]:
        """Save move and import update logs."""
        print("Saving operation logs...")

        # Save move log
        move_log_path = self.root_dir / "rearchitecture_move_log.json"
        with open(move_log_path, "w") as f:
            json.dump(self.move_log, f, indent=2)

        # Save import update log
        import_log_path = self.root_dir / "rearchitecture_import_log.json"
        with open(import_log_path, "w") as f:
            json.dump(self.import_updates, f, indent=2)

        print(f"Move log saved to: {move_log_path}")
        print(f"Import log saved to: {import_log_path}")

        # Create summary
        summary = {
            "total_moves": len([log for log in self.move_log if log["action"] == "move"]),
            "files_created": len([log for log in self.move_log if log["action"] == "create"]),
            "files_archived": len([log for log in self.move_log if log["action"] == "archive"]),
            "directories_removed": len([log for log in self.move_log if log["action"] == "remove"]),
            "files_with_import_updates": len(self.import_updates),
            "total_import_updates": sum(int(log["updates"]) for log in self.import_updates),
        }

        summary_path = self.root_dir / "rearchitecture_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"Summary saved to: {summary_path}")
        return summary

    def run(self) -> None:
        """Execute the complete rearchitecting process."""
        print("Starting codebase rearchitecting...")
        print("=" * 50)

        # Step 1: Create new directory structure
        self.create_directory_structure()

        # Step 2: Handle account service merge
        self.handle_account_service_merge()

        # Step 3: Move files according to architecture
        self.move_files()

        # Step 4: Archive legacy files
        self.archive_legacy_files()

        # Step 5: Clean up empty directories
        self.clean_empty_directories()

        # Step 6: Update all imports
        self.update_all_imports()

        # Step 7: Save logs and summary
        summary = self.save_logs()

        print("=" * 50)
        print("Rearchitecting completed!")
        print(f"Files moved: {summary['total_moves']}")
        print(f"Files created: {summary['files_created']}")
        print(f"Files archived: {summary['files_archived']}")
        print(f"Files with import updates: {summary['files_with_import_updates']}")
        print(f"Total import updates: {summary['total_import_updates']}")
        print("=" * 50)


def main() -> None:
    """Main entry point."""
    import sys

    if len(sys.argv) != 2:
        print("Usage: python rearchitect_codebase.py <project_root_directory>")
        sys.exit(1)

    project_root = sys.argv[1]

    if not os.path.exists(project_root):
        print(f"Error: Directory {project_root} does not exist")
        sys.exit(1)

    rearchitect = CodebaseRearchitect(project_root)
    rearchitect.run()


if __name__ == "__main__":
    main()
