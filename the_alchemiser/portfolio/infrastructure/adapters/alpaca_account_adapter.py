"""Business Unit: portfolio assessment & management | Status: current.

Alpaca account adapter for portfolio context.

Handles account information, positions, and portfolio data via Alpaca API.
"""

from __future__ import annotations

import logging
from typing import Any

from the_alchemiser.domain.interfaces import AccountRepository
from the_alchemiser.shared_kernel.infrastructure.base_alpaca_adapter import BaseAlpacaAdapter

logger = logging.getLogger(__name__)


class AlpacaAccountAdapter(BaseAlpacaAdapter, AccountRepository):
    """Alpaca adapter for account and portfolio operations."""

    def get_account(self) -> Any:
        """Get account information.

        Returns:
            Account object with account details

        """
        try:
            client = self.get_trading_client()
            account = client.get_account()
            self.logger.debug(f"Retrieved account: {account.account_number}")
            return account
        except Exception as e:
            self.logger.error(f"Failed to get account: {e}")
            raise

    def get_positions(self) -> list[Any]:
        """Get all positions.

        Returns:
            List of position objects

        """
        try:
            client = self.get_trading_client()
            positions = client.get_all_positions()
            self.logger.debug(f"Retrieved {len(positions)} positions")
            return list(positions)
        except Exception as e:
            self.logger.error(f"Failed to get positions: {e}")
            return []

    def get_positions_dict(self) -> dict[str, float]:
        """Get positions as a dictionary mapping symbol to quantity.

        Returns:
            Dictionary mapping symbols to quantities

        """
        try:
            positions = self.get_positions()
            positions_dict = {}

            for position in positions:
                symbol = position.symbol
                quantity = float(position.qty)
                positions_dict[symbol] = quantity

            self.logger.debug(f"Retrieved positions dict with {len(positions_dict)} symbols")
            return positions_dict
        except Exception as e:
            self.logger.error(f"Failed to get positions dict: {e}")
            return {}

    def get_all_positions(self) -> list[Any]:
        """Get all positions (alias for get_positions).

        Returns:
            List of position objects

        """
        return self.get_positions()

    def get_position(self, symbol: str) -> Any | None:
        """Get position for a specific symbol.

        Args:
            symbol: Symbol to get position for

        Returns:
            Position object or None if not found

        """
        try:
            client = self.get_trading_client()
            position = client.get_open_position(symbol)
            self.logger.debug(f"Retrieved position for {symbol}")
            return position
        except Exception as e:
            self.logger.debug(f"No position found for {symbol}: {e}")
            return None

    def get_buying_power(self) -> float | None:
        """Get current buying power.

        Returns:
            Buying power as float or None if unavailable

        """
        try:
            account = self.get_account()
            buying_power = float(account.buying_power)
            self.logger.debug(f"Buying power: ${buying_power:,.2f}")
            return buying_power
        except Exception as e:
            self.logger.error(f"Failed to get buying power: {e}")
            return None

    def get_portfolio_value(self) -> float | None:
        """Get current portfolio value.

        Returns:
            Portfolio value as float or None if unavailable

        """
        try:
            account = self.get_account()
            portfolio_value = float(account.portfolio_value)
            self.logger.debug(f"Portfolio value: ${portfolio_value:,.2f}")
            return portfolio_value
        except Exception as e:
            self.logger.error(f"Failed to get portfolio value: {e}")
            return None

    def get_portfolio_history(
        self,
        period: str = "1M",
        timeframe: str = "1D",
    ) -> dict[str, Any] | None:
        """Get portfolio history.

        Args:
            period: Time period ('1D', '1W', '1M', '3M', '1A', 'all')
            timeframe: Resolution ('1Min', '5Min', '15Min', '1H', '1D')

        Returns:
            Portfolio history data or None if unavailable

        """
        try:
            client = self.get_trading_client()

            from alpaca.trading.requests import GetPortfolioHistoryRequest

            request = GetPortfolioHistoryRequest(
                period=period,
                timeframe=timeframe,
            )

            history = client.get_portfolio_history(request)

            # Convert to dictionary format
            result = {
                "timestamp": [ts.isoformat() if ts else None for ts in history.timestamp],
                "equity": list(history.equity) if history.equity else [],
                "profit_loss": list(history.profit_loss) if history.profit_loss else [],
                "profit_loss_pct": list(history.profit_loss_pct) if history.profit_loss_pct else [],
                "base_value": float(history.base_value) if history.base_value else 0,
                "timeframe": timeframe,
                "period": period,
            }

            self.logger.debug(f"Retrieved portfolio history for {period}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to get portfolio history: {e}")
            return None

    def get_activities(
        self,
        activity_type: str | None = None,
        date: str | None = None,
        until: str | None = None,
        after: str | None = None,
        direction: str = "desc",
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        """Get account activities.

        Args:
            activity_type: Filter by activity type
            date: Filter by specific date (YYYY-MM-DD)
            until: Filter activities until this date
            after: Filter activities after this date
            direction: Sort direction ('asc' or 'desc')
            page_size: Number of results per page

        Returns:
            List of activity dictionaries

        """
        try:
            client = self.get_trading_client()

            from alpaca.trading.requests import GetAccountActivitiesRequest

            request = GetAccountActivitiesRequest(
                activity_type=activity_type,
                date=date,
                until=until,
                after=after,
                direction=direction,
                page_size=page_size,
            )

            activities = client.get_account_activities(request)

            # Convert to dictionary format
            result = []
            for activity in activities:
                activity_dict = {
                    "id": activity.id,
                    "activity_type": activity.activity_type,
                    "date": activity.date.isoformat() if activity.date else None,
                    "net_amount": float(activity.net_amount) if activity.net_amount else 0,
                    "description": getattr(activity, "description", ""),
                }

                # Add symbol if it's a trade activity
                if hasattr(activity, "symbol"):
                    activity_dict["symbol"] = activity.symbol

                # Add quantity if it's a trade activity
                if hasattr(activity, "qty"):
                    activity_dict["quantity"] = float(activity.qty)

                # Add price if it's a trade activity
                if hasattr(activity, "price"):
                    activity_dict["price"] = float(activity.price)

                result.append(activity_dict)

            self.logger.debug(f"Retrieved {len(result)} activities")
            return result

        except Exception as e:
            self.logger.error(f"Failed to get activities: {e}")
            return []

    def get_recent_closed_positions(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent closed positions from trade activities.

        Args:
            limit: Maximum number of closed positions to return

        Returns:
            List of closed position summaries

        """
        try:
            # Get recent trade activities
            activities = self.get_activities(
                activity_type="FILL",
                page_size=limit * 2,  # Get more to account for opens/closes
            )

            # Group by symbol and calculate P&L
            closed_positions = []
            symbol_trades = {}

            for activity in activities:
                symbol = activity.get("symbol")
                if not symbol:
                    continue

                if symbol not in symbol_trades:
                    symbol_trades[symbol] = []

                symbol_trades[symbol].append(activity)

            # Calculate closed position P&L for each symbol
            for symbol, trades in symbol_trades.items():
                if len(trades) >= 2:  # Need at least open and close
                    # Sort by date
                    trades.sort(key=lambda x: x.get("date", ""))

                    # Calculate net P&L
                    total_amount = sum(trade.get("net_amount", 0) for trade in trades)

                    if abs(total_amount) > 0.01:  # Only include if there's meaningful P&L
                        closed_positions.append(
                            {
                                "symbol": symbol,
                                "realized_pnl": total_amount,
                                "trade_count": len(trades),
                                "last_trade_date": trades[-1].get("date"),
                            }
                        )

                if len(closed_positions) >= limit:
                    break

            self.logger.debug(f"Retrieved {len(closed_positions)} closed positions")
            return closed_positions

        except Exception as e:
            self.logger.error(f"Failed to get recent closed positions: {e}")
            return []

    def get_account_metrics(self) -> dict[str, Any]:
        """Get comprehensive account metrics.

        Returns:
            Dictionary with account metrics

        """
        try:
            account = self.get_account()

            metrics = {
                "account_id": account.account_number,
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "portfolio_value": float(account.portfolio_value),
                "last_equity": float(account.last_equity),
                "daytrading_buying_power": float(account.daytrading_buying_power),
                "regt_buying_power": float(account.regt_buying_power),
                "day_trade_count": account.daytrade_count,
                "pattern_day_trader": account.pattern_day_trader,
                "trading_blocked": account.trading_blocked,
                "transfers_blocked": account.transfers_blocked,
                "account_blocked": account.account_blocked,
                "status": account.status.value if account.status else "UNKNOWN",
            }

            # Calculate additional metrics
            equity = metrics["equity"]
            cash = metrics["cash"]

            if equity > 0:
                metrics["cash_ratio"] = cash / equity

                # Calculate market value from positions
                positions = self.get_positions()
                total_market_value = sum(
                    abs(float(pos.market_value))
                    for pos in positions
                    if hasattr(pos, "market_value") and pos.market_value
                )
                metrics["market_exposure"] = total_market_value / equity
            else:
                metrics["cash_ratio"] = 0
                metrics["market_exposure"] = 0

            self.logger.debug("Retrieved comprehensive account metrics")
            return metrics

        except Exception as e:
            self.logger.error(f"Failed to get account metrics: {e}")
            return {"error": str(e)}
