"""Business Unit: backtest | Status: current.

HTML report generation for backtest results.

Generates self-contained HTML reports with embedded charts and tables.
Supports both single BacktestResult and PortfolioBacktestResult.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from the_alchemiser.backtest_v2.reporting.charts import (
    create_drawdown_chart,
    create_equity_chart,
    create_monthly_returns_heatmap,
    create_rolling_sharpe_chart,
    create_trade_distribution_chart,
)

if TYPE_CHECKING:
    from the_alchemiser.backtest_v2.core.portfolio_engine import PortfolioBacktestResult
    from the_alchemiser.backtest_v2.core.result import BacktestResult

    AnyBacktestResult = BacktestResult | PortfolioBacktestResult


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Report - {strategy_name}</title>
    <style>
        :root {{
            --primary-color: #2E86AB;
            --success-color: #27AE60;
            --danger-color: #E74C3C;
            --warning-color: #F39C12;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #333333;
            --border-color: #e0e0e0;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 3px solid var(--primary-color);
            margin-bottom: 30px;
        }}
        header h1 {{
            color: var(--primary-color);
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        header .subtitle {{
            color: #666;
            font-size: 1.1rem;
        }}
        .card {{
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            padding: 25px;
            margin-bottom: 25px;
        }}
        .card h2 {{
            color: var(--primary-color);
            font-size: 1.4rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border-color);
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        .metric {{
            background: var(--bg-color);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric .label {{
            font-size: 0.85rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .metric .value {{
            font-size: 1.8rem;
            font-weight: 700;
        }}
        .metric .value.positive {{
            color: var(--success-color);
        }}
        .metric .value.negative {{
            color: var(--danger-color);
        }}
        .metric .value.neutral {{
            color: var(--primary-color);
        }}
        .chart-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            background: var(--bg-color);
            font-weight: 600;
            color: var(--primary-color);
        }}
        tr:hover {{
            background: var(--bg-color);
        }}
        .config-table td:first-child {{
            font-weight: 600;
            width: 200px;
        }}
        .comparison-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .comparison-row .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            text-align: left;
        }}
        .comparison-row .metric .label {{
            margin-bottom: 0;
        }}
        footer {{
            text-align: center;
            padding: 30px 0;
            color: #666;
            font-size: 0.9rem;
            border-top: 1px solid var(--border-color);
            margin-top: 30px;
        }}
        .trades-table {{
            max-height: 400px;
            overflow-y: auto;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .badge-buy {{
            background: rgba(39, 174, 96, 0.15);
            color: var(--success-color);
        }}
        .badge-sell {{
            background: rgba(231, 76, 60, 0.15);
            color: var(--danger-color);
        }}
        @media print {{
            body {{
                padding: 0;
            }}
            .card {{
                box-shadow: none;
                border: 1px solid var(--border-color);
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Backtest Report</h1>
            <p class="subtitle">{strategy_name} | {start_date} to {end_date}</p>
        </header>

        <!-- Configuration -->
        <div class="card">
            <h2>📋 Configuration</h2>
            <table class="config-table">
                <tr><td>Strategy</td><td>{strategy_path}</td></tr>
                <tr><td>Period</td><td>{start_date} to {end_date}</td></tr>
                <tr><td>Initial Capital</td><td>${initial_capital:,.2f}</td></tr>
                <tr><td>Trading Days</td><td>{trading_days}</td></tr>
                <tr><td>Total Trades</td><td>{total_trades}</td></tr>
                <tr><td>Slippage</td><td>{slippage_bps} bps</td></tr>
            </table>
        </div>

        <!-- Key Metrics -->
        <div class="card">
            <h2>📈 Performance Summary</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="label">Total Return</div>
                    <div class="value {return_class}">{total_return}</div>
                </div>
                <div class="metric">
                    <div class="label">CAGR</div>
                    <div class="value {cagr_class}">{cagr}</div>
                </div>
                <div class="metric">
                    <div class="label">Sharpe Ratio</div>
                    <div class="value {sharpe_class}">{sharpe_ratio}</div>
                </div>
                <div class="metric">
                    <div class="label">Sortino Ratio</div>
                    <div class="value {sortino_class}">{sortino_ratio}</div>
                </div>
                <div class="metric">
                    <div class="label">Max Drawdown</div>
                    <div class="value negative">{max_drawdown}</div>
                </div>
                <div class="metric">
                    <div class="label">Max DD Duration</div>
                    <div class="value neutral">{max_dd_duration} days</div>
                </div>
                <div class="metric">
                    <div class="label">Volatility (Ann.)</div>
                    <div class="value neutral">{volatility}</div>
                </div>
                <div class="metric">
                    <div class="label">Calmar Ratio</div>
                    <div class="value {calmar_class}">{calmar_ratio}</div>
                </div>
            </div>
        </div>

        <!-- Trading Statistics -->
        <div class="card">
            <h2>💹 Trading Statistics</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="label">Total Trades</div>
                    <div class="value neutral">{total_trades}</div>
                </div>
                <div class="metric">
                    <div class="label">Win Rate</div>
                    <div class="value {winrate_class}">{win_rate}</div>
                </div>
                <div class="metric">
                    <div class="label">Profit Factor</div>
                    <div class="value {pf_class}">{profit_factor}</div>
                </div>
                <div class="metric">
                    <div class="label">Alpha vs SPY</div>
                    <div class="value {alpha_class}">{alpha}</div>
                </div>
            </div>
        </div>

        <!-- Benchmark Comparison -->
        <div class="card">
            <h2>🎯 Benchmark Comparison (SPY)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Strategy</th>
                        <th>Benchmark (SPY)</th>
                        <th>Difference</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Total Return</td>
                        <td>{total_return}</td>
                        <td>{bench_return}</td>
                        <td class="{alpha_class}">{alpha}</td>
                    </tr>
                    <tr>
                        <td>CAGR</td>
                        <td>{cagr}</td>
                        <td>{bench_cagr}</td>
                        <td>-</td>
                    </tr>
                    <tr>
                        <td>Sharpe Ratio</td>
                        <td>{sharpe_ratio}</td>
                        <td>{bench_sharpe}</td>
                        <td>-</td>
                    </tr>
                    <tr>
                        <td>Max Drawdown</td>
                        <td>{max_drawdown}</td>
                        <td>{bench_max_dd}</td>
                        <td>-</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Equity Curve Chart -->
        <div class="card">
            <h2>📉 Equity Curve</h2>
            <div class="chart-container">
                <img src="data:image/png;base64,{equity_chart}" alt="Equity Curve">
            </div>
        </div>

        <!-- Drawdown Chart -->
        <div class="card">
            <h2>📉 Drawdown</h2>
            <div class="chart-container">
                <img src="data:image/png;base64,{drawdown_chart}" alt="Drawdown">
            </div>
        </div>

        <!-- Monthly Returns Heatmap -->
        <div class="card">
            <h2>📅 Monthly Returns</h2>
            <div class="chart-container">
                <img src="data:image/png;base64,{monthly_chart}" alt="Monthly Returns Heatmap">
            </div>
        </div>

        <!-- Rolling Sharpe -->
        <div class="card">
            <h2>📊 Rolling Sharpe Ratio</h2>
            <div class="chart-container">
                <img src="data:image/png;base64,{rolling_sharpe_chart}" alt="Rolling Sharpe">
            </div>
        </div>

        <!-- Trade Distribution -->
        <div class="card">
            <h2>📊 Trade Distribution</h2>
            <div class="chart-container">
                <img src="data:image/png;base64,{trade_dist_chart}" alt="Trade Distribution">
            </div>
        </div>

        <!-- Recent Trades Table -->
        <div class="card">
            <h2>📝 Recent Trades (Last 50)</h2>
            <div class="trades-table">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Symbol</th>
                            <th>Action</th>
                            <th>Shares</th>
                            <th>Price</th>
                            <th>Value</th>
                            <th>Commission</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trades_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Errors if any -->
        {errors_section}

        <footer>
            <p>Generated by The Alchemiser Backtest Engine | {generated_at}</p>
        </footer>
    </div>
</body>
</html>
"""


def _value_class(value: float, thresholds: tuple[float, float] = (0, 0)) -> str:
    """Determine CSS class based on value.

    Args:
        value: The value to classify
        thresholds: (negative_threshold, positive_threshold)

    Returns:
        CSS class name: 'positive', 'negative', or 'neutral'

    """
    neg_thresh, pos_thresh = thresholds
    if value > pos_thresh:
        return "positive"
    if value < neg_thresh:
        return "negative"
    return "neutral"


def _format_pct(value: float) -> str:
    """Format a decimal as percentage string."""
    return f"{value * 100:+.2f}%"


def _format_ratio(value: float) -> str:
    """Format a ratio."""
    if value >= 999:
        return "∞"
    return f"{value:.2f}"


def generate_html_report(
    result: BacktestResult,
    output_path: Path | str | None = None,
) -> str:
    """Generate HTML report from backtest results.

    Args:
        result: Backtest result object
        output_path: Optional path to save the HTML file

    Returns:
        HTML string

    """
    # Generate all charts
    equity_chart = create_equity_chart(result, as_base64=True)
    drawdown_chart = create_drawdown_chart(result, as_base64=True)
    monthly_chart = create_monthly_returns_heatmap(result, as_base64=True)
    rolling_sharpe_chart = create_rolling_sharpe_chart(result, as_base64=True)
    trade_dist_chart = create_trade_distribution_chart(result, as_base64=True)

    # Extract config values
    config = result.config_summary
    strategy_path = str(config.get("strategy_path", "N/A"))
    strategy_name = Path(strategy_path).stem if strategy_path != "N/A" else "Backtest"

    # Format metrics
    total_return = float(result.metrics.total_return)
    cagr = float(result.metrics.cagr)
    sharpe = result.metrics.sharpe_ratio
    sortino = result.metrics.sortino_ratio
    max_dd = float(result.metrics.max_drawdown)
    volatility = float(result.metrics.volatility)
    calmar = result.metrics.calmar_ratio
    win_rate = result.metrics.win_rate
    profit_factor = result.metrics.profit_factor
    alpha = result.alpha

    # Benchmark metrics
    bench_return = float(result.benchmark_metrics.total_return)
    bench_cagr = float(result.benchmark_metrics.cagr)
    bench_sharpe = result.benchmark_metrics.sharpe_ratio
    bench_max_dd = float(result.benchmark_metrics.max_drawdown)

    # Generate trades table rows
    trades_rows = []
    recent_trades = result.trades[-50:] if result.trades else []
    for trade in reversed(recent_trades):
        badge_class = "badge-buy" if trade.action == "BUY" else "badge-sell"
        row = f"""<tr>
            <td>{trade.date.strftime("%Y-%m-%d")}</td>
            <td>{trade.symbol}</td>
            <td><span class="badge {badge_class}">{trade.action}</span></td>
            <td>{trade.shares:,.0f}</td>
            <td>${float(trade.price):,.2f}</td>
            <td>${float(trade.value):,.2f}</td>
            <td>${float(trade.commission):,.2f}</td>
        </tr>"""
        trades_rows.append(row)

    trades_html = (
        "\n".join(trades_rows)
        if trades_rows
        else "<tr><td colspan='7'>No trades executed</td></tr>"
    )

    # Generate errors section if any
    errors_section = ""
    if result.errors:
        error_rows = []
        for err in result.errors[:20]:  # Show first 20
            row = (
                f"<tr><td>{err.get('date', 'N/A')}</td><td>{err.get('error', 'Unknown')}</td></tr>"
            )
            error_rows.append(row)
        errors_html = "\n".join(error_rows)
        errors_section = f"""
        <div class="card">
            <h2>⚠️ Errors ({len(result.errors)} total)</h2>
            <table>
                <thead><tr><th>Date</th><th>Error</th></tr></thead>
                <tbody>{errors_html}</tbody>
            </table>
        </div>
        """

    # Format the HTML
    html = HTML_TEMPLATE.format(
        strategy_name=strategy_name,
        strategy_path=strategy_path,
        start_date=config.get("start_date", "N/A"),
        end_date=config.get("end_date", "N/A"),
        initial_capital=float(str(config.get("initial_capital", 0))),
        trading_days=config.get("trading_days", 0),
        total_trades=config.get("total_trades", 0),
        slippage_bps=float(str(config.get("slippage_bps", 0))),
        # Metrics
        total_return=_format_pct(total_return),
        return_class=_value_class(total_return),
        cagr=_format_pct(cagr),
        cagr_class=_value_class(cagr),
        sharpe_ratio=_format_ratio(sharpe),
        sharpe_class=_value_class(sharpe, (-0.5, 1.0)),
        sortino_ratio=_format_ratio(sortino),
        sortino_class=_value_class(sortino, (-0.5, 1.0)),
        max_drawdown=_format_pct(-max_dd),
        max_dd_duration=result.metrics.max_drawdown_duration_days,
        volatility=_format_pct(volatility),
        calmar_ratio=_format_ratio(calmar),
        calmar_class=_value_class(calmar, (0, 1.0)),
        win_rate=_format_pct(win_rate),
        winrate_class=_value_class(win_rate, (0.4, 0.5)),
        profit_factor=_format_ratio(profit_factor),
        pf_class=_value_class(profit_factor, (0.8, 1.0)),
        alpha=_format_pct(alpha),
        alpha_class=_value_class(alpha),
        # Benchmark
        bench_return=_format_pct(bench_return),
        bench_cagr=_format_pct(bench_cagr),
        bench_sharpe=_format_ratio(bench_sharpe),
        bench_max_dd=_format_pct(-bench_max_dd),
        # Charts (base64)
        equity_chart=equity_chart,
        drawdown_chart=drawdown_chart,
        monthly_chart=monthly_chart,
        rolling_sharpe_chart=rolling_sharpe_chart,
        trade_dist_chart=trade_dist_chart,
        # Trades
        trades_rows=trades_html,
        # Errors
        errors_section=errors_section,
        # Footer
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )

    # Save if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

    return html


# Portfolio HTML Template
PORTFOLIO_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Backtest Report</title>
    <style>
        :root {{
            --primary-color: #2E86AB;
            --success-color: #27AE60;
            --danger-color: #E74C3C;
            --warning-color: #F39C12;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #333333;
            --border-color: #e0e0e0;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 3px solid var(--primary-color);
            margin-bottom: 30px;
        }}
        header h1 {{ color: var(--primary-color); font-size: 2.5rem; margin-bottom: 10px; }}
        header .subtitle {{ color: #666; font-size: 1.1rem; }}
        .card {{
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            padding: 25px;
            margin-bottom: 25px;
        }}
        .card h2 {{
            color: var(--primary-color);
            font-size: 1.4rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border-color);
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        .metric {{
            background: var(--bg-color);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric .label {{
            font-size: 0.85rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .metric .value {{ font-size: 1.8rem; font-weight: 700; }}
        .metric .value.positive {{ color: var(--success-color); }}
        .metric .value.negative {{ color: var(--danger-color); }}
        .metric .value.neutral {{ color: var(--primary-color); }}
        .chart-container {{ text-align: center; margin: 20px 0; }}
        .chart-container img {{ max-width: 100%; height: auto; border-radius: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid var(--border-color); }}
        th {{ background: var(--bg-color); font-weight: 600; color: var(--primary-color); }}
        tr:hover {{ background: var(--bg-color); }}
        footer {{
            text-align: center;
            padding: 30px 0;
            color: #666;
            font-size: 0.9rem;
            border-top: 1px solid var(--border-color);
            margin-top: 30px;
        }}
        .strategy-row {{ display: flex; align-items: center; }}
        .strategy-bar {{
            height: 8px;
            border-radius: 4px;
            margin-left: 10px;
        }}
        .bar-positive {{ background: var(--success-color); }}
        .bar-negative {{ background: var(--danger-color); }}
        @media print {{
            body {{ padding: 0; }}
            .card {{ box-shadow: none; border: 1px solid var(--border-color); page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Portfolio Backtest Report</h1>
            <p class="subtitle">{num_strategies} Strategies | {start_date} to {end_date}</p>
        </header>

        <!-- Configuration -->
        <div class="card">
            <h2>📋 Configuration</h2>
            <table>
                <tr><td style="font-weight:600;width:200px;">Strategies</td><td>{num_strategies}</td></tr>
                <tr><td style="font-weight:600;">Period</td><td>{start_date} to {end_date}</td></tr>
                <tr><td style="font-weight:600;">Initial Capital</td><td>${initial_capital:,.2f}</td></tr>
            </table>
        </div>

        <!-- Portfolio Metrics -->
        <div class="card">
            <h2>📈 Portfolio Performance</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="label">Total Return</div>
                    <div class="value {return_class}">{total_return}</div>
                </div>
                <div class="metric">
                    <div class="label">CAGR</div>
                    <div class="value {cagr_class}">{cagr}</div>
                </div>
                <div class="metric">
                    <div class="label">Sharpe Ratio</div>
                    <div class="value {sharpe_class}">{sharpe_ratio}</div>
                </div>
                <div class="metric">
                    <div class="label">Sortino Ratio</div>
                    <div class="value {sortino_class}">{sortino_ratio}</div>
                </div>
                <div class="metric">
                    <div class="label">Max Drawdown</div>
                    <div class="value negative">{max_drawdown}</div>
                </div>
                <div class="metric">
                    <div class="label">Max DD Duration</div>
                    <div class="value neutral">{max_dd_duration} days</div>
                </div>
                <div class="metric">
                    <div class="label">Volatility (Ann.)</div>
                    <div class="value neutral">{volatility}</div>
                </div>
                <div class="metric">
                    <div class="label">Alpha vs SPY</div>
                    <div class="value {alpha_class}">{alpha}</div>
                </div>
            </div>
        </div>

        <!-- Benchmark Comparison -->
        <div class="card">
            <h2>🎯 Benchmark Comparison (SPY)</h2>
            <table>
                <thead>
                    <tr><th>Metric</th><th>Portfolio</th><th>Benchmark (SPY)</th></tr>
                </thead>
                <tbody>
                    <tr><td>Total Return</td><td>{total_return}</td><td>{bench_return}</td></tr>
                    <tr><td>Sharpe Ratio</td><td>{sharpe_ratio}</td><td>{bench_sharpe}</td></tr>
                    <tr><td>Max Drawdown</td><td>{max_drawdown}</td><td>{bench_max_dd}</td></tr>
                </tbody>
            </table>
        </div>

        <!-- Equity Curve Chart -->
        <div class="card">
            <h2>📉 Equity Curve</h2>
            <div class="chart-container">
                <img src="data:image/png;base64,{equity_chart}" alt="Equity Curve">
            </div>
        </div>

        <!-- Drawdown Chart -->
        <div class="card">
            <h2>📉 Drawdown</h2>
            <div class="chart-container">
                <img src="data:image/png;base64,{drawdown_chart}" alt="Drawdown">
            </div>
        </div>

        <!-- Strategy Breakdown -->
        <div class="card">
            <h2>📋 Strategy Breakdown</h2>
            <table>
                <thead>
                    <tr>
                        <th>Strategy</th>
                        <th>Weight</th>
                        <th>Return</th>
                        <th>Sharpe</th>
                        <th>Trades</th>
                        <th>Errors</th>
                    </tr>
                </thead>
                <tbody>
                    {strategy_rows}
                </tbody>
            </table>
        </div>

        <!-- Errors if any -->
        {errors_section}

        <footer>
            <p>Generated by The Alchemiser Backtest Engine | {generated_at}</p>
        </footer>
    </div>
</body>
</html>
"""


def generate_portfolio_html_report(
    result: PortfolioBacktestResult,
    output_path: Path | str | None = None,
) -> str:
    """Generate HTML report from portfolio backtest results.

    Args:
        result: Portfolio backtest result object
        output_path: Optional path to save the HTML file

    Returns:
        HTML string

    """
    # Create a pseudo-BacktestResult for chart generation
    from the_alchemiser.backtest_v2.core.result import BacktestResult

    pseudo_result = BacktestResult(
        config_summary=result.config_summary,
        equity_curve=result.equity_curve,
        benchmark_curve=result.benchmark_curve,
        trades=[],  # No trades at portfolio level
        allocation_history={},
        metrics=result.metrics,
        strategy_metrics=result.metrics,  # Use same metrics for portfolio
        benchmark_metrics=result.benchmark_metrics,
        errors=result.errors,
    )

    # Generate charts
    equity_chart = create_equity_chart(pseudo_result, as_base64=True)
    drawdown_chart = create_drawdown_chart(pseudo_result, as_base64=True)

    # Extract config values
    config = result.config_summary
    num_strategies = len(result.strategy_results)

    # Format metrics
    total_return = float(result.metrics.total_return)
    cagr = float(result.metrics.cagr)
    sharpe = result.metrics.sharpe_ratio
    sortino = result.metrics.sortino_ratio
    max_dd = float(result.metrics.max_drawdown)
    volatility = float(result.metrics.volatility)
    alpha = result.alpha

    # Benchmark metrics
    bench_return = float(result.benchmark_metrics.total_return)
    bench_sharpe = result.benchmark_metrics.sharpe_ratio
    bench_max_dd = float(result.benchmark_metrics.max_drawdown)

    # Generate strategy breakdown rows
    strategy_rows = []
    for sr in result.strategy_results:
        ret = float(sr.result.metrics.total_return) * 100
        ret_class = "positive" if ret > 0 else "negative"
        row = f"""<tr>
            <td>{sr.name}</td>
            <td>{float(sr.weight) * 100:.1f}%</td>
            <td class="{ret_class}">{ret:+.2f}%</td>
            <td>{sr.result.metrics.sharpe_ratio:.2f}</td>
            <td>{sr.result.metrics.total_trades}</td>
            <td>{len(sr.result.errors)}</td>
        </tr>"""
        strategy_rows.append(row)
    strategy_html = "\n".join(strategy_rows)

    # Generate errors section if any
    errors_section = ""
    if result.errors:
        error_rows = []
        for err in result.errors[:20]:
            row = (
                f"<tr><td>{err.get('date', 'N/A')}</td><td>{err.get('error', 'Unknown')}</td></tr>"
            )
            error_rows.append(row)
        errors_html = "\n".join(error_rows)
        errors_section = f"""
        <div class="card">
            <h2>⚠️ Errors ({len(result.errors)} total)</h2>
            <table>
                <thead><tr><th>Date</th><th>Error</th></tr></thead>
                <tbody>{errors_html}</tbody>
            </table>
        </div>
        """

    # Format the HTML
    html = PORTFOLIO_HTML_TEMPLATE.format(
        num_strategies=num_strategies,
        start_date=config.get("start_date", "N/A"),
        end_date=config.get("end_date", "N/A"),
        initial_capital=float(str(config.get("initial_capital", 0))),
        total_return=_format_pct(total_return),
        return_class=_value_class(total_return),
        cagr=_format_pct(cagr),
        cagr_class=_value_class(cagr),
        sharpe_ratio=_format_ratio(sharpe),
        sharpe_class=_value_class(sharpe, (-0.5, 1.0)),
        sortino_ratio=_format_ratio(sortino),
        sortino_class=_value_class(sortino, (-0.5, 1.0)),
        max_drawdown=_format_pct(-max_dd),
        max_dd_duration=result.metrics.max_drawdown_duration_days,
        volatility=_format_pct(volatility),
        alpha=_format_pct(alpha),
        alpha_class=_value_class(alpha),
        bench_return=_format_pct(bench_return),
        bench_sharpe=_format_ratio(bench_sharpe),
        bench_max_dd=_format_pct(-bench_max_dd),
        equity_chart=equity_chart,
        drawdown_chart=drawdown_chart,
        strategy_rows=strategy_html,
        errors_section=errors_section,
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )

    # Save if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

    return html


def generate_report(
    result: AnyBacktestResult,
    output_path: Path | str | None = None,
) -> str:
    """Generate HTML report, auto-detecting result type.

    Args:
        result: Either BacktestResult or PortfolioBacktestResult
        output_path: Optional path to save the HTML file

    Returns:
        HTML string

    """
    # Check if this is a portfolio result by looking for strategy_results attribute
    if hasattr(result, "strategy_results"):
        return generate_portfolio_html_report(result, output_path)  # type: ignore[arg-type]
    return generate_html_report(result, output_path)
