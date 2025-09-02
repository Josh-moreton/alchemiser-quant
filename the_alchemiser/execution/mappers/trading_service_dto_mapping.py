#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

DTO mapping utilities for TradingServiceManager results.

This module provides mapping functions to convert between internal data structures
and DTOs for the TradingServiceManager facade, ensuring type-safe returns.

Part of the anti-corruption layer for clean DTO boundaries.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from the_alchemiser.execution.mappers.account_mapping import (
    AccountSummaryTyped,
)
from the_alchemiser.portfolio.mappers.position_mapping import PositionSummary
from the_alchemiser.shared.schemas.accounts import (
    AccountMetricsDTO,
    AccountSummaryDTO,
    BuyingPowerDTO,
    EnrichedAccountSummaryDTO,
    PortfolioAllocationDTO,
    RiskMetricsDTO,
    TradeEligibilityDTO,
)
from the_alchemiser.shared.schemas.enriched_data import (
    EnrichedOrderDTO,
    EnrichedPositionDTO,
    EnrichedPositionsDTO,
    OpenOrdersDTO,
)
from the_alchemiser.shared.schemas.market_data import (
    MarketStatusDTO,
    MultiSymbolQuotesDTO,
    PriceDTO,
    PriceHistoryDTO,
    SpreadAnalysisDTO,
)
from the_alchemiser.shared.schemas.operations import (
    OperationResultDTO,
    OrderCancellationDTO,
    OrderStatusDTO,
)
from the_alchemiser.portfolio.schemas.positions import (
    ClosePositionResultDTO,
    LargestPositionDTO,
    PortfolioMetricsDTO,
    PortfolioSummaryDTO,
    PositionAnalyticsDTO,
    PositionDTO,
    PositionMetricsDTO,
    PositionSummaryDTO,
)


# Position Mapping Functions
def position_summary_to_dto(position_summary: PositionSummary) -> PositionDTO:
    """Convert PositionSummary dataclass to PositionDTO."""
    return PositionDTO(
        symbol=position_summary.symbol,
        quantity=position_summary.qty,
        average_entry_price=position_summary.avg_entry_price,
        current_price=position_summary.current_price,
        market_value=position_summary.market_value,
        unrealized_pnl=position_summary.unrealized_pl,
        unrealized_pnl_percent=position_summary.unrealized_plpc,
    )


def dict_to_position_summary_dto(data: dict[str, Any]) -> PositionSummaryDTO:
    """Convert position summary dict to PositionSummaryDTO."""
    if not data.get("success", False):
        return PositionSummaryDTO(success=False, error=data.get("error", "Unknown error"))

    position_data = data.get("position")
    if position_data:
        position_dto = PositionDTO(
            symbol=data.get("symbol", ""),
            quantity=Decimal(str(position_data.get("quantity", 0))),
            average_entry_price=Decimal(str(position_data.get("avg_entry_price", 0))),
            current_price=Decimal(str(position_data.get("current_price", 0))),
            market_value=Decimal(str(position_data.get("market_value", 0))),
            unrealized_pnl=Decimal(str(position_data.get("unrealized_pnl", 0))),
            unrealized_pnl_percent=Decimal(str(position_data.get("unrealized_plpc", 0))),
        )
    else:
        position_dto = None

    return PositionSummaryDTO(success=True, symbol=data.get("symbol"), position=position_dto)


def dict_to_portfolio_summary_dto(data: dict[str, Any]) -> PortfolioSummaryDTO:
    """Convert portfolio summary dict to PortfolioSummaryDTO."""
    if not data.get("success", False):
        return PortfolioSummaryDTO(success=False, error=data.get("error", "Unknown error"))

    portfolio_data = data.get("portfolio")
    if portfolio_data:
        portfolio_metrics = PortfolioMetricsDTO(
            total_market_value=Decimal(str(portfolio_data.get("total_market_value", 0))),
            cash_balance=Decimal(str(portfolio_data.get("cash_balance", 0))),
            total_positions=int(portfolio_data.get("total_positions", 0)),
            largest_position_percent=Decimal(
                str(portfolio_data.get("largest_position_percent", 0))
            ),
        )
    else:
        portfolio_metrics = None

    return PortfolioSummaryDTO(success=True, portfolio=portfolio_metrics)


def dict_to_close_position_dto(data: dict[str, Any]) -> ClosePositionResultDTO:
    """Convert close position result dict to ClosePositionResultDTO."""
    return ClosePositionResultDTO(
        success=data.get("success", False), order_id=data.get("order_id"), error=data.get("error")
    )


def dict_to_position_analytics_dto(data: dict[str, Any]) -> PositionAnalyticsDTO:
    """Convert position analytics dict to PositionAnalyticsDTO."""
    return PositionAnalyticsDTO(
        success=data.get("success", False),
        symbol=data.get("symbol"),
        risk_metrics=data.get("risk_metrics"),
        error=data.get("error"),
    )


def dict_to_position_metrics_dto(data: dict[str, Any]) -> PositionMetricsDTO:
    """Convert position metrics dict to PositionMetricsDTO."""
    if not data.get("success", False):
        return PositionMetricsDTO(success=False, error=data.get("error", "Unknown error"))

    largest_positions = []
    if data.get("largest_positions"):
        for pos in data["largest_positions"]:
            largest_positions.append(
                LargestPositionDTO(
                    symbol=pos.get("symbol", ""),
                    weight_percent=Decimal(str(pos.get("weight", 0))),
                    market_value=Decimal(str(pos.get("value", 0))),
                )
            )

    return PositionMetricsDTO(
        success=True,
        diversification_score=Decimal(str(data.get("diversification_score", 0))),
        largest_positions=largest_positions,
    )


# Account Mapping Functions
def account_summary_typed_to_dto(account_summary: AccountSummaryTyped) -> AccountSummaryDTO:
    """Convert AccountSummaryTyped to AccountSummaryDTO."""
    metrics_dto = AccountMetricsDTO(
        cash_ratio=account_summary.calculated_metrics.cash_ratio,
        market_exposure=account_summary.calculated_metrics.market_exposure,
        leverage_ratio=account_summary.calculated_metrics.leverage_ratio,
        available_buying_power_ratio=account_summary.calculated_metrics.available_buying_power_ratio,
    )

    return AccountSummaryDTO(
        account_id=account_summary.account_id,
        equity=account_summary.equity.amount,
        cash=account_summary.cash.amount,
        market_value=account_summary.market_value.amount,
        buying_power=account_summary.buying_power.amount,
        last_equity=account_summary.last_equity.amount,
        day_trade_count=account_summary.day_trade_count,
        pattern_day_trader=account_summary.pattern_day_trader,
        trading_blocked=account_summary.trading_blocked,
        transfers_blocked=account_summary.transfers_blocked,
        account_blocked=account_summary.account_blocked,
        calculated_metrics=metrics_dto,
    )


def dict_to_enriched_account_summary_dto(data: dict[str, Any]) -> EnrichedAccountSummaryDTO:
    """Convert enriched account summary dict to EnrichedAccountSummaryDTO."""
    summary_data = data.get("summary", {})

    metrics_data = summary_data.get("calculated_metrics", {})
    metrics_dto = AccountMetricsDTO(
        cash_ratio=Decimal(str(metrics_data.get("cash_ratio", 0))),
        market_exposure=Decimal(str(metrics_data.get("market_exposure", 0))),
        leverage_ratio=(
            Decimal(str(metrics_data.get("leverage_ratio")))
            if metrics_data.get("leverage_ratio") is not None
            else None
        ),
        available_buying_power_ratio=Decimal(
            str(metrics_data.get("available_buying_power_ratio", 0))
        ),
    )

    summary_dto = AccountSummaryDTO(
        account_id=summary_data.get("account_id", ""),
        equity=Decimal(str(summary_data.get("equity", 0))),
        cash=Decimal(str(summary_data.get("cash", 0))),
        market_value=Decimal(str(summary_data.get("market_value", 0))),
        buying_power=Decimal(str(summary_data.get("buying_power", 0))),
        last_equity=Decimal(str(summary_data.get("last_equity", 0))),
        day_trade_count=int(summary_data.get("day_trade_count", 0)),
        pattern_day_trader=bool(summary_data.get("pattern_day_trader", False)),
        trading_blocked=bool(summary_data.get("trading_blocked", False)),
        transfers_blocked=bool(summary_data.get("transfers_blocked", False)),
        account_blocked=bool(summary_data.get("account_blocked", False)),
        calculated_metrics=metrics_dto,
    )

    return EnrichedAccountSummaryDTO(raw=data.get("raw", {}), summary=summary_dto)


def dict_to_buying_power_dto(data: dict[str, Any]) -> BuyingPowerDTO:
    """Convert buying power check dict to BuyingPowerDTO."""
    return BuyingPowerDTO(
        success=data.get("success", False),
        available_buying_power=(
            Decimal(str(data.get("available_buying_power")))
            if data.get("available_buying_power") is not None
            else None
        ),
        required_amount=(
            Decimal(str(data.get("required_amount")))
            if data.get("required_amount") is not None
            else None
        ),
        sufficient_funds=data.get("sufficient_funds"),
        error=data.get("error"),
    )


def dict_to_risk_metrics_dto(data: dict[str, Any]) -> RiskMetricsDTO:
    """Convert risk metrics dict to RiskMetricsDTO."""
    return RiskMetricsDTO(
        success=data.get("success", False),
        risk_metrics=data.get("risk_metrics"),
        error=data.get("error"),
    )


def dict_to_trade_eligibility_dto(data: dict[str, Any]) -> TradeEligibilityDTO:
    """Convert trade eligibility dict to TradeEligibilityDTO."""
    return TradeEligibilityDTO(
        eligible=data.get("eligible", False),
        reason=data.get("reason"),
        details=data.get("details"),
        symbol=data.get("symbol"),
        quantity=data.get("quantity"),
        side=data.get("side"),
        estimated_cost=(
            Decimal(str(data.get("estimated_cost")))
            if data.get("estimated_cost") is not None
            else None
        ),
    )


def dict_to_portfolio_allocation_dto(data: dict[str, Any]) -> PortfolioAllocationDTO:
    """Convert portfolio allocation dict to PortfolioAllocationDTO."""
    return PortfolioAllocationDTO(
        success=data.get("success", False),
        allocation_data=data.get("allocation_data"),
        error=data.get("error"),
    )


# Market Data Mapping Functions
def dict_to_price_dto(data: dict[str, Any]) -> PriceDTO:
    """Convert latest price dict to PriceDTO."""
    return PriceDTO(
        success=data.get("success", False),
        symbol=data.get("symbol"),
        price=Decimal(str(data.get("price"))) if data.get("price") is not None else None,
        error=data.get("error"),
    )


def dict_to_price_history_dto(data: dict[str, Any]) -> PriceHistoryDTO:
    """Convert price history dict to PriceHistoryDTO."""
    return PriceHistoryDTO(
        success=data.get("success", False),
        symbol=data.get("symbol"),
        timeframe=data.get("timeframe"),
        limit=data.get("limit"),
        data=data.get("data"),
        error=data.get("error"),
    )


def dict_to_spread_analysis_dto(data: dict[str, Any]) -> SpreadAnalysisDTO:
    """Convert spread analysis dict to SpreadAnalysisDTO."""
    return SpreadAnalysisDTO(
        success=data.get("success", False),
        symbol=data.get("symbol"),
        spread_analysis=data.get("spread_analysis"),
        error=data.get("error"),
    )


def dict_to_market_status_dto(data: dict[str, Any]) -> MarketStatusDTO:
    """Convert market status dict to MarketStatusDTO."""
    return MarketStatusDTO(
        success=data.get("success", False),
        market_open=data.get("market_open"),
        error=data.get("error"),
    )


def dict_to_multi_symbol_quotes_dto(data: dict[str, Any]) -> MultiSymbolQuotesDTO:
    """Convert multi-symbol quotes dict to MultiSymbolQuotesDTO."""
    quotes = None
    if data.get("quotes"):
        quotes = {symbol: Decimal(str(price)) for symbol, price in data["quotes"].items()}

    return MultiSymbolQuotesDTO(
        success=data.get("success", False),
        quotes=quotes,
        symbols=list(data.get("quotes", {}).keys()) if data.get("quotes") else None,
        error=data.get("error"),
    )


# Operation Mapping Functions
def dict_to_order_cancellation_dto(data: dict[str, Any]) -> OrderCancellationDTO:
    """Convert order cancellation dict to OrderCancellationDTO."""
    return OrderCancellationDTO(
        success=data.get("success", False), order_id=data.get("order_id"), error=data.get("error")
    )


def dict_to_order_status_dto(data: dict[str, Any]) -> OrderStatusDTO:
    """Convert order status dict to OrderStatusDTO."""
    return OrderStatusDTO(
        success=data.get("success", False),
        order_id=data.get("order_id"),
        status=data.get("status"),
        error=data.get("error"),
    )


def dict_to_operation_result_dto(data: dict[str, Any]) -> OperationResultDTO:
    """Convert generic operation result dict to OperationResultDTO."""
    return OperationResultDTO(
        success=data.get("success", False), error=data.get("error"), details=data.get("details")
    )


# Enriched Data Mapping Functions
def list_to_open_orders_dto(
    orders: list[dict[str, Any]], symbol_filter: str | None = None
) -> OpenOrdersDTO:
    """Convert list of enriched order dicts to OpenOrdersDTO."""
    enriched_orders = []
    for order in orders:
        enriched_orders.append(
            EnrichedOrderDTO(
                raw=order.get("raw", {}),
                domain=order.get("domain", {}),
                summary=order.get("summary", {}),
            )
        )

    return OpenOrdersDTO(success=True, orders=enriched_orders, symbol_filter=symbol_filter)


def list_to_enriched_positions_dto(positions: list[dict[str, Any]]) -> EnrichedPositionsDTO:
    """Convert list of enriched position dicts to EnrichedPositionsDTO."""
    enriched_positions = []
    for position in positions:
        enriched_positions.append(
            EnrichedPositionDTO(
                raw=position.get("raw", {}),
                summary=position.get("summary", {}),
            )
        )

    return EnrichedPositionsDTO(success=True, positions=enriched_positions)
