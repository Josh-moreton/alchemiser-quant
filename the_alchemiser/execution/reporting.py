import logging
from typing import Any

from the_alchemiser.core.trading.strategy_manager import StrategyType


def create_execution_summary(
    engine,
    strategy_signals: dict[StrategyType, Any],
    consolidated_portfolio: dict[str, float],
    orders_executed: list[dict],
    account_before: dict,
    account_after: dict,
) -> dict:
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
    except Exception as e:
        logging.warning(f"Failed to get current positions for P&L: {e}")

    current_prices = engine.get_current_prices(list(symbols_in_portfolio))

    pnl_data = calculate_strategy_pnl_summary(engine.paper_trading, current_prices)
    trading_summary = extract_trading_summary(orders_executed)
    strategy_summary = build_strategy_summary(
        strategy_signals,
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


def save_dashboard_data(engine, execution_result):
    """Save structured data for dashboard consumption to S3."""
    try:
        from the_alchemiser.core.utils.s3_utils import get_s3_handler
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
    except Exception as e:
        logging.error(f"Failed to save dashboard data: {e}")


def build_portfolio_state_data(
    target_portfolio: dict[str, float],
    account_info: dict,
    current_positions: dict,
) -> dict:
    """Build portfolio state data for reporting purposes."""
    from the_alchemiser.utils.account_utils import (
        calculate_portfolio_values,
        extract_current_position_values,
    )
    from the_alchemiser.utils.trading_math import calculate_allocation_discrepancy

    portfolio_value = account_info.get("portfolio_value", 0.0)
    target_values = calculate_portfolio_values(target_portfolio, account_info)
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
