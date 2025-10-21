"""Business Unit: portfolio assessment & management; Status: current.

Neutral-only portfolio content builder for email templates.

All financial value, P&L, and dollar-based tables have been removed to enforce
the neutral reporting policy. Remaining helpers only expose:
  * Rebalancing instructions (percent weights + action)
  * Open positions (symbol + quantity + status)
  * Account status utilisation (no dollar values)
  * Orders executed (side, symbol, qty, status)

Any reintroduction of financial metrics must go through explicit design review.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable

from the_alchemiser.execution_v2.models.execution_result import ExecutionResult
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.common import MultiStrategyExecutionResult

# Module-level logger
logger = get_logger(__name__)

# Constants for deployment classification thresholds
HIGH_DEPLOYMENT_PCT = Decimal("95.0")
MODERATE_DEPLOYMENT_PCT = Decimal("80.0")
REBALANCE_TOLERANCE = Decimal("0.01")  # 1% tolerance for rebalancing decisions


@runtime_checkable
class ExecutionSummaryLike(Protocol):  # pragma: no cover - structural typing helper
    """Minimal protocol abstraction for execution summary display."""

    execution_summary: dict[str, Any]


ExecutionLike = (
    ExecutionResult | MultiStrategyExecutionResult | Mapping[str, Any] | ExecutionSummaryLike | Any
)


def _normalise_result(result: ExecutionLike) -> dict[str, Any]:
    """Return a plain dict for an execution result (DTO / mapping / object).

    Args:
        result: Execution result in various formats (DTO, mapping, or object)

    Returns:
        Dictionary representation of the execution result

    """
    if isinstance(result, MultiStrategyExecutionResult):  # pragma: no branch
        try:
            return result.model_dump()
        except (AttributeError, TypeError, ValueError) as e:  # pragma: no cover - defensive
            logger.warning(f"Failed to dump MultiStrategyExecutionResult: {e}")
            return {}
    if isinstance(result, Mapping):  # pragma: no branch
        return dict(result)
    extracted: dict[str, Any] = {}
    for attr in (
        "final_portfolio_state",
        "execution_summary",
        "consolidated_portfolio",
        "account_info_after",
        "account_info_before",
        "orders_executed",
        "positions",
        "final_positions",
    ):
        value = getattr(result, attr, None)
        if value is not None:
            extracted[attr] = value
    return extracted


class PortfolioBuilder:
    """Build neutral portfolio HTML fragments (no financial values).

    NOTE: This file has been pruned for the neutral-only policy. Any financial
    metrics (dollar P&L, monetary allocations, etc.) were intentionally removed.
    If you need to reintroduce such data, open a design review first.
    """

    # ---------------------- internal helpers ---------------------- #
    @staticmethod
    def _extract_current_positions(data: dict[str, Any]) -> dict[str, Any]:
        """Extract current positions from execution result data.

        Args:
            data: Execution result dictionary containing account information

        Returns:
            Dictionary mapping symbols to position data

        """
        # First try final_portfolio_state.positions (preferred)
        final_state = data.get("final_portfolio_state", {})
        if isinstance(final_state, dict) and final_state.get("positions"):
            positions_list = final_state.get("positions", [])
            current_positions: dict[str, Any] = {}
            if isinstance(positions_list, list):
                for pos in positions_list:
                    if isinstance(pos, dict) and pos.get("symbol"):
                        current_positions[pos["symbol"]] = pos
                    # Handle Position DTO objects
                    elif hasattr(pos, "symbol"):
                        current_positions[pos.symbol] = {
                            "symbol": pos.symbol,
                            "market_value": getattr(pos, "market_value", 0),
                            "quantity": getattr(pos, "quantity", 0),
                        }
            if current_positions:
                return current_positions

        # Fallback to account_info_before (before trade execution)
        account_before = data.get("account_info_before", {})
        if isinstance(account_before, dict):
            # Try positions field directly if available
            if account_before.get("positions"):
                positions_list = account_before.get("positions", [])
                current_positions = {}
                if isinstance(positions_list, list):
                    for pos in positions_list:
                        if isinstance(pos, dict) and pos.get("symbol"):
                            current_positions[pos["symbol"]] = pos
                        elif hasattr(pos, "symbol"):
                            current_positions[pos.symbol] = {
                                "symbol": pos.symbol,
                                "market_value": getattr(pos, "market_value", 0),
                                "quantity": getattr(pos, "quantity", 0),
                            }
                if current_positions:
                    return current_positions

        # Legacy fallback: account_info_after.open_positions
        account_after = data.get("account_info_after", {})
        if isinstance(account_after, dict) and account_after.get("open_positions"):
            open_positions = account_after.get("open_positions", [])
            current_positions = {}
            if isinstance(open_positions, list):
                for pos in open_positions:
                    if isinstance(pos, dict) and pos.get("symbol"):
                        current_positions[pos["symbol"]] = pos
            return current_positions
        return {}

    @staticmethod
    def _extract_portfolio_value(data: dict[str, Any]) -> Decimal:
        """Extract portfolio value as Decimal for financial calculations.

        Args:
            data: Execution result dictionary containing account information

        Returns:
            Portfolio value as Decimal

        Raises:
            ValueError: If portfolio value is missing or invalid

        """
        account_after = data.get("account_info_after", {})
        if not isinstance(account_after, dict):  # pragma: no cover - defensive
            logger.warning("account_info_after missing or invalid")
            raise ValueError("account_info_after missing or invalid")
        raw = account_after.get("portfolio_value") or account_after.get("equity")
        if raw is None:
            logger.warning("portfolio value unavailable in account data")
            raise ValueError("portfolio value unavailable")
        try:
            return Decimal(str(raw))
        except (TypeError, ValueError, ArithmeticError) as e:  # pragma: no cover - defensive
            logger.warning(f"invalid portfolio value: {raw}, error: {e}")
            raise ValueError("invalid portfolio value") from e

    # ------- helper methods used by neutral public tables (restored) ------- #
    @staticmethod
    def _get_order_action_info(side: str) -> tuple[str, str]:
        """Get color and label for order action (BUY/SELL).

        Args:
            side: Order side string (buy, sell, etc.)

        Returns:
            Tuple of (color_hex, label)

        """
        side_upper = side.upper()
        if side_upper == "BUY":
            return "#10B981", "BUY"
        if side_upper == "SELL":
            return "#EF4444", "SELL"
        return "#6B7280", side_upper

    @staticmethod
    def _get_order_status_info(status: str) -> tuple[str, str]:
        """Get color and display label for order status.

        Args:
            status: Order status string

        Returns:
            Tuple of (color_hex, display_label)

        """
        status_upper = status.upper()
        if status_upper in ("FILLED", "COMPLETE"):
            return "#10B981", "Filled"
        if status_upper in ("PARTIAL", "PARTIALLY_FILLED"):
            return "#F59E0B", "Partial Fill"
        if status_upper in ("PENDING", "NEW", "ACCEPTED", "PENDING_NEW"):
            return "#3B82F6", "Pending"
        if status_upper in ("CANCELLED", "CANCELED", "REJECTED"):
            return "#EF4444", "Cancelled"
        return "#6B7280", status_upper

    @staticmethod
    def _get_order_status_info_from_success(*, success: bool) -> tuple[str, str]:
        """Get color and display label for order status from success boolean.

        Args:
            success: Order success flag from OrderResult

        Returns:
            Tuple of (color_hex, display_label)

        """
        if success:
            return "#10B981", "Success"
        return "#EF4444", "Failed"

    @staticmethod
    def _format_quantity_display(qty: float | int | Decimal | None) -> str:
        """Format quantity for display with appropriate precision.

        Args:
            qty: Quantity value (supports float, int, Decimal, or None)

        Returns:
            Formatted quantity string or em dash if invalid/zero

        """
        if qty is None:
            return "—"
        try:
            qty_val = float(qty) if not isinstance(qty, (int, float)) else qty
            if qty_val != 0:
                return (
                    f"{qty_val:.2f}" if qty_val >= 1 else f"{qty_val:.6f}".rstrip("0").rstrip(".")
                )
        except (TypeError, ValueError, ArithmeticError):
            pass
        return "—"

    # ---------------------- neutral public builders ---------------------- #
    @staticmethod
    def build_account_summary_neutral(account_info: Mapping[str, Any]) -> str:
        """Neutral account summary: status + day trade usage + deployment %.

        Accepts a mapping (AccountInfo or EnrichedAccountInfo). Dollar values are
        not surfaced—only derived deployment percentage.

        Args:
            account_info: Account information mapping

        Returns:
            HTML table with account summary

        """
        status = str(account_info.get("status", "UNKNOWN"))
        remaining = account_info.get("day_trades_remaining")
        used_str = "—"
        if isinstance(remaining, int) and 0 <= remaining <= 3:
            used = 3 - remaining
            used_str = f"{used}/3"
        # Deployment percentage (if equity & cash present) but no raw numbers
        # Use Decimal for financial calculations to avoid float precision issues
        try:
            equity = Decimal(str(account_info.get("equity", 0) or 0))
            cash = Decimal(str(account_info.get("cash", 0) or 0))
            deployed_pct = (equity - cash) / equity * Decimal("100") if equity > 0 else Decimal("0")
        except (TypeError, ValueError, ArithmeticError):  # pragma: no cover - defensive
            logger.warning("Failed to calculate deployment percentage from account info")
            deployed_pct = Decimal("0")

        # Use Decimal comparison with constants for deployment classification
        if deployed_pct >= HIGH_DEPLOYMENT_PCT:
            deploy_color, deploy_label = "#10B981", "High"
        elif deployed_pct >= MODERATE_DEPLOYMENT_PCT:
            deploy_color, deploy_label = "#F59E0B", "Moderate"
        else:
            deploy_color, deploy_label = "#EF4444", "Low"
        status_color = "#10B981" if status == "ACTIVE" else "#EF4444"
        return f"""
        <table style=\"width:100%;border-collapse:collapse;background-color:white;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);margin:16px 0;\">\n            <tbody>\n                <tr>\n                    <td style=\"padding:16px 20px;border-bottom:1px solid #E5E7EB;\"><span style=\"font-weight:600;font-size:14px;color:#374151;\">Account Status:</span></td>\n                    <td style=\"padding:16px 20px;border-bottom:1px solid #E5E7EB;text-align:right;color:{status_color};font-weight:600;font-size:14px;\">{status}</td>\n                </tr>\n                <tr>\n                    <td style=\"padding:16px 20px;border-bottom:1px solid #E5E7EB;\"><span style=\"font-weight:600;font-size:14px;color:#374151;\">Day Trades Used:</span></td>\n                    <td style=\"padding:16px 20px;border-bottom:1px solid #E5E7EB;text-align:right;font-size:14px;color:#1F2937;\">{used_str}</td>\n                </tr>\n                <tr>\n                    <td style=\"padding:16px 20px;border-bottom:1px solid #E5E7EB;\"><span style=\"font-weight:600;font-size:14px;color:#374151;\">Capital Deployment:</span></td>\n                    <td style=\"padding:16px 20px;border-bottom:1px solid #E5E7EB;text-align:right;color:{deploy_color};font-weight:600;font-size:14px;\">{deploy_label} ({deployed_pct:.1f}%)</td>\n                </tr>\n            </tbody>\n        </table>\n        """

    @staticmethod
    def build_portfolio_rebalancing_table(result: ExecutionLike) -> str:
        """Percent-only rebalancing actions (BUY/SELL/HOLD) vs target weights.

        Args:
            result: Execution result containing portfolio data

        Returns:
            HTML table showing rebalancing actions

        """
        data = _normalise_result(result)
        target_portfolio = (
            data.get("consolidated_portfolio")
            or data.get("execution_summary", {}).get("consolidated_portfolio", {})
            or {}
        )
        if not target_portfolio:
            return "<p>No target portfolio data available</p>"
        current_positions = PortfolioBuilder._extract_current_positions(data)
        # Build current value map if present (market_value fields) for weight estimation
        # Use Decimal for financial calculations to avoid float precision issues
        current_values: dict[str, Decimal] = {}
        for sym, pos in current_positions.items():
            try:
                market_val = Decimal(str(pos.get("market_value", 0) or 0))
                current_values[sym] = market_val
            except (TypeError, ValueError, ArithmeticError):  # pragma: no cover
                logger.debug(f"Failed to parse market_value for {sym}")
                continue
        total_value = sum(current_values.values())
        rows: list[str] = []
        for symbol in sorted(target_portfolio.keys()):
            # Convert target weight to Decimal for precise comparison
            target_weight = Decimal(str(target_portfolio.get(symbol, 0.0)))
            if total_value > 0:
                current_weight = current_values.get(symbol, Decimal("0")) / total_value
            else:
                current_weight = Decimal("0")
            diff = target_weight - current_weight
            # Use math.isclose for float comparison with explicit tolerance
            if math.isclose(float(diff), 0.0, abs_tol=float(REBALANCE_TOLERANCE)):
                action, color = "HOLD", "#6B7280"
            elif diff > 0:
                action, color = "BUY", "#10B981"
            else:
                action, color = "SELL", "#EF4444"
            # Convert to float for display formatting
            target_pct = float(target_weight)
            current_pct = float(current_weight)
            rows.append(
                f"""
                <tr>
                    <td style=\"padding:12px 16px;border-bottom:1px solid #E5E7EB;font-weight:600;color:#1F2937;\">{symbol}</td>
                    <td style=\"padding:12px 16px;border-bottom:1px solid #E5E7EB;text-align:center;color:#059669;\">{target_pct:.1%}</td>
                    <td style=\"padding:12px 16px;border-bottom:1px solid #E5E7EB;text-align:center;color:#374151;\">{current_pct:.1%}</td>
                    <td style=\"padding:12px 16px;border-bottom:1px solid #E5E7EB;text-align:center;font-weight:600;color:{color};\">{action}</td>
                </tr>
                """
            )
        body = "".join(rows)
        return f"""
        <table style=\"width:100%;border-collapse:collapse;background-color:white;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);margin:16px 0;\">\n            <thead>\n                <tr style=\"background-color:#F9FAFB;\">\n                    <th style=\"padding:12px 16px;text-align:left;font-weight:600;color:#374151;border-bottom:2px solid #E5E7EB;\">Symbol</th>\n                    <th style=\"padding:12px 16px;text-align:center;font-weight:600;color:#374151;border-bottom:2px solid #E5E7EB;\">Target %</th>\n                    <th style=\"padding:12px 16px;text-align:center;font-weight:600;color:#374151;border-bottom:2px solid #E5E7EB;\">Current %</th>\n                    <th style=\"padding:12px 16px;text-align:center;font-weight:600;color:#374151;border-bottom:2px solid #E5E7EB;\">Action</th>\n                </tr>\n            </thead>\n            <tbody>{body}</tbody>\n        </table>\n        """

    @staticmethod
    def build_orders_table_neutral(orders: list[Any]) -> str:
        """Build a neutral orders table without financial values.

        Args:
            orders: List of order dictionaries

        Returns:
            HTML table with order details

        """
        if not orders:
            return """
            <div style="text-align: center; padding: 20px; color: #6B7280;">
                <p>No orders executed</p>
            </div>
            """

        # Start building the table
        table_html = """
        <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin: 16px 0;">
            <thead>
                <tr style="background-color: #F9FAFB;">
                    <th style="padding: 12px 16px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                        Action
                    </th>
                    <th style="padding: 12px 16px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                        Symbol
                    </th>
                    <th style="padding: 12px 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                        Quantity
                    </th>
                    <th style="padding: 12px 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                        Status
                    </th>
                </tr>
            </thead>
            <tbody>
        """

        for order in orders:
            # Extract order details safely from OrderResult model fields
            # OrderResult uses: action (not side), shares (not qty), success (not status)
            action = str(order.get("action", ""))
            symbol = str(order.get("symbol", ""))
            shares = order.get("shares", 0)
            success = order.get("success", False)

            # Use helper methods for formatting
            action_color, action_label = PortfolioBuilder._get_order_action_info(action)
            status_color, status_display = PortfolioBuilder._get_order_status_info_from_success(
                success=success
            )
            qty_display = PortfolioBuilder._format_quantity_display(shares)

            table_html += f"""
                <tr>
                    <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: {action_color};">
                        {action_label}
                    </td>
                    <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: #1F2937;">
                        {symbol}
                    </td>
                    <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: center; color: #374151;">
                        {qty_display}
                    </td>
                    <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: center; color: {status_color}; font-weight: 600;">
                        {status_display}
                    </td>
                </tr>
            """

        table_html += """
            </tbody>
        </table>
        """

        return table_html


# Backwards compatibility alias - maintained for legacy code
# TODO: Consider deprecating this alias in favor of explicit class method usage
build_account_summary = PortfolioBuilder.build_account_summary_neutral
