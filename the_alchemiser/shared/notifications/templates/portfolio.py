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

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from the_alchemiser.execution_v2.models.execution_result import ExecutionResultDTO
from the_alchemiser.shared.schemas.common import MultiStrategyExecutionResultDTO


@runtime_checkable
class ExecutionSummaryLike(Protocol):  # pragma: no cover - structural typing helper
    """Minimal protocol abstraction for execution summary display."""

    execution_summary: dict[str, Any]


ExecutionLike = (
    ExecutionResultDTO
    | MultiStrategyExecutionResultDTO
    | Mapping[str, Any]
    | ExecutionSummaryLike
    | Any
)


def _normalise_result(result: ExecutionLike) -> dict[str, Any]:
    """Return a plain dict for an execution result (DTO / mapping / object)."""
    if isinstance(result, MultiStrategyExecutionResultDTO):  # pragma: no branch
        try:
            return result.model_dump()
        except Exception:  # pragma: no cover - defensive
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
        account_after = data.get("account_info_after", {})
        if isinstance(account_after, dict) and account_after.get("open_positions"):
            open_positions = account_after.get("open_positions", [])
            current_positions: dict[str, Any] = {}
            if isinstance(open_positions, list):
                for pos in open_positions:
                    if isinstance(pos, dict) and pos.get("symbol"):
                        current_positions[pos["symbol"]] = pos
            return current_positions
        return {}

    @staticmethod
    def _extract_portfolio_value(data: dict[str, Any]) -> float:
        account_after = data.get("account_info_after", {})
        if not isinstance(account_after, dict):  # pragma: no cover - defensive
            raise ValueError("account_info_after missing or invalid")
        raw = account_after.get("portfolio_value") or account_after.get("equity")
        if raw is None:
            raise ValueError("portfolio value unavailable")
        try:
            return float(raw)
        except (TypeError, ValueError) as e:  # pragma: no cover - defensive
            raise ValueError("invalid portfolio value") from e

    # ------- helper methods used by neutral public tables (restored) ------- #
    @staticmethod
    def _get_order_action_info(side: str) -> tuple[str, str]:
        side_upper = side.upper()
        if side_upper == "BUY":
            return "#10B981", "📈"
        if side_upper == "SELL":
            return "#EF4444", "📉"
        return "#6B7280", "📊"

    @staticmethod
    def _get_order_status_info(status: str) -> tuple[str, str]:
        status_upper = status.upper()
        if status_upper in ("FILLED", "COMPLETE"):
            return "#10B981", f"✅ {status_upper}"
        if status_upper in ("PARTIAL", "PARTIALLY_FILLED"):
            return "#F59E0B", f"🔄 {status_upper}"
        if status_upper in ("PENDING", "NEW", "ACCEPTED", "PENDING_NEW"):
            return "#3B82F6", f"⏳ {status_upper}"
        if status_upper in ("CANCELLED", "CANCELED", "REJECTED"):
            return "#EF4444", f"❌ {status_upper}"
        # Use ASCII 'i' instead of the info symbol to avoid ambiguous unicode lint warning
        return "#6B7280", f"i {status_upper}"

    @staticmethod
    def _format_quantity_display(qty: Any) -> str:  # noqa: ANN401
        if isinstance(qty, (int, float)) and qty != 0:
            return f"{qty:.2f}" if qty >= 1 else f"{qty:.6f}".rstrip("0").rstrip(".")
        return "—"

    # ---------------------- neutral public builders ---------------------- #
    @staticmethod
    def build_account_summary_neutral(account_info: Mapping[str, Any]) -> str:
        """Neutral account summary: status + day trade usage + deployment %.

        Accepts a mapping (AccountInfo or EnrichedAccountInfo). Dollar values are
        not surfaced—only derived deployment percentage.
        """
        status = str(account_info.get("status", "UNKNOWN"))
        remaining = account_info.get("day_trades_remaining")
        used_str = "—"
        if isinstance(remaining, int) and 0 <= remaining <= 3:
            used = 3 - remaining
            used_str = f"{used}/3"
        # Deployment percentage (if equity & cash present) but no raw numbers
        try:
            equity = float(account_info.get("equity", 0) or 0)
            cash = float(account_info.get("cash", 0) or 0)
            deployed_pct = (equity - cash) / equity * 100 if equity > 0 else 0.0
        except (TypeError, ValueError):  # pragma: no cover - defensive
            deployed_pct = 0.0
        if deployed_pct >= 95:
            deploy_color, deploy_emoji = "#10B981", "🟢"
        elif deployed_pct >= 80:
            deploy_color, deploy_emoji = "#F59E0B", "🟡"
        else:
            deploy_color, deploy_emoji = "#EF4444", "🔴"
        status_color = "#10B981" if status == "ACTIVE" else "#EF4444"
        return f"""
        <table style=\"width:100%;border-collapse:collapse;background-color:white;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);margin:16px 0;\">\n            <tbody>\n                <tr>\n                    <td style=\"padding:16px 20px;border-bottom:1px solid #E5E7EB;\"><span style=\"font-weight:600;font-size:14px;\">Account Status:</span></td>\n                    <td style=\"padding:16px 20px;border-bottom:1px solid #E5E7EB;text-align:right;color:{status_color};font-weight:600;font-size:14px;\">{status}</td>\n                </tr>\n                <tr>\n                    <td style=\"padding:16px 20px;border-bottom:1px solid #E5E7EB;\"><span style=\"font-weight:600;font-size:14px;\">Day Trades Used:</span></td>\n                    <td style=\"padding:16px 20px;border-bottom:1px solid #E5E7EB;text-align:right;font-size:14px;\">{used_str}</td>\n                </tr>\n                <tr>\n                    <td style=\"padding:16px 20px;border-bottom:1px solid #E5E7EB;\"><span style=\"font-weight:600;font-size:14px;\">Portfolio Deployed:</span></td>\n                    <td style=\"padding:16px 20px;border-bottom:1px solid #E5E7EB;text-align:right;color:{deploy_color};font-weight:600;font-size:14px;\">{deploy_emoji} {deployed_pct:.1f}%</td>\n                </tr>\n            </tbody>\n        </table>\n        """

    @staticmethod
    def build_portfolio_rebalancing_table(result: ExecutionLike) -> str:
        """Percent-only rebalancing actions (BUY/SELL/HOLD) vs target weights."""
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
        current_values: dict[str, float] = {}
        for sym, pos in current_positions.items():
            try:
                current_values[sym] = float(pos.get("market_value", 0) or 0)
            except (TypeError, ValueError):  # pragma: no cover
                continue
        total_value = sum(current_values.values())
        rows: list[str] = []
        for symbol in sorted(target_portfolio.keys()):
            target_weight = float(target_portfolio.get(symbol, 0.0))
            current_weight = (
                (current_values.get(symbol, 0.0) / total_value) if total_value > 0 else 0.0
            )
            diff = target_weight - current_weight
            if abs(diff) < 0.01:
                action, color = "HOLD", "#6B7280"
            elif diff > 0:
                action, color = "BUY", "#10B981"
            else:
                action, color = "SELL", "#EF4444"
            rows.append(
                f"""
                <tr>
                    <td style=\"padding:12px 16px;border-bottom:1px solid #E5E7EB;font-weight:600;color:#1F2937;\">{symbol}</td>
                    <td style=\"padding:12px 16px;border-bottom:1px solid #E5E7EB;text-align:center;color:#059669;\">{target_weight:.1%}</td>
                    <td style=\"padding:12px 16px;border-bottom:1px solid #E5E7EB;text-align:center;color:#374151;\">{current_weight:.1%}</td>
                    <td style=\"padding:12px 16px;border-bottom:1px solid #E5E7EB;text-align:center;font-weight:600;color:{color};\">{action}</td>
                </tr>
                """
            )
        body = "".join(rows)
        return f"""
        <table style=\"width:100%;border-collapse:collapse;background-color:white;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);margin:16px 0;\">\n            <thead>\n                <tr style=\"background-color:#F9FAFB;\">\n                    <th style=\"padding:12px 16px;text-align:left;font-weight:600;color:#374151;border-bottom:2px solid #E5E7EB;\">Symbol</th>\n                    <th style=\"padding:12px 16px;text-align:center;font-weight:600;color:#374151;border-bottom:2px solid #E5E7EB;\">Target %</th>\n                    <th style=\"padding:12px 16px;text-align:center;font-weight:600;color:#374151;border-bottom:2px solid #E5E7EB;\">Current %</th>\n                    <th style=\"padding:12px 16px;text-align:center;font-weight:600;color:#374151;border-bottom:2px solid #E5E7EB;\">Action</th>\n                </tr>\n            </thead>\n            <tbody>{body}</tbody>\n        </table>\n        """

    @staticmethod
    def build_orders_table_neutral(orders: list[Any]) -> str:
        """Build a neutral orders table without financial values."""
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
            # Extract order details safely
            side = str(order.get("side", ""))
            symbol = str(order.get("symbol", ""))
            qty = order.get("qty", 0)
            status = str(order.get("status", "unknown"))

            # Use helper methods for formatting
            action_color, action_emoji = PortfolioBuilder._get_order_action_info(side)
            status_color, status_display = PortfolioBuilder._get_order_status_info(status)
            qty_display = PortfolioBuilder._format_quantity_display(qty)

            table_html += f"""
                <tr>
                    <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: {action_color};">
                        {action_emoji} {side.upper()}
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


# Backwards compatibility alias
build_account_summary = PortfolioBuilder.build_account_summary_neutral
