#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Single-strategy validation against Composer daily-close backtest.

Runs a single .clj strategy for each trading day in a configurable window
(default 5 trading days / 1 week), records outputs (decisions + final signal),
then prompts the user to paste Composer daily-close backtest holdings for each
day so it can compare and produce a match/mismatch report.

Workflow:
    Phase 1 - Run strategy for each day in the window using S3 data lake data
    Phase 2 - Prompt user to paste Composer backtest holdings per day
    Phase 3 - Compare signals and print report
    Phase 4 - Save detailed results to CSV

Usage:
    make validate-strategy s=gold                     # 5 trading days ending yesterday
    make validate-strategy s=gold days=10             # 10 trading days
    make validate-strategy s=gold end=2026-02-07      # Custom end date

    poetry run python scripts/validation/validate_single_strategy.py gold
    poetry run python scripts/validation/validate_single_strategy.py gold.clj --days 10
    poetry run python scripts/validation/validate_single_strategy.py gold --end-date 2026-02-07
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import webbrowser
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

# Set environment variables for S3 market data access and DynamoDB group cache
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("GROUP_HISTORY_TABLE", "alchemiser-dev-group-history")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
STRATEGY_WORKER_PATH = PROJECT_ROOT / "functions" / "strategy_worker"
SHARED_LAYER_PATH = PROJECT_ROOT / "layers" / "shared"
STRATEGIES_PATH = SHARED_LAYER_PATH / "the_alchemiser" / "shared" / "strategies"
LEDGER_PATH = STRATEGIES_PATH / "strategy_ledger.yaml"
VALIDATION_DIR = PROJECT_ROOT / "validation_results"

# Add paths for imports
sys.path.insert(0, str(STRATEGY_WORKER_PATH))
sys.path.insert(0, str(SHARED_LAYER_PATH))

# Match Lambda handler recursion limit for deeply nested DSL strategies.
sys.setrecursionlimit(10000)

# Comparison tolerance (absolute weight difference)
DEFAULT_TOLERANCE = Decimal("0.05")


# ============================================================================
# Date & Trading-Day Helpers
# ============================================================================


def parse_date(date_str: str) -> date:
    """Parse date string to date object.

    Args:
        date_str: Date string like '2026-02-07', 'yesterday', or 'today'.

    Returns:
        Parsed date object.

    """
    lower = date_str.lower()
    if lower == "yesterday":
        return date.today() - timedelta(days=1)
    if lower == "today":
        return date.today()
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def get_trading_days(end_date: date, num_days: int) -> list[date]:
    """Generate a list of *num_days* weekday trading days ending on *end_date*.

    Walks backward from *end_date*, collecting weekdays (Mon-Fri).
    Does not exclude US market holidays -- the market data layer handles
    missing bars gracefully (no bars for holidays).

    Args:
        end_date: The most recent date (inclusive if it is a weekday).
        num_days: Number of trading days to collect.

    Returns:
        List of date objects, oldest-first.

    """
    days: list[date] = []
    current = end_date
    while len(days) < num_days:
        if current.weekday() < 5:  # Monday=0 .. Friday=4
            days.append(current)
        current -= timedelta(days=1)
    days.reverse()
    return days


# ============================================================================
# Strategy Resolution
# ============================================================================


def resolve_strategy_file(strategy_arg: str) -> str:
    """Resolve a strategy argument to the .clj filename.

    Accepts:
        - Strategy name without extension: 'gold'
        - Filename with extension: 'gold.clj'
        - Subfolder path: 'ftlt/tqqq_ftlt.clj'

    Args:
        strategy_arg: User-supplied strategy identifier.

    Returns:
        Resolved .clj filename (relative to STRATEGIES_PATH).

    Raises:
        FileNotFoundError: If no matching strategy file is found.

    """
    # If it already ends with .clj, check directly
    if strategy_arg.endswith(".clj"):
        full_path = STRATEGIES_PATH / strategy_arg
        if full_path.exists():
            return strategy_arg
        raise FileNotFoundError(f"Strategy file not found: {strategy_arg}")

    # Try exact name + .clj
    candidate = f"{strategy_arg}.clj"
    if (STRATEGIES_PATH / candidate).exists():
        return candidate

    # Fuzzy match (glob for *name*.clj anywhere under strategies dir)
    matches = list(STRATEGIES_PATH.rglob(f"*{strategy_arg}*.clj"))
    if len(matches) == 1:
        return str(matches[0].relative_to(STRATEGIES_PATH))
    if len(matches) > 1:
        names = [str(m.relative_to(STRATEGIES_PATH)) for m in matches]
        raise FileNotFoundError(
            f"Ambiguous strategy name '{strategy_arg}'. Matches: {', '.join(names)}"
        )

    raise FileNotFoundError(
        f"Strategy file not found for '{strategy_arg}'. Check available files in {STRATEGIES_PATH}"
    )


# ============================================================================
# Strategy Ledger
# ============================================================================


def load_strategy_ledger() -> dict[str, dict[str, Any]]:
    """Load strategy ledger from YAML file.

    Returns:
        Dict mapping strategy name to metadata dict.

    """
    import yaml

    with open(LEDGER_PATH) as f:
        return yaml.safe_load(f) or {}


def find_composer_url(ledger: dict[str, dict[str, Any]], dsl_file: str) -> str | None:
    """Find the Composer source URL for a DSL file.

    Args:
        ledger: Strategy ledger data.
        dsl_file: DSL filename (e.g. 'gold.clj' or 'ftlt/tqqq_ftlt.clj').

    Returns:
        Composer URL string, or None if not found.

    """
    basename = Path(dsl_file).name
    for strategy_info in ledger.values():
        ledger_filename = strategy_info.get("filename", "")
        if ledger_filename == dsl_file or ledger_filename == basename:
            return strategy_info.get("source_url")
    return None


# ============================================================================
# Historical Market Data Adapter
# ============================================================================


def create_historical_adapter(cutoff_date: date) -> Any:
    """Create a MarketDataPort adapter that filters data to a cutoff date.

    Returns bars from S3 only up to and including *cutoff_date*, allowing
    the DSL engine to produce the signal that would have been generated
    on that date.

    Args:
        cutoff_date: Only return bars on or before this date.

    Returns:
        An object implementing MarketDataPort.

    """
    import pandas as pd

    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
    from the_alchemiser.shared.types.market_data import BarModel
    from the_alchemiser.shared.types.market_data_port import MarketDataPort
    from the_alchemiser.shared.value_objects.symbol import Symbol

    class HistoricalMarketDataAdapter(MarketDataPort):
        """Adapter returning market data up to a cutoff date."""

        def __init__(self, cutoff: date) -> None:
            self.cutoff_date = cutoff
            self.market_data_store = MarketDataStore()
            self._cache: dict[str, pd.DataFrame] = {}

        def _get_dataframe(self, symbol: str) -> pd.DataFrame:
            """Get DataFrame for symbol, cached."""
            if symbol not in self._cache:
                df = self.market_data_store.read_symbol_data(symbol)
                if df is not None and not df.empty:
                    if "timestamp" in df.columns:
                        df = df.set_index("timestamp")
                    if not isinstance(df.index, pd.DatetimeIndex):
                        df.index = pd.to_datetime(df.index)
                    self._cache[symbol] = df
                else:
                    return pd.DataFrame()
            return self._cache[symbol]

        def get_bars(
            self,
            symbol: Symbol,
            period: str,
            timeframe: str,
        ) -> list[BarModel]:
            """Get bars filtered to cutoff date."""
            symbol_str = str(symbol)
            df = self._get_dataframe(symbol_str)
            if df.empty:
                return []

            cutoff_ts = pd.Timestamp(self.cutoff_date, tz=timezone.utc)
            if df.index.tz is None:
                df.index = df.index.tz_localize(timezone.utc)
            df_filtered = df[df.index.normalize() <= cutoff_ts]
            if df_filtered.empty:
                return []

            bars: list[BarModel] = []
            for ts, row in df_filtered.iterrows():
                bar = BarModel(
                    symbol=symbol_str,
                    timestamp=ts.to_pydatetime(),
                    open=Decimal(str(row.get("open", row.get("Open", 0)))),
                    high=Decimal(str(row.get("high", row.get("High", 0)))),
                    low=Decimal(str(row.get("low", row.get("Low", 0)))),
                    close=Decimal(str(row.get("close", row.get("Close", 0)))),
                    volume=int(row.get("volume", row.get("Volume", 0))),
                )
                bars.append(bar)
            return bars

        def get_latest_bar(self, symbol: Symbol) -> BarModel | None:
            """Get latest bar as of cutoff date."""
            bars = self.get_bars(symbol, "1D", "1D")
            return bars[-1] if bars else None

        def get_quote(self, symbol: Symbol) -> Any:
            """Not used in historical mode."""
            return None

    return HistoricalMarketDataAdapter(cutoff_date)


# ============================================================================
# Strategy Execution
# ============================================================================


def run_strategy_for_date(
    dsl_file: str,
    as_of_date: date,
) -> dict[str, Any]:
    """Run a strategy with market data cutoff at a specific date.

    Args:
        dsl_file: DSL strategy filename.
        as_of_date: Only use market data up to this date.

    Returns:
        Dict with keys: target_weights, decision_path, debug_traces.

    """
    from engines.dsl.engine import DslEngine

    adapter = create_historical_adapter(as_of_date)

    engine = DslEngine(
        strategy_config_path=STRATEGIES_PATH,
        market_data_adapter=adapter,
        debug_mode=True,
    )

    correlation_id = f"validate-{dsl_file}-{as_of_date.isoformat()}"
    allocation, _trace = engine.evaluate_strategy(dsl_file, correlation_id, as_of_date=as_of_date)

    debug_traces = engine.evaluator.debug_traces
    decision_path = engine.evaluator.decision_path

    return {
        "target_weights": {k: v for k, v in allocation.target_weights.items()},
        "decision_path": decision_path,
        "debug_traces": debug_traces,
    }


# ============================================================================
# Composer Holdings Parser (from validate_signals.py)
# ============================================================================


def parse_composer_holdings(raw_text: str) -> dict[str, Decimal]:
    """Parse Composer.trade 'Simulated Holdings' copy-paste format.

    Expects lines like:
        SPY
        60.0 %
        TLT
        40.0 %

    Args:
        raw_text: Raw text pasted from Composer backtest.

    Returns:
        Dict mapping symbol to weight (as Decimal fraction, e.g. 0.60).

    """
    holdings: dict[str, Decimal] = {}
    lines = raw_text.strip().split("\n")
    last_ticker: str | None = None

    for line in lines:
        line = line.strip()
        if not line or "Symphony Cash Remainder" in line:
            last_ticker = None
            continue

        alloc_match = re.search(r"(\d+\.?\d*)\s*%\s*$", line)
        if alloc_match and last_ticker:
            holdings[last_ticker] = Decimal(alloc_match.group(1)) / Decimal("100")
            last_ticker = None
            continue

        if re.match(r"^[A-Z][A-Z0-9]{0,4}$", line):
            last_ticker = line

    return holdings


def capture_composer_holdings(label: str) -> dict[str, Decimal] | None:
    """Capture Composer holdings via paste + Ctrl+D.

    Args:
        label: Label for the temp file (used in display).

    Returns:
        Parsed holdings dict, or None if cancelled/empty.

    """
    safe_label = label.replace("/", "_")
    temp_path = Path(tempfile.gettempdir()) / f"composer_{safe_label}.txt"

    print("\n  Paste Composer holdings, then press Enter + Ctrl+D:")

    try:
        with open(temp_path, "w") as f:
            subprocess.run(["cat"], stdout=f, check=True)
    except (subprocess.CalledProcessError, KeyboardInterrupt):
        print("  Cancelled")
        return None

    try:
        content = temp_path.read_text()
        temp_path.unlink()
    except (FileNotFoundError, OSError):
        return None

    if not content.strip():
        print("  Empty input (skipped)")
        return None

    holdings = parse_composer_holdings(content)
    if not holdings:
        print("  Could not parse holdings from input")
        return None

    print(f"\n  Parsed {len(holdings)} holdings:")
    for ticker, weight in sorted(holdings.items(), key=lambda x: x[1], reverse=True):
        print(f"    {ticker:<8} {float(weight) * 100:>6.2f}%")

    return holdings


# ============================================================================
# Comparison Logic
# ============================================================================


def compare_signals(
    our_signals: dict[str, Decimal],
    composer_signals: dict[str, Decimal],
    tolerance: Decimal,
) -> tuple[bool, list[str]]:
    """Compare our signals vs Composer signals within tolerance.

    Args:
        our_signals: Our strategy output weights.
        composer_signals: Composer backtest weights.
        tolerance: Maximum absolute difference to consider a match.

    Returns:
        Tuple of (is_match, list of difference descriptions).

    """
    all_symbols = sorted(set(our_signals.keys()) | set(composer_signals.keys()))
    diffs: list[str] = []

    for sym in all_symbols:
        ours = our_signals.get(sym)
        theirs = composer_signals.get(sym)

        if ours is None:
            diffs.append(f"{sym}: missing from ours (composer={float(theirs or 0) * 100:.1f}%)")
        elif theirs is None:
            diffs.append(f"{sym}: extra in ours ({float(ours) * 100:.1f}%, not in composer)")
        elif abs(float(ours) - float(theirs)) >= float(tolerance):
            delta = (float(ours) - float(theirs)) * 100
            diffs.append(
                f"{sym}: {delta:+.1f}pp (ours={float(ours) * 100:.1f}%, composer={float(theirs) * 100:.1f}%)"
            )

    return len(diffs) == 0, diffs


def format_weights(weights: dict[str, Decimal]) -> str:
    """Format a weights dict as a compact string.

    Args:
        weights: Dict mapping symbol to Decimal weight.

    Returns:
        Formatted string like 'SPY=60.0% TLT=40.0%'.

    """
    parts = [
        f"{sym}={float(w) * 100:.1f}%"
        for sym, w in sorted(weights.items(), key=lambda x: -float(x[1]))
    ]
    return " ".join(parts)


# ============================================================================
# CSV Report
# ============================================================================


CSV_FIELDS = [
    "date",
    "strategy_name",
    "dsl_file",
    "our_signals",
    "composer_signals",
    "status",
    "differences",
    "decision_path",
    "validated_at",
]


def write_csv_report(
    results: list[dict[str, Any]],
    strategy_name: str,
    end_date: date,
) -> Path:
    """Write validation results to CSV.

    Args:
        results: List of per-day result dicts.
        strategy_name: Strategy name for the filename.
        end_date: End date of the validation window.

    Returns:
        Path to the written CSV file.

    """
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = VALIDATION_DIR / f"strategy_validation_{strategy_name}_{end_date.isoformat()}.csv"

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    return csv_path


# ============================================================================
# Main
# ============================================================================


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate a single strategy against Composer daily-close backtest",
    )
    parser.add_argument(
        "strategy",
        help="Strategy name (e.g. 'gold'), filename ('gold.clj'), or path ('ftlt/tqqq_ftlt.clj')",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        help="Number of trading days to validate (default: 5, i.e. ~1 week)",
    )
    parser.add_argument(
        "--end-date",
        default="yesterday",
        help="End date of the validation window (YYYY-MM-DD, 'yesterday', 'today'). Default: yesterday",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't auto-open the Composer URL",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.05,
        help="Match tolerance as absolute weight difference (default: 0.05 = 5pp)",
    )

    args = parser.parse_args()

    tolerance = Decimal(str(args.tolerance))
    end_date = parse_date(args.end_date)

    # Resolve strategy file
    try:
        dsl_file = resolve_strategy_file(args.strategy)
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)

    strategy_name = dsl_file.replace(".clj", "")
    trading_days = get_trading_days(end_date, args.days)

    print("\n" + "=" * 80)
    print("SINGLE-STRATEGY VALIDATION")
    print("=" * 80)
    print(f"  Strategy:      {strategy_name} ({dsl_file})")
    print(
        f"  Window:        {trading_days[0]} to {trading_days[-1]} ({len(trading_days)} trading days)"
    )
    print(f"  Tolerance:     {float(tolerance) * 100:.1f}pp")

    # -----------------------------------------------------------------------
    # Phase 1: Run strategy for each trading day
    # -----------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("PHASE 1: Running strategy for each trading day")
    print("-" * 80)

    day_results: list[dict[str, Any]] = []

    for i, day in enumerate(trading_days, 1):
        try:
            result = run_strategy_for_date(dsl_file, day)
            weights = result["target_weights"]
            weight_str = format_weights(weights)
            print(f"  [{i}/{len(trading_days)}] {day}: {weight_str}")
            day_results.append(
                {
                    "date": day,
                    "our_signals": weights,
                    "decision_path": result["decision_path"],
                    "debug_traces": result["debug_traces"],
                }
            )
        except Exception as e:
            print(f"  [{i}/{len(trading_days)}] {day}: ERROR - {type(e).__name__}: {e}")
            day_results.append(
                {
                    "date": day,
                    "our_signals": None,
                    "decision_path": [],
                    "debug_traces": [],
                    "error": str(e),
                }
            )

    successful = sum(1 for r in day_results if r["our_signals"] is not None)
    print(f"\n  Completed: {successful}/{len(trading_days)} days")

    # -----------------------------------------------------------------------
    # Phase 2: Prompt for Composer backtest holdings
    # -----------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("PHASE 2: Capture Composer daily-close backtest holdings")
    print("-" * 80)

    # Load ledger and optionally open browser
    try:
        ledger = load_strategy_ledger()
        composer_url = find_composer_url(ledger, dsl_file)
    except Exception:
        ledger = {}
        composer_url = None

    if composer_url:
        print(f"\n  Composer URL: {composer_url}")
        if not args.no_browser:
            print("  Opening in browser...")
            try:
                webbrowser.open(composer_url)
            except Exception:
                pass
    else:
        print("\n  (No Composer URL found in strategy ledger)")

    print(
        "\n  Instructions:"
        "\n  1. Open the Composer backtest for this strategy"
        "\n  2. For each date below, navigate to that date in the backtest"
        "\n  3. Copy the 'Simulated Holdings' and paste them when prompted"
        "\n  4. Press Enter then Ctrl+D to confirm each entry"
        "\n  5. Press Ctrl+D immediately (empty) to skip a day"
        "\n  6. Press Ctrl+C to abort"
    )

    try:
        for i, day_result in enumerate(day_results):
            day = day_result["date"]
            our_weights = day_result["our_signals"]

            print(f"\n  --- Day {i + 1}/{len(trading_days)}: {day} ---")
            if our_weights:
                print(f"  Our signal: {format_weights(our_weights)}")
            else:
                print(f"  Our signal: ERROR (skipping comparison)")
                day_result["composer_signals"] = None
                continue

            composer = capture_composer_holdings(f"{strategy_name}_{day.isoformat()}")
            day_result["composer_signals"] = composer

    except KeyboardInterrupt:
        print("\n\n  Interrupted -- proceeding with captured data")
        # Fill remaining days with None
        for r in day_results:
            if "composer_signals" not in r:
                r["composer_signals"] = None

    # -----------------------------------------------------------------------
    # Phase 3: Comparison report
    # -----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("VALIDATION REPORT")
    print("=" * 80)
    print(f"  Strategy: {strategy_name}")
    print(f"  Window:   {trading_days[0]} to {trading_days[-1]}")
    print(f"  Tolerance: {float(tolerance) * 100:.1f}pp")

    matches = 0
    mismatches = 0
    skipped = 0

    print(f"\n  {'Date':<14} {'Status':<12} {'Details'}")
    print("  " + "-" * 72)

    for day_result in day_results:
        day = day_result["date"]
        our_signals = day_result.get("our_signals")
        composer_signals = day_result.get("composer_signals")

        if our_signals is None or composer_signals is None:
            reason = "no Composer input" if our_signals else "engine error"
            print(f"  {day!s:<14} {'SKIP':<12} {reason}")
            skipped += 1
            day_result["status"] = "SKIPPED"
            day_result["diffs"] = []
            continue

        is_match, diffs = compare_signals(our_signals, composer_signals, tolerance)

        if is_match:
            matches += 1
            print(f"  {day!s:<14} {'MATCH':<12} {format_weights(our_signals)}")
            day_result["status"] = "MATCH"
        else:
            mismatches += 1
            diff_summary = "; ".join(diffs[:3])
            if len(diffs) > 3:
                diff_summary += f" (+{len(diffs) - 3} more)"
            print(f"  {day!s:<14} {'MISMATCH':<12} {diff_summary}")
            day_result["status"] = "MISMATCH"

        day_result["diffs"] = diffs

    total_compared = matches + mismatches
    rate = (matches / total_compared * 100) if total_compared > 0 else 0

    print("  " + "-" * 72)
    print(f"\n  SUMMARY: {matches}/{total_compared} matched ({rate:.1f}%)")
    if skipped:
        print(f"           {skipped} skipped")

    # Show decision path details for mismatched days
    mismatch_days = [r for r in day_results if r.get("status") == "MISMATCH"]
    if mismatch_days:
        print("\n" + "-" * 80)
        print("MISMATCH DETAILS (decision paths for divergent days)")
        print("-" * 80)
        for r in mismatch_days:
            day = r["date"]
            print(f"\n  {day}:")
            print(f"    Ours:     {format_weights(r['our_signals'])}")
            if r.get("composer_signals"):
                print(f"    Composer: {format_weights(r['composer_signals'])}")
            for diff in r.get("diffs", []):
                print(f"    - {diff}")
            decision_path = r.get("decision_path", [])
            if decision_path:
                print("    Decision path:")
                for j, decision in enumerate(decision_path, 1):
                    condition = decision.get("condition", "?")
                    result = decision.get("result", "?")
                    branch = decision.get("branch", "?")
                    print(f"      [{j}] {condition} = {result} -> {branch}")

    # -----------------------------------------------------------------------
    # Phase 4: Save CSV report
    # -----------------------------------------------------------------------
    csv_rows: list[dict[str, Any]] = []
    validated_at = datetime.now(UTC).isoformat()

    for r in day_results:
        our_json = ""
        if r.get("our_signals"):
            our_json = json.dumps(
                {k: float(v) for k, v in r["our_signals"].items()},
                sort_keys=True,
            )

        composer_json = ""
        if r.get("composer_signals"):
            composer_json = json.dumps(
                {k: float(v) for k, v in r["composer_signals"].items()},
                sort_keys=True,
            )

        decision_json = ""
        if r.get("decision_path"):
            decision_json = json.dumps(r["decision_path"])

        csv_rows.append(
            {
                "date": r["date"].isoformat(),
                "strategy_name": strategy_name,
                "dsl_file": dsl_file,
                "our_signals": our_json,
                "composer_signals": composer_json,
                "status": r.get("status", "SKIPPED"),
                "differences": "; ".join(r.get("diffs", [])),
                "decision_path": decision_json,
                "validated_at": validated_at,
            }
        )

    csv_path = write_csv_report(csv_rows, strategy_name, end_date)
    print(f"\n  Report saved to: {csv_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
