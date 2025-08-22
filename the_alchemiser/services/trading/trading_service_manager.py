import datetime
import logging
from typing import Any

from the_alchemiser.application.mapping.account_mapping import (
    account_summary_to_typed,
    account_typed_to_serializable,
    to_money_usd,
)
from the_alchemiser.application.mapping.order_mapping import (
    alpaca_order_to_domain,
    summarize_order,
)
from the_alchemiser.application.mapping.position_mapping import alpaca_position_to_summary
from the_alchemiser.services.account.account_service import AccountService
from the_alchemiser.services.errors.decorators import translate_trading_errors
from the_alchemiser.services.market_data.market_data_service import MarketDataService
from the_alchemiser.services.repository.alpaca_manager import AlpacaManager
from the_alchemiser.services.trading.order_service import OrderService
from the_alchemiser.services.trading.position_service import PositionService
from the_alchemiser.utils.num import floats_equal


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
        self, symbol: str, quantity: float, side: str, validate: bool = True
    ) -> dict[str, Any]:
        """Place a market order with validation"""
        try:
            # Always use typed path (V2 migration complete)
            try:
                from alpaca.trading.enums import OrderSide, TimeInForce
                from alpaca.trading.requests import MarketOrderRequest
            except Exception as e:
                # If imports fail, this is a configuration error, not a fallback case
                raise ImportError(f"Required Alpaca trading modules not available: {e}") from e

            req = MarketOrderRequest(
                symbol=symbol.upper(),
                qty=quantity,
                notional=None,
                side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )
            placed = self.alpaca_manager.place_order(req)
            dom = alpaca_order_to_domain(placed)
            return {
                "success": True,
                "order_id": str(getattr(placed, "id", getattr(placed, "order_id", ""))),
                "order": {
                    "raw": placed,
                    "domain": dom,
                    "summary": summarize_order(dom),
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def place_limit_order(
        self, symbol: str, quantity: float, side: str, limit_price: float, validate: bool = True
    ) -> dict[str, Any]:
        """Place a limit order with validation"""
        try:
            # Always use typed path (V2 migration complete)
            try:
                from alpaca.trading.enums import OrderSide, TimeInForce
                from alpaca.trading.requests import LimitOrderRequest
            except Exception as e:
                # If imports fail, this is a configuration error, not a fallback case
                raise ImportError(f"Required Alpaca trading modules not available: {e}") from e

            req = LimitOrderRequest(
                symbol=symbol.upper(),
                qty=quantity,
                side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price,
            )
            placed = self.alpaca_manager.place_order(req)
            dom = alpaca_order_to_domain(placed)
            return {
                "success": True,
                "order_id": str(getattr(placed, "id", getattr(placed, "order_id", ""))),
                "order": {
                    "raw": placed,
                    "domain": dom,
                    "summary": summarize_order(dom),
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def place_stop_loss_order(
        self, symbol: str, quantity: float, stop_price: float, validate: bool = True
    ) -> dict[str, Any]:
        """Place a stop-loss order using liquidation (not directly supported)"""
        return {
            "success": False,
            "error": "Stop-loss orders not directly supported. Use liquidate_position for position closure.",
        }

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        """Cancel an order with enhanced feedback"""
        try:
            success = self.orders.cancel_order(order_id)
            return {"success": success, "order_id": order_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_order_status(self, order_id: str) -> dict[str, Any]:
        """Get order status (not directly available - use AlpacaManager directly)"""
        return {
            "success": False,
            "error": "Order status queries not available in enhanced services. Use AlpacaManager directly.",
        }

    @translate_trading_errors(default_return=[])
    def get_open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """Get open orders.

        Legacy path returns raw-ish dicts derived from Alpaca objects.
        When the type system flag is enabled, returns a richer dict with
        a 'domain' key containing the mapped domain Order and a 'summary'.
        """
        orders = self.alpaca_manager.get_orders(status="open")
        # Optional symbol filter for safety (Alpaca filter applied earlier best-effort)
        if symbol:
            orders = [
                o
                for o in orders
                if getattr(o, "symbol", None) == symbol
                or (isinstance(o, dict) and o.get("symbol") == symbol)
            ]

        # Always use enriched typed path (V2 migration complete)
        enriched: list[dict[str, Any]] = []
        for o in orders:
            dom = alpaca_order_to_domain(o)
            enriched.append(
                {
                    "raw": o,
                    "domain": dom,
                    "summary": summarize_order(dom),
                }
            )
        return enriched

    # Position Management Operations
    def get_position_summary(self, symbol: str | None = None) -> dict[str, Any]:
        """Get comprehensive position summary"""
        try:
            if symbol:
                # Get specific position info
                positions = self.positions.get_positions_with_analysis()
                position = positions.get(symbol)
                if position:
                    return {
                        "success": True,
                        "symbol": symbol,
                        "position": {
                            "quantity": position.quantity,
                            "market_value": position.market_value,
                            "unrealized_pnl": position.unrealized_pnl,
                            "weight_percent": position.weight_percent,
                        },
                    }
                else:
                    return {"success": False, "error": f"No position found for {symbol}"}
            else:
                # Get portfolio summary
                portfolio = self.positions.get_portfolio_summary()
                return {
                    "success": True,
                    "portfolio": {
                        "total_market_value": portfolio.total_market_value,
                        "cash_balance": portfolio.cash_balance,
                        "total_positions": portfolio.total_positions,
                        "largest_position_percent": portfolio.largest_position_percent,
                    },
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close_position(self, symbol: str, percentage: float = 100.0) -> dict[str, Any]:
        """Close a position using liquidation"""
        try:
            # Sonar: replace float equality check with tolerance
            if not floats_equal(percentage, 100.0):
                return {
                    "success": False,
                    "error": "Partial position closure not directly supported. Use liquidate_position for full closure.",
                }
            order_id = self.orders.liquidate_position(symbol)
            return {"success": True, "order_id": order_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_position_analytics(self, symbol: str) -> dict[str, Any]:
        """Get detailed position analytics"""
        try:
            risk_metrics = self.positions.get_position_risk_metrics(symbol)
            return {"success": True, "risk_metrics": risk_metrics}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def calculate_position_metrics(self) -> dict[str, Any]:
        """Calculate portfolio-wide position metrics"""
        try:
            diversification_score = self.positions.calculate_diversification_score()
            largest_positions = self.positions.get_largest_positions()
            return {
                "success": True,
                "diversification_score": diversification_score,
                "largest_positions": [
                    {"symbol": pos.symbol, "weight": pos.weight_percent, "value": pos.market_value}
                    for pos in largest_positions
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Market Data Operations
    def get_latest_price(self, symbol: str, validate: bool = True) -> dict[str, Any]:
        """Get latest price with validation and caching"""
        try:
            price = self.market_data.get_validated_price(symbol)
            if price is not None:
                return {"success": True, "symbol": symbol, "price": price}
            else:
                return {"success": False, "error": f"Could not get price for {symbol}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_price_history(
        self, symbol: str, timeframe: str = "1Day", limit: int = 100, validate: bool = True
    ) -> dict[str, Any]:
        """Get price history (not directly available - use AlpacaManager directly)"""
        return {
            "success": False,
            "error": "Price history queries not available in enhanced services. Use AlpacaManager directly.",
        }

    def analyze_spread(self, symbol: str) -> dict[str, Any]:
        """Analyze bid-ask spread for a symbol"""
        try:
            spread_data = self.market_data.get_spread_analysis(symbol)
            if spread_data:
                return {"success": True, "spread_analysis": spread_data}
            else:
                return {"success": False, "error": f"Could not analyze spread for {symbol}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_market_status(self) -> dict[str, Any]:
        """Get current market status"""
        try:
            is_open = self.market_data.is_market_hours()
            return {"success": True, "market_open": is_open}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_multi_symbol_quotes(self, symbols: list[str]) -> dict[str, Any]:
        """Get quotes for multiple symbols efficiently"""
        try:
            prices = self.market_data.get_batch_prices(symbols)
            return {"success": True, "quotes": prices}
        except Exception as e:
            return {"success": False, "error": str(e)}

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
        self, symbol: str, quantity: int, side: str, estimated_cost: float | None = None
    ) -> dict[str, Any]:
        """Validate if a trade can be executed"""
        return self.account.validate_trade_eligibility(
            symbol, quantity, side, estimated_cost or 0.0
        )

    def get_portfolio_allocation(self) -> dict[str, Any]:
        """Get portfolio allocation and diversification metrics"""
        return self.account.get_portfolio_allocation()

    @translate_trading_errors(default_return={"error": "Failed to get account summary"})
    def get_account_summary_enriched(self) -> dict[str, Any]:
        """Enriched account summary with typed domain objects.

        Returns structured data with both legacy format and typed domain objects.
        """
        legacy = self.account.get_account_summary()

        # Always return typed path (V2 migration complete)
        typed = account_summary_to_typed(legacy)
        return {"raw": legacy, "summary": account_typed_to_serializable(typed)}

    def get_all_positions(self) -> list[Any]:
        """Get all positions from the underlying repository"""
        return self.alpaca_manager.get_all_positions()

    @translate_trading_errors(default_return=[])
    def get_positions_enriched(self) -> list[dict[str, Any]]:
        """Enriched positions list with typed domain objects.

        Returns list of {"raw": pos, "summary": PositionSummary-as-dict}
        """
        raw_positions = self.alpaca_manager.get_all_positions()

        # Always return enriched typed path (V2 migration complete)
        enriched: list[dict[str, Any]] = []
        for p in raw_positions:
            s = alpaca_position_to_summary(p)
            enriched.append(
                {
                    "raw": p,
                    "summary": {
                        "symbol": s.symbol,
                        "qty": float(s.qty),
                        "avg_entry_price": float(s.avg_entry_price),
                        "current_price": float(s.current_price),
                        "market_value": float(s.market_value),
                        "unrealized_pl": float(s.unrealized_pl),
                        "unrealized_plpc": float(s.unrealized_plpc),
                    },
                }
            )
        return enriched

    def get_portfolio_value(self) -> Any:
        """Get total portfolio value with typed domain objects."""
        raw = self.alpaca_manager.get_portfolio_value()
        # Always return typed path (V2 migration complete)
        money = to_money_usd(raw)
        return {"value": raw, "money": money}

    # High-Level Trading Operations
    @translate_trading_errors(
        default_return={
            "success": False,
            "reason": "Order execution failed",
            "error": "Service error",
        }
    )
    def execute_smart_order(
        self, symbol: str, quantity: int, side: str, order_type: str = "market", **kwargs: Any
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
        # Pre-trade validation
        estimated_cost = None
        if side.lower() == "buy" and order_type == "market":
            price_data = self.get_latest_price(symbol)
            if price_data.get("success") and price_data.get("price"):
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

    @translate_trading_errors(
        default_return={
            "error": "Failed to generate dashboard",
            "timestamp": datetime.datetime.now().isoformat(),
        }
    )
    def get_trading_dashboard(self) -> dict[str, Any]:
        """
        Get a comprehensive trading dashboard with all key metrics

        Returns:
            Complete trading dashboard data
        """
        return {
            "account": self.get_account_summary(),
            "risk_metrics": self.get_risk_metrics(),
            "portfolio_allocation": self.get_portfolio_allocation(),
            "position_summary": self.get_position_summary(),
            "open_orders": self.get_open_orders(),
            "market_status": self.get_market_status(),
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }

    def close(self) -> None:
        """Clean up resources"""
        try:
            if hasattr(self.alpaca_manager, "close"):
                self.alpaca_manager.close()
            self.logger.info("TradingServiceManager closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing TradingServiceManager: {e}")
