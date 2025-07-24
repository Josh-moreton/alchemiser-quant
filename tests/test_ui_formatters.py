from the_alchemiser.core.ui.cli_formatter import render_technical_indicators
from the_alchemiser.core.ui.telegram_formatter import build_multi_strategy_message
from types import SimpleNamespace


def test_render_technical_indicators_basic():
    data = {
        'NUCLEAR': {
            'indicators': {
                'SPY': {'current_price': 100, 'rsi_10': 60, 'ma_200': 90},
                'TQQQ': {'current_price': 50, 'rsi_10': 40, 'ma_200': 55},
            }
        }
    }
    output = render_technical_indicators(data)
    assert "SPY" in output
    assert "TQQQ" in output


def test_build_multi_strategy_message_basic():
    result = SimpleNamespace(
        success=True,
        consolidated_portfolio={'SPY': 0.6, 'BIL': 0.4},
        execution_summary={
            'strategy_summary': {
                'NUCLEAR': {'allocation': 0.5, 'signal': 'BUY SPY'},
                'TECL': {'allocation': 0.5, 'signal': 'BUY TECL'},
            },
            'trading_summary': {
                'total_trades': 1,
                'total_buy_value': 1000,
                'total_sell_value': 0,
            },
        },
    )
    message = build_multi_strategy_message(result, "PAPER")
    assert "PAPER MULTI-STRATEGY EXECUTION" in message
    assert "SPY" in message
