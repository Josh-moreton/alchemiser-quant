import logging
from typing import Any

from the_alchemiser.services.alpaca_manager import AlpacaManager
from the_alchemiser.services.enhanced.account_service import AccountService
from the_alchemiser.services.enhanced.market_data_service import MarketDataService
from the_alchemiser.services.enhanced.order_service import OrderService
from the_alchemiser.services.enhanced.position_service import PositionService


class TradingServiceManager:
    """
    Centralized service manager providing high-level access to all trading services

    This class acts as a facade, providing a single entry point for all trading operations
    while maintaining clean separation of concerns through the service layer architecture.
    """

    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        """
        Initialize the trading service manager

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading environment
        """
        self.logger = logging.getLogger(__name__)

        # Initialize the core repository implementation
        self.alpaca_manager = AlpacaManager(api_key, secret_key, paper)

        # Initialize enhanced services
        self.orders = OrderService(self.alpaca_manager)
        self.positions = PositionService(self.alpaca_manager)
        self.market_data = MarketDataService(self.alpaca_manager)
        self.account = AccountService(self.alpaca_manager)

        self.logger.info(f"TradingServiceManager initialized with paper={paper}")

    # Order Management Operations
    def place_market_order(
        self, symbol: str, quantity: int, side: str, validate: bool = True
    ) -> dict[str, Any]:
        """Place a market order with validation"""
        return self.orders.place_market_order(symbol, quantity, side, validate)

    def place_limit_order(
        self, symbol: str, quantity: int, side: str, limit_price: float, validate: bool = True
    ) -> dict[str, Any]:
        """Place a limit order with validation"""
        return self.orders.place_limit_order(symbol, quantity, side, limit_price, validate)

    def place_stop_loss_order(
        self, symbol: str, quantity: int, stop_price: float, validate: bool = True
    ) -> dict[str, Any]:
        """Place a stop-loss order with validation"""
        return self.orders.place_stop_loss_order(symbol, quantity, stop_price, validate)

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        """Cancel an order with enhanced feedback"""
        return self.orders.cancel_order(order_id)

    def get_order_status(self, order_id: str) -> dict[str, Any]:
        """Get enhanced order status with analytics"""
        return self.orders.get_order_status(order_id)

    def get_open_orders(self, symbol: str = None) -> list[dict[str, Any]]:
        """Get all open orders with enhanced details"""
        return self.orders.get_open_orders(symbol)

    # Position Management Operations
    def get_position_summary(self, symbol: str = None) -> dict[str, Any]:
        """Get comprehensive position summary"""
        return self.positions.get_position_summary(symbol)

    def close_position(self, symbol: str, percentage: float = 100.0) -> dict[str, Any]:
        """Close a position (partial or full)"""
        return self.positions.close_position(symbol, percentage)

    def get_position_analytics(self, symbol: str) -> dict[str, Any]:
        """Get detailed position analytics"""
        return self.positions.get_position_analytics(symbol)

    def calculate_position_metrics(self) -> dict[str, Any]:
        """Calculate portfolio-wide position metrics"""
        return self.positions.calculate_position_metrics()

    # Market Data Operations
    def get_latest_price(self, symbol: str, validate: bool = True) -> dict[str, Any]:
        """Get latest price with validation and caching"""
        return self.market_data.get_latest_price(symbol, validate)

    def get_price_history(
        self, symbol: str, timeframe: str = "1Day", limit: int = 100, validate: bool = True
    ) -> dict[str, Any]:
        """Get price history with enhanced analytics"""
        return self.market_data.get_price_history(symbol, timeframe, limit, validate)

    def analyze_spread(self, symbol: str) -> dict[str, Any]:
        """Analyze bid-ask spread for a symbol"""
        return self.market_data.analyze_spread(symbol)

    def get_market_status(self) -> dict[str, Any]:
        """Get current market status"""
        return self.market_data.get_market_status()

    def get_multi_symbol_quotes(self, symbols: list[str]) -> dict[str, Any]:
        """Get quotes for multiple symbols efficiently"""
        return self.market_data.get_multi_symbol_quotes(symbols)

    # Account Management Operations
    def get_account_summary(self) -> dict[str, Any]:
        """Get comprehensive account summary with metrics"""
        return self.account.get_account_summary()

    def check_buying_power(self, required_amount: float) -> dict[str, Any]:
        """Check available buying power"""
        return self.account.check_buying_power(required_amount)

    def get_risk_metrics(self) -> dict[str, Any]:
        """Calculate comprehensive risk metrics"""
        return self.account.get_risk_metrics()

    def validate_trade_eligibility(
        self, symbol: str, quantity: int, side: str, estimated_cost: float = None
    ) -> dict[str, Any]:
        """Validate if a trade can be executed"""
        return self.account.validate_trade_eligibility(symbol, quantity, side, estimated_cost)

    def get_portfolio_allocation(self) -> dict[str, Any]:
        """Get portfolio allocation and diversification metrics"""
        return self.account.get_portfolio_allocation()

    # High-Level Trading Operations
    def execute_smart_order(
        self, symbol: str, quantity: int, side: str, order_type: str = "market", **kwargs
    ) -> dict[str, Any]:
        """
        Execute a smart order with comprehensive validation and risk management

        Args:
            symbol: Symbol to trade
            quantity: Number of shares
            side: 'buy' or 'sell'
            order_type: 'market', 'limit', or 'stop_loss'
            **kwargs: Additional order parameters (limit_price, stop_price, etc.)

        Returns:
            Comprehensive order execution result
        """
        try:
            # Pre-trade validation
            estimated_cost = None
            if side.lower() == "buy" and order_type == "market":
                price_data = self.get_latest_price(symbol)
                estimated_cost = price_data["price"] * quantity

            eligibility = self.validate_trade_eligibility(symbol, quantity, side, estimated_cost)
            if not eligibility["eligible"]:
                return {
                    "success": False,
                    "reason": eligibility["reason"],
                    "details": eligibility["details"],
                }

            # Execute the order based on type
            if order_type.lower() == "market":
                result = self.place_market_order(symbol, quantity, side, validate=False)
            elif order_type.lower() == "limit":
                limit_price = kwargs.get("limit_price")
                if not limit_price:
                    return {"success": False, "reason": "limit_price required for limit orders"}
                result = self.place_limit_order(symbol, quantity, side, limit_price, validate=False)
            elif order_type.lower() == "stop_loss":
                stop_price = kwargs.get("stop_price")
                if not stop_price:
                    return {"success": False, "reason": "stop_price required for stop_loss orders"}
                result = self.place_stop_loss_order(symbol, quantity, stop_price, validate=False)
            else:
                return {"success": False, "reason": f"Unsupported order type: {order_type}"}

            # Add post-execution analytics
            if result.get("success"):
                result["pre_trade_validation"] = eligibility
                result["account_impact"] = self.get_account_summary()

            return result

        except Exception as e:
            self.logger.error(f"Failed to execute smart order: {e}")
            return {"success": False, "reason": f"Execution failed: {str(e)}", "error": str(e)}

    def get_trading_dashboard(self) -> dict[str, Any]:
        """
        Get a comprehensive trading dashboard with all key metrics

        Returns:
            Complete trading dashboard data
        """
        try:
            return {
                "account": self.get_account_summary(),
                "risk_metrics": self.get_risk_metrics(),
                "portfolio_allocation": self.get_portfolio_allocation(),
                "position_summary": self.get_position_summary(),
                "open_orders": self.get_open_orders(),
                "market_status": self.get_market_status(),
                "timestamp": self.market_data._get_current_time().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Failed to generate trading dashboard: {e}")
            return {"error": str(e), "timestamp": self.market_data._get_current_time().isoformat()}

    def close(self):
        """Clean up resources"""
        try:
            if hasattr(self.alpaca_manager, "close"):
                self.alpaca_manager.close()
            self.logger.info("TradingServiceManager closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing TradingServiceManager: {e}")
