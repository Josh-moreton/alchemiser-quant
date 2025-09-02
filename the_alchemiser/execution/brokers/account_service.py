"""Business Unit: execution | Status: current

Account management and broker account services for execution module.
"""

from __future__ import annotations

import logging
from typing import Any, Literal, cast

from the_alchemiser.shared.interfaces.repository_protocols import AccountRepository
from the_alchemiser.shared.math.num import floats_equal
from the_alchemiser.shared.value_objects.core_types import AccountInfo, PositionsDict


class AccountService:
    """Enhanced account service providing business logic and validation for account operations."""

    def __init__(self, account_repository: AccountRepository) -> None:
        """Initialize AccountService.

        Args:
            account_repository: Repository for account operations

        """
        self.account_repository = account_repository
        self.logger = logging.getLogger(__name__)

    def _get_attr(self, obj: Any, attr: str, default: Any = 0) -> Any:  # noqa: ANN401  # Handles both objects and dicts dynamically
        """Safely get attributes from objects or dicts.

        Args:
            obj: Object or dict to get attribute from
            attr: Attribute name
            default: Default value if attribute not found

        Returns:
            Attribute value or default

        """
        if hasattr(obj, attr):
            return getattr(obj, attr)
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return default

    def get_account_summary(self) -> dict[str, Any]:
        """Get comprehensive account summary with calculated metrics.

        Returns:
            Dictionary containing account details with enhanced metrics

        """
        try:
            account = self.account_repository.get_account()
            if not account:
                raise ValueError("Could not retrieve account information")

            # Calculate additional metrics
            equity = float(self._get_attr(account, "equity", 0))
            cash = float(self._get_attr(account, "cash", 0))
            long_market_value = float(self._get_attr(account, "long_market_value", 0))
            short_market_value = float(self._get_attr(account, "short_market_value", 0))
            market_value = long_market_value + abs(short_market_value)
            buying_power = float(self._get_attr(account, "buying_power", 0))

            # Calculate ratios and risk metrics
            cash_ratio = cash / equity if equity > 0 else 0
            market_exposure = market_value / equity if equity > 0 else 0
            leverage_ratio = equity / cash if cash > 0 else float("inf")

            return {
                "account_id": self._get_attr(account, "id", "unknown"),
                "equity": equity,
                "cash": cash,
                "market_value": market_value,
                "buying_power": buying_power,
                "day_trade_count": self._get_attr(account, "daytrade_count", 0),
                "pattern_day_trader": self._get_attr(account, "pattern_day_trader", False),
                "trading_blocked": self._get_attr(account, "trading_blocked", False),
                "transfers_blocked": self._get_attr(account, "transfers_blocked", False),
                "account_blocked": self._get_attr(account, "account_blocked", False),
                "last_equity": float(self._get_attr(account, "last_equity", equity)),
                "calculated_metrics": {
                    "cash_ratio": round(cash_ratio, 4),
                    "market_exposure": round(market_exposure, 4),
                    "leverage_ratio": (
                        round(leverage_ratio, 4) if leverage_ratio != float("inf") else None
                    ),
                    "available_buying_power_ratio": (
                        round(buying_power / equity, 4) if equity > 0 else 0
                    ),
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to get account summary: {e}")
            raise

    def check_buying_power(self, required_amount: float) -> dict[str, Any]:
        """Check if account has sufficient buying power for a trade.

        Args:
            required_amount: Amount needed for the trade

        Returns:
            Dictionary with buying power check results

        """
        try:
            account = self.account_repository.get_account()
            if not account:
                raise ValueError("Could not retrieve account information")

            buying_power = float(self._get_attr(account, "buying_power", 0))
            cash = float(self._get_attr(account, "cash", 0))
            trading_blocked = self._get_attr(account, "trading_blocked", False)
            pattern_day_trader = self._get_attr(account, "pattern_day_trader", False)

            sufficient_buying_power = buying_power >= required_amount
            sufficient_cash = cash >= required_amount

            return {
                "required_amount": required_amount,
                "available_buying_power": buying_power,
                "available_cash": cash,
                "sufficient_buying_power": sufficient_buying_power,
                "sufficient_cash": sufficient_cash,
                "excess_buying_power": buying_power - required_amount,
                "can_trade": sufficient_buying_power and not trading_blocked,
                "trading_blocked": trading_blocked,
                "pattern_day_trader": pattern_day_trader,
            }

        except Exception as e:
            self.logger.error(f"Failed to check buying power: {e}")
            raise

    def get_risk_metrics(self) -> dict[str, Any]:
        """Calculate comprehensive risk metrics for the account.

        Returns:
            Dictionary containing various risk metrics

        """
        try:
            account = self.account_repository.get_account()
            positions = self.account_repository.get_positions()

            if not account:
                raise ValueError("Could not retrieve account information")

            equity = float(self._get_attr(account, "equity", 0))
            cash = float(self._get_attr(account, "cash", 0))
            long_value = float(self._get_attr(account, "long_market_value", 0))
            short_value = abs(float(self._get_attr(account, "short_market_value", 0)))
            total_market_value = long_value + short_value

            # Position concentration risk
            position_values = {}
            total_position_value = 0.0

            for position in positions:
                # Handle both object and dict position formats
                qty = (
                    self._get_attr(position, "qty", 0)
                    if hasattr(position, "qty") or isinstance(position, dict)
                    else 0
                )
                if not floats_equal(qty, 0.0):
                    market_value = (
                        self._get_attr(position, "market_value", 0)
                        if hasattr(position, "market_value") or isinstance(position, dict)
                        else 0
                    )
                    symbol = (
                        self._get_attr(position, "symbol", "")
                        if hasattr(position, "symbol") or isinstance(position, dict)
                        else ""
                    )

                    if symbol:
                        position_value = abs(float(qty) * float(market_value))
                        position_values[symbol] = position_value
                        total_position_value += position_value

            # Calculate concentration metrics
            max_position_value = max(position_values.values()) if position_values else 0
            max_concentration = max_position_value / equity if equity > 0 else 0

            # Risk ratios
            cash_to_equity = cash / equity if equity > 0 else 0
            market_exposure = total_market_value / equity if equity > 0 else 0
            leverage = (long_value + short_value) / equity if equity > 0 else 0

            return {
                "equity": equity,
                "cash_ratio": round(cash_to_equity, 4),
                "market_exposure": round(market_exposure, 4),
                "leverage_ratio": round(leverage, 4),
                "max_position_concentration": round(max_concentration, 4),
                "number_of_positions": len(
                    [p for p in positions if self._get_attr(p, "qty", 0) != 0]
                ),
                "long_exposure": round(long_value / equity, 4) if equity > 0 else 0,
                "short_exposure": round(short_value / equity, 4) if equity > 0 else 0,
                "day_trade_count": self._get_attr(account, "daytrade_count", 0),
                "pattern_day_trader": self._get_attr(account, "pattern_day_trader", False),
                "trading_restrictions": {
                    "trading_blocked": self._get_attr(account, "trading_blocked", False),
                    "transfers_blocked": self._get_attr(account, "transfers_blocked", False),
                    "account_blocked": self._get_attr(account, "account_blocked", False),
                },
                "position_breakdown": position_values,
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate risk metrics: {e}")
            raise

    def validate_trade_eligibility(
        self, symbol: str, quantity: int, side: str, estimated_cost: float | None = None
    ) -> dict[str, Any]:
        """Validate if a trade can be executed based on account status and buying power.

        Args:
            symbol: Symbol to trade
            quantity: Number of shares
            side: 'buy' or 'sell'
            estimated_cost: Estimated cost of the trade

        Returns:
            Dictionary with trade eligibility results

        """
        try:
            account = self.account_repository.get_account()
            positions = self.account_repository.get_positions()

            if not account:
                raise ValueError("Could not retrieve account information")

            # Basic account checks
            if self._get_attr(account, "trading_blocked", False):
                return {
                    "eligible": False,
                    "reason": "Trading is blocked on this account",
                    "details": {"trading_blocked": True},
                }

            if self._get_attr(account, "account_blocked", False):
                return {
                    "eligible": False,
                    "reason": "Account is blocked",
                    "details": {"account_blocked": True},
                }

            # Check for existing position
            current_position = None
            for position in positions:
                position_symbol = self._get_attr(position, "symbol", "")
                if position_symbol == symbol:
                    current_position = position
                    break

            current_qty = (
                float(self._get_attr(current_position, "qty", 0)) if current_position else 0
            )

            # Validate sell orders
            if side.lower() == "sell":
                if current_qty <= 0:
                    return {
                        "eligible": False,
                        "reason": f"No long position to sell for {symbol}",
                        "details": {"current_position": current_qty},
                    }

                if abs(quantity) > current_qty:
                    return {
                        "eligible": False,
                        "reason": f"Cannot sell {quantity} shares, only {current_qty} available",
                        "details": {
                            "current_position": current_qty,
                            "requested_quantity": quantity,
                        },
                    }

            # Validate buy orders
            elif side.lower() == "buy" and estimated_cost:
                buying_power_check = self.check_buying_power(estimated_cost)
                if not buying_power_check["can_trade"]:
                    return {
                        "eligible": False,
                        "reason": "Insufficient buying power",
                        "details": buying_power_check,
                    }

            # Pattern day trader checks
            pattern_day_trader = self._get_attr(account, "pattern_day_trader", False)
            daytrade_count = self._get_attr(account, "daytrade_count", 0)
            if pattern_day_trader and daytrade_count >= 3:
                equity = float(self._get_attr(account, "equity", 0))
                if equity < 25000:
                    return {
                        "eligible": False,
                        "reason": "Pattern day trader with insufficient equity for day trading",
                        "details": {
                            "equity": equity,
                            "minimum_required": 25000,
                            "day_trade_count": daytrade_count,
                        },
                    }

            return {
                "eligible": True,
                "reason": "Trade is eligible",
                "details": {
                    "current_position": current_qty,
                    "account_equity": float(self._get_attr(account, "equity", 0)),
                    "buying_power": float(self._get_attr(account, "buying_power", 0)),
                    "day_trade_count": daytrade_count,
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to validate trade eligibility: {e}")
            raise

    def get_portfolio_allocation(self) -> dict[str, Any]:
        """Calculate portfolio allocation and diversification metrics.

        Returns:
            Dictionary containing allocation breakdown

        """
        try:
            account = self.account_repository.get_account()
            positions = self.account_repository.get_positions()

            if not account:
                raise ValueError("Could not retrieve account information")

            equity = float(self._get_attr(account, "equity", 0))
            cash = float(self._get_attr(account, "cash", 0))

            allocations = {}
            total_position_value = 0.0

            for position in positions:
                qty = self._get_attr(position, "qty", 0)
                if not floats_equal(qty, 0.0):
                    market_value = self._get_attr(position, "market_value", 0)
                    symbol = self._get_attr(position, "symbol", "")
                    if symbol:
                        position_value = abs(float(qty) * float(market_value))
                        allocation_pct = position_value / equity if equity > 0 else 0

                        allocations[symbol] = {
                            "quantity": float(qty),
                            "market_value": position_value,
                            "allocation_percentage": round(allocation_pct * 100, 2),
                            "unrealized_pl": float(self._get_attr(position, "unrealized_pl", 0)),
                            "unrealized_plpc": float(
                                self._get_attr(position, "unrealized_plpc", 0)
                            ),
                        }
                        total_position_value += position_value

            cash_allocation = cash / equity if equity > 0 else 0

            return {
                "total_equity": equity,
                "cash": cash,
                "cash_allocation_percentage": round(cash_allocation * 100, 2),
                "invested_percentage": (
                    round((total_position_value / equity) * 100, 2) if equity > 0 else 0
                ),
                "position_count": len(allocations),
                "positions": allocations,
                "diversification_metrics": {
                    "largest_position_pct": (
                        max([pos["allocation_percentage"] for pos in allocations.values()])
                        if allocations
                        else 0
                    ),
                    "top_5_concentration": sum(
                        sorted(
                            [pos["allocation_percentage"] for pos in allocations.values()],
                            reverse=True,
                        )[:5]
                    ),
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate portfolio allocation: {e}")
            raise

    # ---- Extended enrichment accessors (encapsulate repository capabilities) ----
    def get_portfolio_history(self) -> dict[str, Any] | None:
        """Return portfolio history if repository supports it.

        This prevents consumers (e.g., AccountFacade) from reaching directly into the
        underlying repository attribute, maintaining the AccountService abstraction.
        """
        try:
            repo = self.account_repository
            if hasattr(repo, "get_portfolio_history"):
                history = cast(Any, repo).get_portfolio_history()
                if history:
                    return cast(dict[str, Any], history)
            return None
        except Exception as e:  # pragma: no cover - defensive
            self.logger.debug(f"Portfolio history retrieval failed: {e}")
            return None

    def get_recent_closed_positions(self) -> list[dict[str, Any]] | None:
        """Return recent closed position P&L data if repository supports it.

        Encapsulates optional repository capability and prevents callers from
        accessing the repository attribute directly.
        """
        try:
            repo = self.account_repository
            if hasattr(repo, "get_recent_closed_positions"):
                closed = cast(Any, repo).get_recent_closed_positions()
                if closed:
                    return cast(list[dict[str, Any]], closed)
            return None
        except Exception as e:  # pragma: no cover - defensive
            self.logger.debug(f"Recent closed positions retrieval failed: {e}")
            return None

    # Protocol method implementations for DI compatibility
    def get_account_info(self) -> AccountInfo:
        """Protocol-compliant account info method for TradingEngine DI mode.

        Returns AccountInfo-compatible dict as expected by AccountInfoProvider protocol.
        """
        try:
            summary = self.get_account_summary()

            # Map comprehensive summary to protocol-expected format (constrained to AccountInfo keys)
            status: Literal["ACTIVE", "INACTIVE"] = (
                "ACTIVE" if not summary["trading_blocked"] else "INACTIVE"
            )
            return {
                "account_id": summary["account_id"],
                "equity": summary["equity"],
                "cash": summary["cash"],
                "buying_power": summary["buying_power"],
                "day_trades_remaining": max(0, 3 - summary["day_trade_count"]),
                "portfolio_value": summary["equity"],
                "last_equity": summary["last_equity"],
                "daytrading_buying_power": summary["buying_power"],
                "regt_buying_power": summary["buying_power"],
                "status": status,  # Literal["ACTIVE","INACTIVE"]
            }
        except Exception as e:
            self.logger.error(f"Failed to get protocol-compliant account info: {e}")
            raise

    def get_positions_dict(self) -> PositionsDict:
        """Protocol-compliant positions method for TradingEngine DI mode.

        Returns PositionsDict as expected by PositionProvider protocol.
        """
        try:
            positions = self.account_repository.get_positions()
            positions_dict: PositionsDict = {}

            for position in positions:
                symbol = self._get_attr(position, "symbol", "")
                qty = self._get_attr(position, "qty", 0)

                # Only include positions with non-zero quantity
                if symbol and not floats_equal(float(qty), 0.0):
                    positions_dict[symbol] = {
                        "symbol": symbol,
                        "qty": float(qty),
                        "side": "long" if float(qty) > 0 else "short",
                        "market_value": float(self._get_attr(position, "market_value", 0)),
                        "cost_basis": float(self._get_attr(position, "avg_entry_price", 0)),
                        "unrealized_pl": float(self._get_attr(position, "unrealized_pl", 0)),
                        "unrealized_plpc": float(self._get_attr(position, "unrealized_plpc", 0)),
                        "current_price": float(self._get_attr(position, "current_price", 0)),
                    }

            return positions_dict
        except Exception as e:
            self.logger.error(f"Failed to get protocol-compliant positions dict: {e}")
            raise

    def get_current_price(self, symbol: str) -> float:
        """Protocol-compliant price method for TradingEngine DI mode.

        Returns current price as expected by PriceProvider protocol.
        """
        try:
            # AccountRepository does not expose pricing; delegate if underlying repo supports MarketDataRepository
            if hasattr(self.account_repository, "get_current_price"):
                # runtime duck-typing; cast repository to Any and call method directly
                price_func = cast(Any, self.account_repository).get_current_price
                return cast(float, price_func(symbol))
            raise NotImplementedError("Current price not available from AccountRepository")
        except Exception as e:
            self.logger.error(f"Failed to get current price for {symbol}: {e}")
            raise

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Protocol-compliant prices method for TradingEngine DI mode.

        Returns price dict as expected by PriceProvider protocol.
        """
        try:
            if hasattr(self.account_repository, "get_current_prices"):
                prices_func = cast(Any, self.account_repository).get_current_prices
                return cast(dict[str, float], prices_func(symbols))
            raise NotImplementedError("Batch prices not available from AccountRepository")
        except Exception as e:
            self.logger.error(f"Failed to get current prices for {symbols}: {e}")
            raise
