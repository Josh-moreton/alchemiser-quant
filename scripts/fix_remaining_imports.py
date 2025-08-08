#!/usr/bin/env python3
"""
Fix Remaining Import Issues

This script fixes import paths that weren't caught by the main rearchitecting script.
"""

import re
from pathlib import Path


def fix_imports_in_file(file_path: Path) -> bool:
    """Fix imports in a single file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Define comprehensive import mappings
        import_mappings = {
            # Core utils imports
            r"from the_alchemiser\.core\.utils\.common import": "from the_alchemiser.utils.common import",
            r"from the_alchemiser\.core\.utils\.s3_utils import": "from the_alchemiser.infrastructure.s3.s3_utils import",
            # Utils that moved to different layers
            r"from the_alchemiser\.utils\.config_utils import": "from the_alchemiser.infrastructure.config.config_utils import",
            r"from the_alchemiser\.utils\.indicator_utils import": "from the_alchemiser.domain.math.indicator_utils import",
            r"from the_alchemiser\.utils\.trading_math import": "from the_alchemiser.domain.math.trading_math import",
            r"from the_alchemiser\.utils\.math_utils import": "from the_alchemiser.domain.math.math_utils import",
            r"from the_alchemiser\.utils\.market_timing_utils import": "from the_alchemiser.domain.math.market_timing_utils import",
            r"from the_alchemiser\.utils\.asset_info import": "from the_alchemiser.domain.math.asset_info import",
            # Utils that moved to services
            r"from the_alchemiser\.utils\.account_utils import": "from the_alchemiser.services.account_utils import",
            r"from the_alchemiser\.utils\.price_utils import": "from the_alchemiser.services.price_utils import",
            r"from the_alchemiser\.utils\.price_fetching_utils import": "from the_alchemiser.services.price_fetching_utils import",
            r"from the_alchemiser\.utils\.position_manager import": "from the_alchemiser.services.position_manager import",
            # Utils that moved to application
            r"from the_alchemiser\.utils\.order_validation_utils import": "from the_alchemiser.application.order_validation_utils import",
            r"from the_alchemiser\.utils\.smart_pricing_handler import": "from the_alchemiser.application.smart_pricing_handler import",
            r"from the_alchemiser\.utils\.asset_order_handler import": "from the_alchemiser.application.asset_order_handler import",
            r"from the_alchemiser\.utils\.limit_order_handler import": "from the_alchemiser.application.limit_order_handler import",
            r"from the_alchemiser\.utils\.progressive_order_utils import": "from the_alchemiser.application.progressive_order_utils import",
            r"from the_alchemiser\.utils\.portfolio_pnl_utils import": "from the_alchemiser.application.portfolio_pnl_utils import",
            r"from the_alchemiser\.utils\.spread_assessment import": "from the_alchemiser.application.spread_assessment import",
            # Utils that moved to interface
            r"from the_alchemiser\.utils\.signal_display_utils import": "from the_alchemiser.interface.cli.signal_display_utils import",
            r"from the_alchemiser\.utils\.dashboard_utils import": "from the_alchemiser.interface.cli.dashboard_utils import",
            # Infrastructure websocket utils
            r"from the_alchemiser\.utils\.websocket_connection_manager import": "from the_alchemiser.infrastructure.websocket.websocket_connection_manager import",
            r"from the_alchemiser\.utils\.websocket_order_monitor import": "from the_alchemiser.infrastructure.websocket.websocket_order_monitor import",
            # Core modules that moved
            r"from the_alchemiser\.core\.exceptions import": "from the_alchemiser.services.exceptions import",
            r"from the_alchemiser\.core\.error_handler import": "from the_alchemiser.services.error_handler import",
            r"from the_alchemiser\.core\.error_recovery import": "from the_alchemiser.services.error_recovery import",
            r"from the_alchemiser\.core\.error_reporter import": "from the_alchemiser.services.error_reporter import",
            r"from the_alchemiser\.core\.error_monitoring import": "from the_alchemiser.services.error_monitoring import",
            r"from the_alchemiser\.core\.retry_decorator import": "from the_alchemiser.services.retry_decorator import",
            r"from the_alchemiser\.core\.types import": "from the_alchemiser.domain.types import",
            # Config imports
            r"from the_alchemiser\.core\.config import": "from the_alchemiser.infrastructure.config.config import",
            r"from the_alchemiser\.config\.execution_config import": "from the_alchemiser.infrastructure.config.execution_config import",
            # Data provider imports
            r"from the_alchemiser\.core\.data\.": "from the_alchemiser.infrastructure.data_providers.",
            # Logging imports
            r"from the_alchemiser\.core\.logging\.": "from the_alchemiser.infrastructure.logging.",
            # Secrets imports
            r"from the_alchemiser\.core\.secrets\.": "from the_alchemiser.infrastructure.secrets.",
            # Alerts imports
            r"from the_alchemiser\.core\.alerts\.": "from the_alchemiser.infrastructure.alerts.",
            # Validation imports
            r"from the_alchemiser\.core\.validation\.": "from the_alchemiser.infrastructure.validation.",
            # Model imports
            r"from the_alchemiser\.core\.models\.": "from the_alchemiser.domain.models.",
            # Registry imports
            r"from the_alchemiser\.core\.registry\.": "from the_alchemiser.domain.registry.",
            # Trading/strategy imports
            r"from the_alchemiser\.core\.trading\.": "from the_alchemiser.domain.strategies.",
            # Indicators imports
            r"from the_alchemiser\.core\.indicators\.": "from the_alchemiser.domain.math.",
            # Service imports
            r"from the_alchemiser\.core\.services\.": "from the_alchemiser.services.",
            # Execution imports
            r"from the_alchemiser\.execution\.": "from the_alchemiser.application.",
            # Tracking imports
            r"from the_alchemiser\.tracking\.": "from the_alchemiser.application.tracking.",
            # UI imports
            r"from the_alchemiser\.core\.ui\.": "from the_alchemiser.interface.",
            r"from the_alchemiser\.cli import": "from the_alchemiser.interface.cli.cli import",
        }

        # Apply all mappings
        for pattern, replacement in import_mappings.items():
            content = re.sub(pattern, replacement, content)

        # Write back if changed
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed imports in {file_path}")
            return True
        return False

    except Exception as e:
        print(f"Error fixing imports in {file_path}: {e}")
        return False


def main():
    """Fix imports in all Python files."""
    root_dir = Path("/Users/joshua.moreton/Documents/GitHub/the-alchemiser")
    alchemiser_dir = root_dir / "the_alchemiser"

    files_fixed = 0

    # Fix imports in all Python files
    for py_file in alchemiser_dir.rglob("*.py"):
        if "__pycache__" not in str(py_file):
            if fix_imports_in_file(py_file):
                files_fixed += 1

    # Also fix scripts and tests
    for py_file in root_dir.rglob("*.py"):
        if (
            "the_alchemiser" not in str(py_file)
            and py_file.name.endswith(".py")
            and "__pycache__" not in str(py_file)
        ):
            if fix_imports_in_file(py_file):
                files_fixed += 1

    print(f"Fixed imports in {files_fixed} files")


if __name__ == "__main__":
    main()
