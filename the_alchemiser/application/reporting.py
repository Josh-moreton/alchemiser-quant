"""Helpers for building execution summaries and dashboard data."""

import logging
from typing import Any

from the_alchemiser.core.exceptions import DataProviderError, TradingClientError
from the_alchemiser.domain.strategies.strategy_manager import StrategyType
from the_alchemiser.domain.types import AccountInfo


def create_execution_summary(
    engine: Any,  # TODO: Phase 10 - Add proper TradingEngine type when available
    strategy_signals: dict[StrategyType, Any],
    consolidated_portfolio: dict[str, float],
    orders_executed: list[
        dict[str, Any]
    ],  # TODO: Phase 10 - OrderDetails has different structure than expected
    account_before: AccountInfo,
    account_after: AccountInfo,
) -> dict[str, Any]:  # TODO: Phase 10 - ReportingData structure needs alignment
    """Create execution summary using helper utilities."""
    from the_alchemiser.utils.portfolio_pnl_utils import (
        build_allocation_summary,
        build_strategy_summary,
        calculate_strategy_pnl_summary,
        extract_trading_summary,
    )

    symbols_in_portfolio = set(consolidated_portfolio.keys())
    try:
        current_positions = engine.get_positions()
        symbols_in_portfolio.update(current_positions.keys())
    except TradingClientError as e:
        logging.warning(f"Trading client error getting current positions for P&L: {e}")
    except Exception as e:
        logging.warning(f"Unexpected error getting current positions for P&L: {e}")

    current_prices = engine.get_current_prices(list(symbols_in_portfolio))

    pnl_data = calculate_strategy_pnl_summary(engine.paper_trading, current_prices)
    trading_summary = extract_trading_summary(orders_executed)

    # Convert StrategyType keys to strings for build_strategy_summary
    strategy_signals_str = {k.value: v for k, v in strategy_signals.items()}
    strategy_summary = build_strategy_summary(
        strategy_signals_str,
        engine.strategy_manager.strategy_allocations,
        pnl_data["all_strategy_pnl"],
    )
    allocations = build_allocation_summary(consolidated_portfolio)

    return {
        "allocations": allocations,
        "strategy_summary": strategy_summary,
        "trading_summary": trading_summary,
        "pnl_summary": pnl_data["summary"],
        "account_info_before": account_before,
        "account_info_after": account_after,
    }


def save_dashboard_data(
    engine: Any, execution_result: Any  # TODO: Phase 10 - Add proper types when available
) -> None:
    """Save structured data for dashboard consumption to S3."""
    try:
        from the_alchemiser.infrastructure.s3.s3_utils import get_s3_handler
        from the_alchemiser.utils.dashboard_utils import (
            build_basic_dashboard_structure,
            build_s3_paths,
            extract_portfolio_metrics,
            extract_positions_data,
            extract_recent_trades_data,
            extract_strategies_data,
        )

        s3_handler = get_s3_handler()
        dashboard_data = build_basic_dashboard_structure(engine.paper_trading)
        dashboard_data["success"] = execution_result.success

        if execution_result.account_info_after:
            portfolio_metrics = extract_portfolio_metrics(execution_result.account_info_after)
            dashboard_data["portfolio"].update(portfolio_metrics)
            open_positions = execution_result.account_info_after.get("open_positions", [])
            dashboard_data["positions"] = extract_positions_data(open_positions)

        dashboard_data["strategies"] = extract_strategies_data(
            execution_result.strategy_signals,
            engine.strategy_manager.strategy_allocations,
        )
        dashboard_data["signals"] = {
            (
                strategy_type.value if hasattr(strategy_type, "value") else str(strategy_type)
            ): signal_data
            for strategy_type, signal_data in execution_result.strategy_signals.items()
        }

        if execution_result.orders_executed:
            dashboard_data["recent_trades"] = extract_recent_trades_data(
                execution_result.orders_executed
            )

        latest_path, historical_path = build_s3_paths(engine.paper_trading)
        success = s3_handler.write_json(latest_path, dashboard_data)
        if success:
            s3_handler.write_json(historical_path, dashboard_data)
        else:
            logging.error("Failed to save dashboard data to S3")
    except OSError as e:
        logging.error(f"File/network error saving dashboard data: {e}")
    except DataProviderError as e:
        logging.error(f"Data provider error saving dashboard data: {e}")
    except Exception as e:
        logging.error(f"Unexpected error saving dashboard data: {e}")


def build_portfolio_state_data(
    target_portfolio: dict[str, float],
    account_info: dict[str, Any],
    current_positions: dict[str, Any],
) -> dict[str, Any]:
    """Build portfolio state data for reporting purposes."""
    from the_alchemiser.domain.math.trading_math import calculate_allocation_discrepancy
    from the_alchemiser.services.account_utils import (
        extract_current_position_values,
    )

    portfolio_value = account_info.get("portfolio_value", 0.0)

    # Calculate target values (simple implementation)
    target_values = {
        symbol: weight * portfolio_value for symbol, weight in target_portfolio.items()
    }
    current_values = extract_current_position_values(current_positions)

    allocations = {}
    all_symbols = set(target_portfolio.keys()) | set(current_positions.keys())

    for symbol in all_symbols:
        target_weight = target_portfolio.get(symbol, 0.0)
        target_value = target_values.get(symbol, 0.0)
        current_value = current_values.get(symbol, 0.0)

        current_weight, _ = calculate_allocation_discrepancy(
            target_weight, current_value, portfolio_value
        )

        allocations[symbol] = {
            "target_percent": target_weight * 100,
            "current_percent": current_weight * 100,
            "target_value": target_value,
            "current_value": current_value,
        }

    return {"allocations": allocations}
