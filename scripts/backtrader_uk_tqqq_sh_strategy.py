#!/usr/bin/env python3
"""Business Unit: backtest | Status: current.

Backtrader script for "TQQQ or SH KMLM Phenomenon" strategy with UK tickers.

This script implements the TQQQ/SH switching strategy adapted for UK markets:
- TQQQ (US 3x leveraged NASDAQ) → LQQ3 (UK 3x leveraged NASDAQ)
- SH (US -1x S&P500) → XSPS (UK -1x S&P500)

Strategy Logic:
The strategy uses RSI indicators to make daily rebalancing decisions:
1. If RSI(IEF, 20) > RSI(PSQ, 20):
   a. If RSI(XLK, 10) > RSI(KMLM, 10): Hold LQQ3
   b. Else: Hold XSPS
2. Else:
   a. If RSI(LQQ3, 10) < 31: Hold LQQ3
   b. Else: Hold XSPS

Usage:
    # Default run (last 365 days)
    python scripts/backtrader_uk_tqqq_sh_strategy.py

    # Custom date range
    python scripts/backtrader_uk_tqqq_sh_strategy.py --start 2020-01-01 --end 2023-12-31

    # Custom capital
    python scripts/backtrader_uk_tqqq_sh_strategy.py --capital 100000

    # Generate plot
    python scripts/backtrader_uk_tqqq_sh_strategy.py --plot

    # Verbose output
    python scripts/backtrader_uk_tqqq_sh_strategy.py --verbose
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import backtrader as bt

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TQQQSHKMLMStrategy(bt.Strategy):
    """TQQQ/SH KMLM Phenomenon Strategy adapted for UK markets (LQQ3/XSPS).

    This strategy switches between leveraged long (LQQ3) and short (XSPS) positions
    based on RSI comparisons across multiple timeframes and instruments.
    """

    params = (
        ("rsi_ief_psg_window", 20),  # RSI window for IEF/PSQ comparison
        ("rsi_main_window", 10),  # RSI window for main comparisons
        ("rsi_oversold", 31),  # Oversold threshold for LQQ3 RSI
        ("verbose", False),  # Enable verbose logging
    )

    def __init__(self) -> None:
        """Initialize strategy with RSI indicators for all required instruments."""
        # Track data feeds by name for easy access
        self.data_by_name: dict[str, bt.feeds.DataBase] = {}
        for data in self.datas:
            name = data._name
            self.data_by_name[name] = data

        # Verify required data feeds
        required = ["IEF", "PSQ", "XLK", "KMLM", "LQQ3", "XSPS", "DBMF"]
        missing = [name for name in required if name not in self.data_by_name]
        if missing:
            raise ValueError(f"Missing required data feeds: {missing}")

        # Initialize RSI indicators
        self.rsi_ief = bt.indicators.RSI(
            self.data_by_name["IEF"].close,
            period=self.params.rsi_ief_psg_window,
        )
        self.rsi_psq = bt.indicators.RSI(
            self.data_by_name["PSQ"].close,
            period=self.params.rsi_ief_psg_window,
        )
        self.rsi_xlk = bt.indicators.RSI(
            self.data_by_name["XLK"].close,
            period=self.params.rsi_main_window,
        )
        self.rsi_kmlm = bt.indicators.RSI(
            self.data_by_name["KMLM"].close,
            period=self.params.rsi_main_window,
        )
        self.rsi_lqq3 = bt.indicators.RSI(
            self.data_by_name["LQQ3"].close,
            period=self.params.rsi_main_window,
        )
        self.rsi_dbmf = bt.indicators.RSI(
            self.data_by_name["DBMF"].close,
            period=self.params.rsi_main_window,
        )

        # Track current position
        self.current_position: str | None = None
        self.order = None

    def log(self, txt: str, dt: datetime | None = None) -> None:
        """Log messages with timestamp.

        Args:
            txt: Message to log
            dt: Optional datetime (uses current bar datetime if not provided)

        """
        if self.params.verbose:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()}: {txt}")

    def notify_order(self, order: bt.Order) -> None:
        """Track order status.

        Args:
            order: Order being tracked

        """
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY EXECUTED, Price: {order.executed.price:.2f}, "
                    f"Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}",
                )
            elif order.issell():
                self.log(
                    f"SELL EXECUTED, Price: {order.executed.price:.2f}, "
                    f"Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}",
                )
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"Order Canceled/Margin/Rejected: {order.status}")

        self.order = None

    def next(self) -> None:
        """Execute strategy logic on each bar."""
        # Skip if we have pending orders
        if self.order:
            return

        # Get current RSI values
        rsi_ief = self.rsi_ief[0]
        rsi_psq = self.rsi_psq[0]
        rsi_xlk = self.rsi_xlk[0]
        rsi_kmlm = self.rsi_kmlm[0]
        rsi_lqq3 = self.rsi_lqq3[0]
        rsi_dbmf = self.rsi_dbmf[0]

        # Determine target position based on strategy logic
        target_position = self._determine_target_position(
            rsi_ief, rsi_psq, rsi_xlk, rsi_kmlm, rsi_lqq3, rsi_dbmf
        )

        # Log decision
        self.log(
            f"RSI Values - IEF: {rsi_ief:.2f}, PSQ: {rsi_psq:.2f}, "
            f"XLK: {rsi_xlk:.2f}, KMLM: {rsi_kmlm:.2f}, LQQ3: {rsi_lqq3:.2f}, "
            f"DBMF: {rsi_dbmf:.2f} | Target: {target_position}",
        )

        # Rebalance if needed
        if target_position != self.current_position:
            self._rebalance_to(target_position)
            self.current_position = target_position

    def _determine_target_position(
        self,
        rsi_ief: float,
        rsi_psq: float,
        rsi_xlk: float,
        rsi_kmlm: float,
        rsi_lqq3: float,
        rsi_dbmf: float,
    ) -> str:
        """Determine target position based on RSI values.

        Args:
            rsi_ief: RSI of IEF (20-day window)
            rsi_psq: RSI of PSQ (20-day window)
            rsi_xlk: RSI of XLK (10-day window)
            rsi_kmlm: RSI of KMLM (10-day window)
            rsi_lqq3: RSI of LQQ3 (10-day window)
            rsi_dbmf: RSI of DBMF (10-day window) - not used in this logic but kept for reference

        Returns:
            Target position: "LQQ3" or "XSPS"

        """
        # Main decision tree
        if rsi_ief > rsi_psq:
            # IEF RSI > PSQ RSI branch
            if rsi_xlk > rsi_kmlm:
                # XLK RSI > KMLM RSI: Hold LQQ3
                return "LQQ3"
            else:
                # XLK RSI <= KMLM RSI: Hold XSPS
                # (DBMF comparison in original DSL always results in XSPS in this branch)
                return "XSPS"
        else:
            # IEF RSI <= PSQ RSI branch
            if rsi_lqq3 < self.params.rsi_oversold:
                # LQQ3 is oversold: Hold LQQ3
                return "LQQ3"
            else:
                # LQQ3 not oversold: Hold XSPS
                # (DBMF comparison in original DSL always results in XSPS in this branch)
                return "XSPS"

    def _rebalance_to(self, target: str) -> None:
        """Rebalance portfolio to target position.

        Args:
            target: Target ticker symbol ("LQQ3" or "XSPS")

        """
        lqq3_data = self.data_by_name["LQQ3"]
        xsps_data = self.data_by_name["XSPS"]

        # Close all positions first
        lqq3_size = self.getposition(lqq3_data).size
        xsps_size = self.getposition(xsps_data).size

        if lqq3_size != 0:
            self.log(f"Closing LQQ3 position (size: {lqq3_size})")
            self.order = self.close(data=lqq3_data)

        if xsps_size != 0:
            self.log(f"Closing XSPS position (size: {xsps_size})")
            self.order = self.close(data=xsps_data)

        # Open new position with 100% of capital
        if target == "LQQ3":
            self.log(f"Opening LQQ3 position (100% of portfolio)")
            self.order = self.order_target_percent(data=lqq3_data, target=1.0)
        elif target == "XSPS":
            self.log(f"Opening XSPS position (100% of portfolio)")
            self.order = self.order_target_percent(data=xsps_data, target=1.0)


def load_data_feed(
    ticker: str,
    fromdate: datetime,
    todate: datetime,
    data_dir: Path,
) -> bt.feeds.PandasData | None:
    """Load data feed for a ticker from local Parquet file.

    Args:
        ticker: Ticker symbol
        fromdate: Start date
        todate: End date
        data_dir: Directory containing Parquet files

    Returns:
        PandasData feed or None if file not found

    """
    try:
        import pandas as pd
    except ImportError:
        print("Error: pandas is required for loading data", file=sys.stderr)
        sys.exit(1)

    file_path = data_dir / f"{ticker}.parquet"
    if not file_path.exists():
        print(f"Warning: Data file not found for {ticker}: {file_path}", file=sys.stderr)
        return None

    # Load parquet file
    df = pd.read_parquet(file_path)

    # Ensure datetime index
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
    elif not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # Filter to date range
    df = df[(df.index >= fromdate) & (df.index <= todate)]

    if df.empty:
        print(f"Warning: No data for {ticker} in date range", file=sys.stderr)
        return None

    # Ensure required columns exist
    required_cols = ["open", "high", "low", "close", "volume"]
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Missing required column '{col}' for {ticker}", file=sys.stderr)
            return None

    # Create backtrader data feed
    data = bt.feeds.PandasData(
        dataname=df,
        datetime=None,  # Use index
        open="open",
        high="high",
        low="low",
        close="close",
        volume="volume",
        openinterest=-1,  # Not used
        fromdate=fromdate,
        todate=todate,
    )
    data._name = ticker  # Store ticker name for reference

    return data


def main() -> int:
    """Run backtrader strategy.

    Returns:
        Exit code (0 for success, 1 for error)

    """
    parser = argparse.ArgumentParser(
        description="Backtest TQQQ/SH KMLM strategy adapted for UK markets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Default run (last 365 days)
    python scripts/backtrader_uk_tqqq_sh_strategy.py

    # Custom date range
    python scripts/backtrader_uk_tqqq_sh_strategy.py --start 2020-01-01 --end 2023-12-31

    # Custom capital
    python scripts/backtrader_uk_tqqq_sh_strategy.py --capital 100000

    # Generate plot
    python scripts/backtrader_uk_tqqq_sh_strategy.py --plot

    # Verbose output
    python scripts/backtrader_uk_tqqq_sh_strategy.py --verbose
        """,
    )

    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start date (YYYY-MM-DD). Default: 365 days ago",
    )

    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End date (YYYY-MM-DD). Default: today",
    )

    parser.add_argument(
        "--capital",
        type=float,
        default=100_000,
        help="Initial capital (default: 100000)",
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/historical",
        help="Path to historical data directory (default: data/historical)",
    )

    parser.add_argument(
        "--commission",
        type=float,
        default=0.001,
        help="Commission rate (default: 0.001 = 0.1%%)",
    )

    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate plot of results",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Parse dates
    if args.start:
        fromdate = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=UTC)
    else:
        fromdate = datetime.now(UTC) - timedelta(days=365)

    if args.end:
        todate = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=UTC)
    else:
        todate = datetime.now(UTC)

    # Validate data directory
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}", file=sys.stderr)
        print("Run 'make backtest' or fetch data first.", file=sys.stderr)
        return 1

    # Initialize backtrader
    cerebro = bt.Cerebro()

    # Add strategy
    cerebro.addstrategy(
        TQQQSHKMLMStrategy,
        verbose=args.verbose,
    )

    # Load data feeds (required symbols for strategy)
    required_tickers = ["IEF", "PSQ", "XLK", "KMLM", "LQQ3", "XSPS", "DBMF"]
    print(f"Loading data for {len(required_tickers)} tickers...")

    for ticker in required_tickers:
        data = load_data_feed(ticker, fromdate, todate, data_dir)
        if data is None:
            print(f"Error: Failed to load data for {ticker}", file=sys.stderr)
            print(
                f"Fetch data first: python scripts/fetch_backtest_data.py --symbols {' '.join(required_tickers)}",
                file=sys.stderr,
            )
            return 1
        cerebro.adddata(data, name=ticker)
        print(f"  ✓ Loaded {ticker}")

    # Set initial capital
    cerebro.broker.setcash(args.capital)

    # Set commission
    cerebro.broker.setcommission(commission=args.commission)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

    # Print starting conditions
    print("=" * 70)
    print("BACKTRADER STRATEGY BACKTEST")
    print("=" * 70)
    print(f"Strategy:        TQQQ/SH KMLM Phenomenon (UK adapted)")
    print(f"Start Date:      {fromdate.date()}")
    print(f"End Date:        {todate.date()}")
    print(f"Initial Capital: ${args.capital:,.2f}")
    print(f"Commission:      {args.commission * 100:.2f}%")
    print(f"Data Directory:  {data_dir}")
    print("=" * 70)
    print(f"Starting Portfolio Value: ${cerebro.broker.getvalue():,.2f}")
    print()

    # Run backtest
    results = cerebro.run()
    strat = results[0]

    # Print results
    print()
    print("=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    print(f"Final Portfolio Value: ${cerebro.broker.getvalue():,.2f}")
    print(
        f"Total Return:          ${cerebro.broker.getvalue() - args.capital:+,.2f} "
        f"({((cerebro.broker.getvalue() - args.capital) / args.capital * 100):+.2f}%)",
    )

    # Analyzer results
    sharpe = strat.analyzers.sharpe.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    returns = strat.analyzers.returns.get_analysis()
    trades = strat.analyzers.trades.get_analysis()

    print()
    print("Performance Metrics:")
    print(f"  Sharpe Ratio:        {sharpe.get('sharperatio', 'N/A')}")
    print(f"  Max Drawdown:        {drawdown.get('max', {}).get('drawdown', 'N/A'):.2f}%")
    print(f"  Total Return:        {returns.get('rtot', 'N/A') * 100:.2f}%")
    print(f"  Average Annual:      {returns.get('rnorm', 'N/A') * 100:.2f}%")

    print()
    print("Trade Statistics:")
    total_trades = trades.get("total", {})
    print(f"  Total Trades:        {total_trades.get('total', 0)}")
    print(f"  Won:                 {total_trades.get('won', 0)}")
    print(f"  Lost:                {total_trades.get('lost', 0)}")

    if total_trades.get("total", 0) > 0:
        win_rate = total_trades.get("won", 0) / total_trades.get("total", 1) * 100
        print(f"  Win Rate:            {win_rate:.2f}%")

    print("=" * 70)

    # Plot if requested
    if args.plot:
        print("\nGenerating plot...")
        cerebro.plot(style="candlestick")

    return 0


if __name__ == "__main__":
    sys.exit(main())
