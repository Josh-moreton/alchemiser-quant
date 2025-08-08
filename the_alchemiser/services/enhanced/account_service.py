import logging
from typing import Any

from the_alchemiser.domain.interfaces import AccountRepository


class AccountService:
    """Enhanced account service providing business logic and validation for account operations"""

    def __init__(self, account_repository: AccountRepository):
        """
        Initialize AccountService

        Args:
            account_repository: Repository for account operations
        """
        self.account_repository = account_repository
        self.logger = logging.getLogger(__name__)

    def _get_attr(self, obj: Any, attr: str, default: Any = 0) -> Any:
        """
        Helper method to safely get attributes from objects or dicts

        Args:
            obj: Object or dict to get attribute from
            attr: Attribute name
            default: Default value if attribute not found

        Returns:
            Attribute value or default
        """
        if hasattr(obj, attr):
            return getattr(obj, attr)
        elif isinstance(obj, dict):
            return obj.get(attr, default)
        return default

    def get_account_summary(self) -> dict[str, Any]:
        """
        Get comprehensive account summary with calculated metrics

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
        """
        Check if account has sufficient buying power for a trade

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
        """
        Calculate comprehensive risk metrics for the account

        Returns:
            Dictionary containing various risk metrics
        """
        try:
            account = self.account_repository.get_account()
            positions = self.account_repository.get_positions()

            equity = float(account.equity)
            cash = float(account.cash)
            long_value = float(account.long_market_value or 0)
            short_value = abs(float(account.short_market_value or 0))
            total_market_value = long_value + short_value

            # Position concentration risk
            position_values = {}
            total_position_value = 0

            for position in positions:
                if position.qty != 0:
                    position_value = abs(float(position.qty) * float(position.market_value or 0))
                    position_values[position.symbol] = position_value
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
                "number_of_positions": len([p for p in positions if p.qty != 0]),
                "long_exposure": round(long_value / equity, 4) if equity > 0 else 0,
                "short_exposure": round(short_value / equity, 4) if equity > 0 else 0,
                "day_trade_count": account.daytrade_count,
                "pattern_day_trader": account.pattern_day_trader,
                "trading_restrictions": {
                    "trading_blocked": account.trading_blocked,
                    "transfers_blocked": account.transfers_blocked,
                    "account_blocked": account.account_blocked,
                },
                "position_breakdown": position_values,
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate risk metrics: {e}")
            raise

    def validate_trade_eligibility(
        self, symbol: str, quantity: int, side: str, estimated_cost: float | None = None
    ) -> dict[str, Any]:
        """
        Validate if a trade can be executed based on account status and buying power

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

            # Basic account checks
            if account.trading_blocked:
                return {
                    "eligible": False,
                    "reason": "Trading is blocked on this account",
                    "details": {"trading_blocked": True},
                }

            if account.account_blocked:
                return {
                    "eligible": False,
                    "reason": "Account is blocked",
                    "details": {"account_blocked": True},
                }

            # Check for existing position
            current_position = None
            for position in positions:
                if position.symbol == symbol:
                    current_position = position
                    break

            current_qty = float(current_position.qty) if current_position else 0

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
            if account.pattern_day_trader and account.daytrade_count >= 3:
                equity = float(account.equity)
                if equity < 25000:
                    return {
                        "eligible": False,
                        "reason": "Pattern day trader with insufficient equity for day trading",
                        "details": {
                            "equity": equity,
                            "minimum_required": 25000,
                            "day_trade_count": account.daytrade_count,
                        },
                    }

            return {
                "eligible": True,
                "reason": "Trade is eligible",
                "details": {
                    "current_position": current_qty,
                    "account_equity": float(account.equity),
                    "buying_power": float(account.buying_power),
                    "day_trade_count": account.daytrade_count,
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to validate trade eligibility: {e}")
            raise

    def get_portfolio_allocation(self) -> dict[str, Any]:
        """
        Calculate portfolio allocation and diversification metrics

        Returns:
            Dictionary containing allocation breakdown
        """
        try:
            account = self.account_repository.get_account()
            positions = self.account_repository.get_positions()

            equity = float(account.equity)
            cash = float(account.cash)

            allocations = {}
            total_position_value = 0

            for position in positions:
                if position.qty != 0:
                    position_value = abs(float(position.qty) * float(position.market_value or 0))
                    allocation_pct = position_value / equity if equity > 0 else 0

                    allocations[position.symbol] = {
                        "quantity": float(position.qty),
                        "market_value": position_value,
                        "allocation_percentage": round(allocation_pct * 100, 2),
                        "unrealized_pl": float(position.unrealized_pl or 0),
                        "unrealized_plpc": float(position.unrealized_plpc or 0),
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
