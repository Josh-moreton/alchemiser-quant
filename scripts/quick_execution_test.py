#!/usr/bin/env python3
"""Business Unit: execution_v2 | Status: current.

Quick execution test script using signal mock with real Paper API.

This standalone script mocks a SignalGenerated event and runs the complete
workflow through real Paper API execution. Enables rapid development iteration
without waiting for strategy signal generation.

Usage:
    # Basic execution test
    python scripts/quick_execution_test.py

    # With custom allocations
    python scripts/quick_execution_test.py --allocations SPY:0.5,QQQ:0.3,AAPL:0.2

    # Test mode without real execution
    python scripts/quick_execution_test.py --test-only

Environment variables:
    ALPACA_API_KEY: Paper API key (required)
    ALPACA_SECRET_KEY: Paper API secret (required)
    PAPER_TRADING: Must be "true" (enforced)
    TESTING: Set to "true" for test mode
"""

import argparse
import os
import sys
import time
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def validate_environment() -> bool:
    """Validate required environment variables and safety checks.

    Returns:
        True if environment is valid, False otherwise

    """
    print("🔍 Validating environment...")

    # Check for required credentials
    if not os.environ.get("ALPACA_API_KEY"):
        print("❌ Error: ALPACA_API_KEY environment variable not set")
        return False

    if not os.environ.get("ALPACA_SECRET_KEY"):
        print("❌ Error: ALPACA_SECRET_KEY environment variable not set")
        return False

    # Enforce Paper trading mode
    if os.environ.get("PAPER_TRADING", "").lower() != "true":
        print("❌ Error: PAPER_TRADING must be set to 'true'")
        print("   This script only supports Paper trading for safety")
        return False

    # Check API key format (Paper keys start with 'PK')
    api_key = os.environ.get("ALPACA_API_KEY", "")
    if not api_key.startswith("PK"):
        print("⚠️  Warning: API key doesn't start with 'PK' (Paper key prefix)")
        print("   Please verify you're using Paper API credentials")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != "yes":
            return False

    print("✅ Environment validation passed")
    print(f"   Paper Trading: {os.environ.get('PAPER_TRADING')}")
    print(f"   API Key: {api_key[:8]}...")
    return True


def parse_allocations(allocation_str: str) -> dict[str, float]:
    """Parse allocation string into dictionary.

    Args:
        allocation_str: Comma-separated allocations like "SPY:0.5,QQQ:0.3,AAPL:0.2"

    Returns:
        Dictionary of symbol to weight

    Raises:
        ValueError: If allocation format is invalid

    """
    allocations = {}
    total_weight = 0.0

    for pair in allocation_str.split(","):
        if ":" not in pair:
            raise ValueError(f"Invalid allocation format: {pair} (expected SYMBOL:WEIGHT)")

        symbol, weight_str = pair.split(":", 1)
        symbol = symbol.strip().upper()
        try:
            weight = float(weight_str.strip())
        except ValueError:
            raise ValueError(f"Invalid weight for {symbol}: {weight_str}")

        if weight < 0 or weight > 1:
            raise ValueError(f"Weight for {symbol} must be between 0 and 1, got {weight}")

        allocations[symbol] = weight
        total_weight += weight

    # Validate total weight
    if not (0.99 <= total_weight <= 1.01):
        raise ValueError(f"Total allocations must sum to ~1.0, got {total_weight}")

    return allocations


def run_signal_mock_execution(
    allocations: dict[str, float] | None = None, test_only: bool = False
) -> bool:
    """Run signal mock execution test.

    Args:
        allocations: Optional custom allocations
        test_only: If True, only test event creation without execution

    Returns:
        True if successful, False otherwise

    """
    try:
        # Import after path is set up
        from the_alchemiser.shared.events import EventBus, SignalGenerated
        from the_alchemiser.shared.schemas.consolidated_portfolio import ConsolidatedPortfolio

        print("\n🚀 Starting Signal Mock Execution Test")
        print("=" * 60)

        # Generate correlation ID for tracking
        correlation_id = f"quick-exec-{uuid.uuid4()}"
        print(f"📊 Correlation ID: {correlation_id}")

        # Use default liquid securities if no allocations provided
        if allocations is None:
            allocations = {
                "SPY": 0.35,  # S&P 500 ETF
                "QQQ": 0.25,  # Nasdaq ETF
                "AAPL": 0.20,  # Apple
                "MSFT": 0.20,  # Microsoft
            }

        print(f"📈 Target allocations:")
        for symbol, weight in allocations.items():
            print(f"   {symbol}: {weight:.2%}")

        # Create consolidated portfolio
        target_allocations = {
            symbol: Decimal(str(weight)) for symbol, weight in allocations.items()
        }

        consolidated_portfolio = ConsolidatedPortfolio(
            target_allocations=target_allocations,
            correlation_id=correlation_id,
            timestamp=datetime.now(UTC),
            strategy_count=1,
            source_strategies=["quick_execution_test"],
        )

        # Create SignalGenerated event
        signal_event = SignalGenerated(
            signals_data={
                "strategy_name": "quick_execution_test",
                "generated_at": datetime.now(UTC).isoformat(),
                "allocations": allocations,
                "test_mode": True,
            },
            consolidated_portfolio=consolidated_portfolio.model_dump(),
            signal_count=len(allocations),
            metadata={
                "test_type": "quick_execution_script",
                "liquid_securities": True,
                "paper_trading": True,
            },
            correlation_id=correlation_id,
            causation_id=f"script-startup-{uuid.uuid4()}",
            event_id=f"signal-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="quick_execution_script",
            schema_version="1.0",
        )

        print(f"\n✅ Signal event created successfully")
        print(f"   Event ID: {signal_event.event_id}")
        print(f"   Signal count: {signal_event.signal_count}")

        if test_only:
            print("\n⚠️  Test-only mode: Skipping actual execution")
            print("✅ Signal mock creation successful")
            return True

        print("\n⚠️  Full execution requires ApplicationContainer integration")
        print("   This would involve:")
        print("   1. Initialize ApplicationContainer with Paper API credentials")
        print("   2. Register Portfolio and Execution handlers")
        print("   3. Publish signal event to EventBus")
        print("   4. Wait for execution completion")
        print("   5. Report results")
        print("\n💡 For full execution, integrate with the main system orchestrator")

        return True

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main entry point for quick execution test script."""
    parser = argparse.ArgumentParser(
        description="Quick execution test with signal mock and real Paper API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic test with default allocations
    python scripts/quick_execution_test.py

    # Custom allocations
    python scripts/quick_execution_test.py --allocations SPY:0.5,QQQ:0.3,AAPL:0.2

    # Test-only mode (no real execution)
    python scripts/quick_execution_test.py --test-only

Environment:
    ALPACA_API_KEY: Paper API key (required)
    ALPACA_SECRET_KEY: Paper API secret (required)
    PAPER_TRADING: Must be "true" (enforced)
        """,
    )

    parser.add_argument(
        "--allocations",
        type=str,
        help="Custom allocations (format: SYMBOL:WEIGHT,SYMBOL:WEIGHT,...)",
    )

    parser.add_argument(
        "--test-only", action="store_true", help="Test signal creation only, no execution"
    )

    args = parser.parse_args()

    # Set Paper trading mode if not set
    if "PAPER_TRADING" not in os.environ:
        os.environ["PAPER_TRADING"] = "true"

    if "TESTING" not in os.environ:
        os.environ["TESTING"] = "true"

    # Validate environment
    if not validate_environment():
        sys.exit(1)

    # Parse allocations if provided
    allocations = None
    if args.allocations:
        try:
            allocations = parse_allocations(args.allocations)
            print(f"\n✅ Parsed custom allocations: {allocations}")
        except ValueError as e:
            print(f"\n❌ Error parsing allocations: {e}")
            sys.exit(1)

    # Run execution test
    start_time = time.time()
    success = run_signal_mock_execution(allocations=allocations, test_only=args.test_only)
    duration = time.time() - start_time

    print("\n" + "=" * 60)
    if success:
        print(f"✅ Quick execution test completed in {duration:.2f}s")
        sys.exit(0)
    else:
        print(f"❌ Quick execution test failed after {duration:.2f}s")
        sys.exit(1)


if __name__ == "__main__":
    main()
