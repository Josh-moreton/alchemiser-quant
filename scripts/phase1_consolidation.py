#!/usr/bin/env python3
"""
Phase 1 Implementation Script - Consolidate Alpaca Usage

This script demonstrates how to start using the new AlpacaManager to consolidate
scattered Alpaca imports. It shows before/after patterns and provides a migration
path that doesn't break existing code.
"""

import os
from pathlib import Path


def find_files_with_alpaca_imports():
    """Find all Python files that import Alpaca modules."""
    alpaca_files = []

    # Search for files with Alpaca imports
    for file_path in Path(".").rglob("*.py"):
        if any(exclude in str(file_path) for exclude in ["__pycache__", ".git", "examples"]):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for various Alpaca import patterns
            alpaca_patterns = [
                "from alpaca.trading.client import",
                "from alpaca.data.historical import",
                "import alpaca.trading",
                "import alpaca.data",
                "TradingClient(",
                "StockHistoricalDataClient(",
            ]

            if any(pattern in content for pattern in alpaca_patterns):
                alpaca_files.append(file_path)

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return alpaca_files


def analyze_current_alpaca_usage():
    """Analyze current Alpaca usage patterns."""
    print("🔍 Analyzing current Alpaca usage...")

    alpaca_files = find_files_with_alpaca_imports()

    print(f"\n📊 Found {len(alpaca_files)} files with Alpaca imports:")
    for file_path in alpaca_files:
        print(f"  - {file_path}")

    return alpaca_files


def show_migration_examples():
    """Show before/after migration examples."""
    print("\n📝 Migration Examples:")
    print("=" * 50)

    print("\n🔴 BEFORE - Scattered Alpaca usage:")
    print(
        """
# services/account_service.py
from alpaca.trading.client import TradingClient

class AccountService:
    def __init__(self, api_key, secret_key):
        self.client = TradingClient(api_key, secret_key, paper=True)
    
    def get_account_info(self):
        try:
            return self.client.get_account()
        except Exception as e:
            # Basic error handling
            print(f"Error: {e}")
            return None

# services/position_manager.py  
from alpaca.trading.client import TradingClient

class PositionManager:
    def __init__(self, api_key, secret_key):
        self.client = TradingClient(api_key, secret_key, paper=True)
    
    def get_positions(self):
        return self.client.get_all_positions()

# application/alpaca_client.py
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient

class AlpacaClient:
    def __init__(self, api_key, secret_key):
        self.trading_client = TradingClient(api_key, secret_key, paper=True)
        self.data_client = StockHistoricalDataClient(api_key, secret_key)
"""
    )

    print("\n🟢 AFTER - Using AlpacaManager:")
    print(
        """
# services/account_service.py
from the_alchemiser.services.alpaca_manager import AlpacaManager

class AccountService:
    def __init__(self, alpaca_manager: AlpacaManager):
        self.alpaca = alpaca_manager
    
    def get_account_info(self):
        # Better error handling built into AlpacaManager
        return self.alpaca.get_account()

# Alternative backward-compatible approach:
class AccountService:
    def __init__(self, api_key, secret_key):
        self.alpaca = AlpacaManager(api_key, secret_key, paper=True)
    
    def get_account_info(self):
        return self.alpaca.get_account()

# services/position_manager.py
from the_alchemiser.services.alpaca_manager import AlpacaManager

class PositionManager:
    def __init__(self, alpaca_manager: AlpacaManager):
        self.alpaca = alpaca_manager
    
    def get_positions(self):
        return self.alpaca.get_positions()  # Built-in error handling

# application/main_trading_app.py
from the_alchemiser.services.alpaca_manager import create_alpaca_manager

# Single point of Alpaca configuration
alpaca = create_alpaca_manager(api_key, secret_key, paper=True)

# Share the same manager across services
account_service = AccountService(alpaca)
position_manager = PositionManager(alpaca)
"""
    )


def create_migration_checklist():
    """Create a checklist for Phase 1 migration."""
    print("\n✅ Phase 1 Migration Checklist:")
    print("=" * 40)

    checklist = [
        "1. ✅ Create AlpacaManager class",
        "2. ⏳ Identify files with scattered Alpaca imports",
        "3. ⏳ Replace direct TradingClient creation with AlpacaManager",
        "4. ⏳ Replace direct StockHistoricalDataClient with AlpacaManager",
        "5. ⏳ Update error handling to use AlpacaManager methods",
        "6. ⏳ Test that all existing functionality still works",
        "7. ⏳ Update tests to use AlpacaManager",
        "8. ⏳ Fix remaining mypy errors",
        "9. ⏳ Document the new patterns for the team",
        "10. ⏳ Create examples of new usage patterns",
    ]

    for item in checklist:
        print(f"  {item}")


def suggest_specific_migrations(alpaca_files):
    """Suggest specific migration steps for found files."""
    if not alpaca_files:
        print("\n🎉 No files with direct Alpaca imports found!")
        return

    print(f"\n🔄 Suggested Migration Steps for {len(alpaca_files)} files:")
    print("=" * 60)

    for i, file_path in enumerate(alpaca_files, 1):
        print(f"\n{i}. {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            suggestions = []

            if "TradingClient(" in content:
                suggestions.append("   → Replace TradingClient creation with AlpacaManager")

            if "StockHistoricalDataClient(" in content:
                suggestions.append("   → Replace StockHistoricalDataClient with AlpacaManager")

            if "from alpaca.trading.client import TradingClient" in content:
                suggestions.append(
                    "   → Replace import with: from the_alchemiser.services.alpaca_manager import AlpacaManager"
                )

            if "client.get_all_positions()" in content:
                suggestions.append("   → Replace with: alpaca_manager.get_positions()")

            if "client.submit_order(" in content:
                suggestions.append("   → Replace with: alpaca_manager.place_order()")

            if "client.get_account()" in content:
                suggestions.append("   → Replace with: alpaca_manager.get_account()")

            for suggestion in suggestions:
                print(suggestion)

        except Exception as e:
            print(f"   ❌ Error analyzing file: {e}")


def show_benefits():
    """Show the benefits of Phase 1 migration."""
    print("\n🎯 Benefits of Phase 1 Migration:")
    print("=" * 40)

    benefits = [
        "✅ Consolidated Alpaca usage - all in one place",
        "✅ Consistent error handling across all operations",
        "✅ Better logging and debugging capabilities",
        "✅ Easier testing - mock one class instead of many",
        "✅ Configuration in one place - easier to manage",
        "✅ Validation built-in - catch errors early",
        "✅ Backward compatibility - existing code keeps working",
        "✅ Sets foundation for future improvements",
    ]

    for benefit in benefits:
        print(f"  {benefit}")


def create_example_usage():
    """Create an example of how to use the new AlpacaManager."""
    example_code = '''
"""
Example usage of AlpacaManager - Phase 1 Incremental Improvement

This shows how to use the new AlpacaManager in a real application.
"""

import os
from the_alchemiser.services.alpaca_manager import create_alpaca_manager

def main():
    # Get credentials from environment
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("❌ Please set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables")
        return
    
    # Create the manager (paper trading by default for safety)
    alpaca = create_alpaca_manager(api_key, secret_key, paper=True)
    
    # Validate connection
    if not alpaca.validate_connection():
        print("❌ Failed to connect to Alpaca")
        return
    
    print("✅ Connected to Alpaca successfully")
    
    # Get account info
    try:
        account = alpaca.get_account()
        print(f"Account Status: {account.status}")
        print(f"Buying Power: ${alpaca.get_buying_power()}")
        print(f"Portfolio Value: ${alpaca.get_portfolio_value()}")
    except Exception as e:
        print(f"❌ Error getting account info: {e}")
    
    # Get positions
    try:
        positions = alpaca.get_positions()
        print(f"\\nCurrent Positions: {len(positions)}")
        for position in positions:
            print(f"  {position.symbol}: {position.qty} shares")
    except Exception as e:
        print(f"❌ Error getting positions: {e}")
    
    # Get current price (example)
    try:
        price = alpaca.get_current_price("AAPL")
        if price:
            print(f"\\nAAPL current price: ${price:.2f}")
        else:
            print("\\nCould not get AAPL price")
    except Exception as e:
        print(f"❌ Error getting price: {e}")
    
    # Place a small test order (only in paper trading!)
    if alpaca.is_paper_trading:
        try:
            print("\\n📝 Placing test order (paper trading only)...")
            order = alpaca.place_market_order("AAPL", "buy", 1)
            print(f"✅ Order placed: {order.id}")
            
            # Cancel the order immediately (just testing)
            if alpaca.cancel_order(order.id):
                print("✅ Order cancelled successfully")
                
        except Exception as e:
            print(f"❌ Error with test order: {e}")
    else:
        print("\\n⚠️  Skipping test order - not in paper trading mode")

if __name__ == "__main__":
    main()
'''

    with open("examples/alpaca_manager_example.py", "w") as f:
        f.write(example_code)

    print(f"\n📄 Created example usage file: examples/alpaca_manager_example.py")


def main():
    """Main function to run Phase 1 analysis and planning."""
    print("🚀 Phase 1: Alpaca Usage Consolidation")
    print("=" * 50)

    # Analyze current state
    alpaca_files = analyze_current_alpaca_usage()

    # Show migration examples
    show_migration_examples()

    # Create migration checklist
    create_migration_checklist()

    # Suggest specific migrations
    suggest_specific_migrations(alpaca_files)

    # Show benefits
    show_benefits()

    # Create example
    create_example_usage()

    print("\n🎯 Next Steps:")
    print("=" * 20)
    print("1. Review the AlpacaManager class in: the_alchemiser/services/alpaca_manager.py")
    print("2. Try the example: python examples/alpaca_manager_example.py")
    print("3. Start migrating one file at a time using the patterns shown")
    print("4. Test thoroughly after each migration")
    print("5. Once comfortable, proceed to Phase 2 (Interface Extraction)")

    print(f"\n✅ Phase 1 analysis complete!")
    print(f"Found {len(alpaca_files)} files that can benefit from AlpacaManager")


if __name__ == "__main__":
    main()
