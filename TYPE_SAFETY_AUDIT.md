# Type Safety Audit


This report lists Python files with missing or imprecise type hints, based on static analysis.


| File | First untyped function |
| --- | --- |
| `fix_type_params.py` | fix_file_type_params at line 8 |
| `the_alchemiser/backtest/cli.py` | main at line 253 |
| `the_alchemiser/backtest/data_cache.py` | clear_global_cache at line 613 |
| `the_alchemiser/backtest/data_loader.py` | __init__ at line 37 |
| `the_alchemiser/backtest/engine.py` | __str__ at line 59 |
| `the_alchemiser/backtest/metrics.py` | __str__ at line 31 |
| `the_alchemiser/backtest/strategies/__init__.py` | __init__ at line 28 |
| `the_alchemiser/cli.py` | show_welcome at line 32 |
| `the_alchemiser/config/execution_config.py` | reload_execution_config at line 90 |
| `the_alchemiser/core/alerts/alert_service.py` | create_alert at line 34 |
| `the_alchemiser/core/config.py` | settings_customise_sources at line 107 |
| `the_alchemiser/core/data/data_provider.py` | __init__ at line 27 |
| `the_alchemiser/core/data/real_time_pricing.py` | mid_price at line 50 |
| `the_alchemiser/core/exceptions.py` | __init__ at line 39 |
| `the_alchemiser/core/indicators/indicators.py` | rsi at line 38 |
| `the_alchemiser/core/logging/logging_utils.py` | process at line 13 |
| `the_alchemiser/core/registry/strategy_registry.py` | get_strategy_config at line 72 |
| `the_alchemiser/core/secrets/secrets_manager.py` | __init__ at line 24 |
| `the_alchemiser/core/trading/klm_ensemble_engine.py` | main at line 407 |
| `the_alchemiser/core/trading/klm_trading_bot.py` | main at line 253 |
| `the_alchemiser/core/trading/klm_workers/base_klm_variant.py` | __init__ at line 26 |
| `the_alchemiser/core/trading/klm_workers/variant_1200_28.py` | __init__ at line 26 |
| `the_alchemiser/core/trading/klm_workers/variant_1280_26.py` | __init__ at line 32 |
| `the_alchemiser/core/trading/klm_workers/variant_410_38.py` | __init__ at line 23 |
| `the_alchemiser/core/trading/klm_workers/variant_506_38.py` | __init__ at line 33 |
| `the_alchemiser/core/trading/klm_workers/variant_520_22.py` | __init__ at line 28 |
| `the_alchemiser/core/trading/klm_workers/variant_530_18.py` | __init__ at line 41 |
| `the_alchemiser/core/trading/klm_workers/variant_830_21.py` | __init__ at line 28 |
| `the_alchemiser/core/trading/klm_workers/variant_nova.py` | __init__ at line 30 |
| `the_alchemiser/core/trading/nuclear_signals.py` | get_best_nuclear_stocks at line 48 |
| `the_alchemiser/core/trading/strategy_engine.py` | __init__ at line 27 |
| `the_alchemiser/core/trading/strategy_manager.py` | main at line 465 |
| `the_alchemiser/core/trading/tecl_signals.py` | __init__ at line 47 |
| `the_alchemiser/core/trading/tecl_strategy_engine.py` | main at line 351 |
| `the_alchemiser/core/ui/email/client.py` | __init__ at line 20 |
| `the_alchemiser/core/ui/email/config.py` | __init__ at line 16 |
| `the_alchemiser/core/ui/email/templates/__init__.py` | build_trading_report at line 42 |
| `the_alchemiser/core/ui/email/templates/signals.py` | build_signal_information at line 16 |
| `the_alchemiser/core/ui/email/templates/trading_report.py` | build_regular_report at line 18 |
| `the_alchemiser/core/ui/email_utils.py` | _build_portfolio_display at line 44 |
| `the_alchemiser/core/utils/s3_utils.py` | replace_file_handlers_with_s3 at line 204 |
| `the_alchemiser/core/validation/indicator_validator.py` | __init__ at line 32 |
| `the_alchemiser/execution/account_service.py` | get_positions at line 10 |
| `the_alchemiser/execution/alpaca_client.py` | __init__ at line 81 |
| `the_alchemiser/execution/execution_manager.py` | __init__ at line 10 |
| `the_alchemiser/execution/portfolio_rebalancer.py` | __init__ at line 17 |
| `the_alchemiser/execution/reporting.py` | create_execution_summary at line 7 |
| `the_alchemiser/execution/smart_execution.py` | place_market_order at line 30 |
| `the_alchemiser/execution/trading_engine.py` | main at line 812 |
| `the_alchemiser/lambda_handler.py` | lambda_handler at line 84 |
| `the_alchemiser/main.py` | configure_application_logging at line 47 |
| `the_alchemiser/tracking/integration.py` | strategy_execution_context at line 69 |
| `the_alchemiser/tracking/strategy_order_tracker.py` | get_strategy_tracker at line 559 |
| `the_alchemiser/utils/account_utils.py` | extract_comprehensive_account_data at line 13 |
| `the_alchemiser/utils/asset_info.py` | __init__ at line 40 |
| `the_alchemiser/utils/asset_order_handler.py` | __init__ at line 24 |
| `the_alchemiser/utils/config_utils.py` | load_alert_config at line 12 |
| `the_alchemiser/utils/indicator_utils.py` | safe_get_indicator at line 12 |
| `the_alchemiser/utils/limit_order_handler.py` | __init__ at line 24 |
| `the_alchemiser/utils/market_timing_utils.py` | __init__ at line 24 |
| `the_alchemiser/utils/position_manager.py` | __init__ at line 18 |
| `the_alchemiser/utils/price_fetching_utils.py` | subscribe_for_real_time at line 16 |
| `the_alchemiser/utils/price_utils.py` | ensure_scalar_price at line 10 |
| `the_alchemiser/utils/progressive_order_utils.py` | __str__ at line 26 |
| `the_alchemiser/utils/signal_display_utils.py` | display_signal_results at line 12 |
| `the_alchemiser/utils/smart_pricing_handler.py` | __init__ at line 19 |
| `the_alchemiser/utils/spread_assessment.py` | __init__ at line 39 |
| `the_alchemiser/utils/symbol_lookback_calculator.py` | main at line 372 |
| `the_alchemiser/utils/websocket_connection_manager.py` | __init__ at line 24 |
| `the_alchemiser/utils/websocket_order_monitor.py` | __init__ at line 23 |
## General Recommendations

- Add explicit type annotations for all function parameters and return values.
- Replace dynamic patterns with Protocols or generics where appropriate.
- Use `typing` features such as `TypedDict`, `Protocol`, and `Final` for better precision.
- Enable `from __future__ import annotations` to postpone evaluation of type hints.
- Consider adopting additional static analysis tools like Pyright or Pylance for IDE feedback.

Example fix:
```python
# Before
def process(data):
    return data[0]

# After
from typing import Sequence, Any

def process(data: Sequence[Any]) -> Any:
    return data[0]
```
