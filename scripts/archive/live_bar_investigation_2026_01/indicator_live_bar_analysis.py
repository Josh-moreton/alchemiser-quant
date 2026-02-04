#!/usr/bin/env python3
"""Business Unit: Strategy | Status: current.

Indicator Live Bar Analysis - Comprehensive T0 vs T-1 testing for Composer parity.

This script systematically tests all combinations of T0 (live bar) vs T-1 (no live bar)
indicator configurations across all strategies, for specific historical dates.

It compares computed allocations against validation CSVs (ground truth from Composer)
to determine the optimal live bar configuration for each strategy/indicator.

Outputs:
- Markdown report with summary tables and recommendations
- Raw JSON with full debug traces for each test run

Usage:
    poetry run python scripts/indicator_live_bar_analysis.py
    poetry run python scripts/indicator_live_bar_analysis.py --dates 2026-01-15 2026-01-16
    poetry run python scripts/indicator_live_bar_analysis.py --strategies blatant_tech gold
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ==============================================================================
# CONFIGURATION
# ==============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
STRATEGIES_PATH = PROJECT_ROOT / "layers" / "shared" / "the_alchemiser" / "shared" / "strategies"
VALIDATION_PATH = PROJECT_ROOT / "validation_results"

# Map DSL indicator names to internal indicator types
INDICATOR_NAME_MAP: dict[str, str] = {
    "rsi": "rsi",
    "moving-average-price": "moving_average",
    "moving-average-return": "moving_average_return",
    "cumulative-return": "cumulative_return",
    "current-price": "current_price",
    "stdev-return": "stdev_return",
    "stdev-price": "stdev_price",
    "max-drawdown": "max_drawdown",
    "exponential-moving-average-price": "exponential_moving_average_price",
}

# Indicators we can toggle T0/T-1
TOGGLEABLE_INDICATORS = [
    "rsi",
    "moving_average",
    "moving_average_return",
    "cumulative_return",
    "stdev_return",
    "stdev_price",
    "max_drawdown",
    "exponential_moving_average_price",
]

# current_price is always T0 (by design) so we don't toggle it


# ==============================================================================
# DATA STRUCTURES
# ==============================================================================


@dataclass
class ValidationEntry:
    """A single validation entry from the CSV."""
    
    validation_date: str
    session_id: str
    strategy_name: str
    dsl_file: str
    matches: bool
    notes: str
    expected_symbols: set[str]  # Parsed from notes
    validated_at: str


@dataclass
class TestResult:
    """Result of a single test run."""
    
    strategy: str
    date: str
    indicator_config: dict[str, bool]  # indicator_type -> use_live_bar
    computed_symbols: set[str]
    expected_symbols: set[str]
    matches: bool
    allocation: dict[str, float]
    error: str | None = None


@dataclass
class StrategyAnalysis:
    """Analysis results for a single strategy."""
    
    strategy_name: str
    indicators_used: set[str]
    results_by_date: dict[str, list[TestResult]] = field(default_factory=dict)
    matching_configs: dict[str, list[dict[str, bool]]] = field(default_factory=dict)  # date -> list of matching configs
    

# ==============================================================================
# DSL PARSING
# ==============================================================================


def extract_indicators_from_dsl(dsl_content: str) -> set[str]:
    """Extract indicator types used in a DSL file.
    
    Args:
        dsl_content: Raw content of the .clj DSL file
        
    Returns:
        Set of indicator type names (internal format)
    """
    indicators: set[str] = set()
    
    # Patterns for different indicator usages
    patterns = [
        r'\(rsi\s+',                           # (rsi "SYMBOL" ...)
        r'\(moving-average-price\s+',          # (moving-average-price "SYMBOL" ...)
        r'\(moving-average-return\s+',         # (moving-average-return "SYMBOL" ...)
        r'\(cumulative-return\s+',             # (cumulative-return "SYMBOL" ...)
        r'\(current-price\s+',                 # (current-price "SYMBOL")
        r'\(stdev-return\s+',                  # (stdev-return "SYMBOL" ...)
        r'\(stdev-price\s+',                   # (stdev-price "SYMBOL" ...)
        r'\(max-drawdown\s+',                  # (max-drawdown "SYMBOL" ...)
        r'\(exponential-moving-average-price\s+',  # (exponential-moving-average-price ...)
        # Filter indicators (used inside filter blocks)
        r'\(filter\s+\(rsi\s+',                # (filter (rsi {:window ...}) ...)
        r'\(filter\s+\(moving-average-return\s+',
        r'\(filter\s+\(cumulative-return\s+',
    ]
    
    for pattern in patterns:
        if re.search(pattern, dsl_content):
            # Extract the indicator name from the pattern
            match = re.search(r'\(([a-z-]+)', pattern)
            if match:
                dsl_name = match.group(1)
                if dsl_name in INDICATOR_NAME_MAP:
                    indicators.add(INDICATOR_NAME_MAP[dsl_name])
    
    return indicators


def get_strategy_indicators(strategy_name: str) -> set[str]:
    """Get indicators used by a strategy.
    
    Args:
        strategy_name: Strategy name (without .clj)
        
    Returns:
        Set of indicator types used
    """
    dsl_path = STRATEGIES_PATH / f"{strategy_name}.clj"
    if not dsl_path.exists():
        return set()
    
    content = dsl_path.read_text()
    return extract_indicators_from_dsl(content)


def list_strategies() -> list[str]:
    """List all available strategies."""
    if not STRATEGIES_PATH.exists():
        return []
    return sorted([p.stem for p in STRATEGIES_PATH.glob("*.clj")])


# ==============================================================================
# VALIDATION CSV PARSING
# ==============================================================================


def parse_expected_symbols(notes: str) -> set[str]:
    """Parse expected symbols from validation notes.
    
    Args:
        notes: Notes field like "live signal is EDZ XLF" or empty
        
    Returns:
        Set of expected symbol names
    """
    if not notes:
        return set()
    
    # Look for "live signal is ..." pattern
    match = re.search(r'live signal is\s+([A-Z0-9\s]+)', notes, re.IGNORECASE)
    if match:
        symbols_str = match.group(1).strip()
        # Split on whitespace and filter empty
        return {s.strip() for s in symbols_str.split() if s.strip()}
    
    return set()


def load_validation_csv(date_str: str) -> dict[str, ValidationEntry]:
    """Load validation CSV for a specific date.
    
    Args:
        date_str: Date string like "2026-01-15"
        
    Returns:
        Dict mapping strategy_name to ValidationEntry
    """
    # Try multiple filename patterns
    patterns = [
        f"signal_validation_{date_str}.csv",
        f"signal_validation_{date_str}-dev.csv",
    ]
    
    for pattern in patterns:
        csv_path = VALIDATION_PATH / pattern
        if csv_path.exists():
            entries: dict[str, ValidationEntry] = {}
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    matches = row.get("matches", "").lower() == "yes"
                    notes = row.get("notes", "")
                    
                    entry = ValidationEntry(
                        validation_date=row.get("validation_date", ""),
                        session_id=row.get("session_id", ""),
                        strategy_name=row.get("strategy_name", ""),
                        dsl_file=row.get("dsl_file", ""),
                        matches=matches,
                        notes=notes,
                        expected_symbols=parse_expected_symbols(notes) if not matches else set(),
                        validated_at=row.get("validated_at", ""),
                    )
                    entries[entry.strategy_name] = entry
            return entries
    
    return {}


# ==============================================================================
# TRACE EXECUTION
# ==============================================================================


def run_trace(
    strategy: str,
    as_of_date: str,
    indicator_config: dict[str, bool],
) -> dict[str, Any]:
    """Run trace_strategy_routes with custom indicator config.
    
    Args:
        strategy: Strategy name
        as_of_date: Historical date (YYYY-MM-DD)
        indicator_config: Dict mapping indicator_type to use_live_bar boolean
        
    Returns:
        Trace output dict with allocation and debug info
    """
    config_json = json.dumps(indicator_config)
    out_file = Path(f"/tmp/indicator_test_{strategy}_{as_of_date}.json")
    
    cmd = [
        "poetry", "run", "python", "scripts/trace_strategy_routes.py",
        strategy,
        "--as-of", as_of_date,
        "--policy", "custom",
        "--indicator-config", config_json,
        "--out", str(out_file),
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=120,  # 2 minutes timeout per trace
    )
    
    if result.returncode != 0:
        return {
            "error": f"Command failed: {result.stderr[:500]}",
            "allocation": {},
        }
    
    try:
        with open(out_file) as f:
            data = json.load(f)
        return data
    except Exception as e:
        return {
            "error": f"JSON parse error: {e}",
            "allocation": {},
        }


def extract_symbols(allocation: dict[str, float]) -> set[str]:
    """Extract symbols with non-trivial weights from allocation.
    
    Args:
        allocation: Dict mapping symbol to weight
        
    Returns:
        Set of symbols with weight > 0.001
    """
    return {symbol for symbol, weight in allocation.items() if weight > 0.001}


# ==============================================================================
# TEST GENERATION
# ==============================================================================


def generate_indicator_configs(indicators: set[str]) -> list[dict[str, bool]]:
    """Generate all T0/T-1 combinations for a set of indicators.
    
    Args:
        indicators: Set of indicator types to toggle
        
    Returns:
        List of all possible configurations
    """
    # Filter to only toggleable indicators
    toggleable = [i for i in indicators if i in TOGGLEABLE_INDICATORS]
    
    if not toggleable:
        # No toggleable indicators, return single default config
        return [{}]
    
    # Generate all combinations
    configs: list[dict[str, bool]] = []
    for values in itertools.product([True, False], repeat=len(toggleable)):
        config = dict(zip(toggleable, values))
        configs.append(config)
    
    return configs


def config_to_label(config: dict[str, bool]) -> str:
    """Convert indicator config to human-readable label.
    
    Args:
        config: Dict mapping indicator_type to use_live_bar
        
    Returns:
        String like "rsi=T0, cumulative_return=T-1"
    """
    if not config:
        return "default"
    
    parts = []
    for indicator, use_live in sorted(config.items()):
        label = "T0" if use_live else "T-1"
        parts.append(f"{indicator}={label}")
    return ", ".join(parts)


# ==============================================================================
# MAIN ANALYSIS
# ==============================================================================


def run_analysis(
    strategies: list[str] | None = None,
    dates: list[str] | None = None,
    verbose: bool = False,
) -> tuple[list[StrategyAnalysis], dict[str, Any]]:
    """Run the full analysis.
    
    Args:
        strategies: List of strategy names (or None for all)
        dates: List of dates to test (or None for default)
        verbose: Print progress
        
    Returns:
        Tuple of (list of StrategyAnalysis, raw debug dict)
    """
    if strategies is None:
        strategies = list_strategies()
    if dates is None:
        dates = ["2026-01-15", "2026-01-16"]
    
    # Load all validation CSVs
    validations: dict[str, dict[str, ValidationEntry]] = {}
    for date in dates:
        validations[date] = load_validation_csv(date)
    
    # Results storage
    analyses: list[StrategyAnalysis] = []
    raw_debug: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dates": dates,
        "strategies": {},
    }
    
    for strategy in strategies:
        if verbose:
            print(f"\n{'='*60}")
            print(f"Analyzing: {strategy}")
            print("=" * 60)
        
        # Get indicators used by this strategy
        indicators = get_strategy_indicators(strategy)
        toggleable = {i for i in indicators if i in TOGGLEABLE_INDICATORS}
        
        if verbose:
            print(f"Indicators found: {indicators}")
            print(f"Toggleable: {toggleable}")
        
        # Generate all configs for this strategy
        configs = generate_indicator_configs(toggleable)
        
        if verbose:
            print(f"Testing {len(configs)} configurations")
        
        analysis = StrategyAnalysis(
            strategy_name=strategy,
            indicators_used=toggleable,
        )
        
        raw_debug["strategies"][strategy] = {
            "indicators": list(toggleable),
            "configs_tested": len(configs),
            "dates": {},
        }
        
        for date in dates:
            validation = validations.get(date, {}).get(strategy)
            
            if validation is None:
                if verbose:
                    print(f"  {date}: No validation data")
                continue
            
            # Get expected symbols
            if validation.matches:
                # If validation says "yes", we need to discover expected symbols from a matching run
                # For now, we'll run with default config to get the baseline
                expected_symbols: set[str] = set()
            else:
                expected_symbols = validation.expected_symbols
            
            results: list[TestResult] = []
            matching_configs: list[dict[str, bool]] = []
            
            raw_debug["strategies"][strategy]["dates"][date] = {
                "validation_matches": validation.matches,
                "expected_symbols": list(expected_symbols),
                "notes": validation.notes,
                "runs": [],
            }
            
            for i, config in enumerate(configs):
                if verbose:
                    print(f"  {date} config {i+1}/{len(configs)}: {config_to_label(config)}")
                
                try:
                    trace_output = run_trace(strategy, date, config)
                except subprocess.TimeoutExpired:
                    trace_output = {"error": "Timeout", "allocation": {}}
                except Exception as e:
                    trace_output = {"error": str(e), "allocation": {}}
                
                allocation = trace_output.get("allocation", {})
                computed_symbols = extract_symbols(allocation)
                error = trace_output.get("error")
                
                # For strategies that already match, discover expected symbols from first run
                if validation.matches and not expected_symbols and computed_symbols:
                    expected_symbols = computed_symbols.copy()
                    raw_debug["strategies"][strategy]["dates"][date]["expected_symbols"] = list(expected_symbols)
                
                # Check if this config produces a match
                matches = False
                if expected_symbols and computed_symbols:
                    matches = computed_symbols == expected_symbols
                elif validation.matches and computed_symbols:
                    # If validation says "yes" and we have symbols, assume match
                    # (first config sets the baseline)
                    matches = True
                
                result = TestResult(
                    strategy=strategy,
                    date=date,
                    indicator_config=config,
                    computed_symbols=computed_symbols,
                    expected_symbols=expected_symbols,
                    matches=matches,
                    allocation=allocation,
                    error=error,
                )
                results.append(result)
                
                if matches:
                    matching_configs.append(config)
                
                # Store debug info
                raw_debug["strategies"][strategy]["dates"][date]["runs"].append({
                    "config": config,
                    "config_label": config_to_label(config),
                    "computed_symbols": list(computed_symbols),
                    "matches": matches,
                    "error": error,
                    "allocation": allocation,
                    "decision_path": trace_output.get("decision_path"),
                })
                
                if verbose:
                    match_str = "✓ MATCH" if matches else "✗ no match"
                    print(f"    Computed: {sorted(computed_symbols)} {match_str}")
            
            analysis.results_by_date[date] = results
            analysis.matching_configs[date] = matching_configs
        
        analyses.append(analysis)
    
    return analyses, raw_debug


# ==============================================================================
# REPORT GENERATION
# ==============================================================================


def generate_markdown_report(
    analyses: list[StrategyAnalysis],
    dates: list[str],
) -> str:
    """Generate markdown report from analysis results.
    
    Args:
        analyses: List of StrategyAnalysis objects
        dates: List of dates tested
        
    Returns:
        Markdown string
    """
    lines: list[str] = []
    
    lines.append("# Indicator Live Bar Analysis Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"**Dates Tested:** {', '.join(dates)}")
    lines.append("")
    
    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Strategy | Indicators | " + " | ".join(f"{d} Match?" for d in dates) + " | Recommended Config |")
    lines.append("|" + "|".join(["---"] * (3 + len(dates))) + "|")
    
    for analysis in analyses:
        indicators_str = ", ".join(sorted(analysis.indicators_used)) or "none"
        
        # Check matches for each date
        date_matches = []
        for date in dates:
            matching = analysis.matching_configs.get(date, [])
            if matching:
                date_matches.append(f"✓ ({len(matching)} configs)")
            else:
                results = analysis.results_by_date.get(date, [])
                if not results:
                    date_matches.append("No data")
                else:
                    date_matches.append("✗")
        
        # Find configs that match ALL dates
        all_matching: list[dict[str, bool]] = []
        if all(analysis.matching_configs.get(d) for d in dates):
            # Find intersection of matching configs across dates
            first = True
            for date in dates:
                configs = analysis.matching_configs.get(date, [])
                configs_set = {tuple(sorted(c.items())) for c in configs}
                if first:
                    all_matching_set = configs_set
                    first = False
                else:
                    all_matching_set &= configs_set
            all_matching = [dict(c) for c in all_matching_set]
        
        if all_matching:
            # Prefer all-T-1 if available, otherwise show first
            all_t1 = next((c for c in all_matching if all(not v for v in c.values())), None)
            if all_t1:
                rec = "All T-1"
            else:
                rec = config_to_label(all_matching[0])
        else:
            rec = "**Needs investigation**"
        
        cols = [analysis.strategy_name, indicators_str] + date_matches + [rec]
        lines.append("| " + " | ".join(cols) + " |")
    
    lines.append("")
    
    # Detailed results per strategy
    lines.append("## Detailed Results")
    lines.append("")
    
    for analysis in analyses:
        lines.append(f"### {analysis.strategy_name}")
        lines.append("")
        lines.append(f"**Indicators used:** {', '.join(sorted(analysis.indicators_used)) or 'none'}")
        lines.append("")
        
        for date in dates:
            results = analysis.results_by_date.get(date, [])
            matching = analysis.matching_configs.get(date, [])
            
            lines.append(f"#### {date}")
            lines.append("")
            
            if not results:
                lines.append("*No validation data available*")
                lines.append("")
                continue
            
            # Show expected symbols
            if results:
                expected = results[0].expected_symbols
                lines.append(f"**Expected symbols (from Composer):** {' '.join(sorted(expected)) or 'N/A'}")
                lines.append("")
            
            # Results table
            lines.append("| Config | Computed Symbols | Match |")
            lines.append("|--------|-----------------|-------|")
            
            for result in results:
                config_str = config_to_label(result.indicator_config)
                symbols_str = " ".join(sorted(result.computed_symbols)) or "(empty)"
                match_str = "✓" if result.matches else "✗"
                if result.error:
                    symbols_str = f"ERROR: {result.error[:50]}"
                lines.append(f"| {config_str} | {symbols_str} | {match_str} |")
            
            lines.append("")
            
            if matching:
                lines.append(f"**Matching configurations ({len(matching)}):**")
                for config in matching[:5]:  # Limit to 5
                    lines.append(f"- {config_to_label(config)}")
                if len(matching) > 5:
                    lines.append(f"- ... and {len(matching) - 5} more")
                lines.append("")
            else:
                lines.append("**No matching configurations found!**")
                lines.append("")
    
    # Recommendations section
    lines.append("## Recommendations")
    lines.append("")
    
    # Find strategies that need all T-1
    all_t1_strategies = []
    mixed_strategies = []
    problem_strategies = []
    
    for analysis in analyses:
        # Find configs that match ALL dates
        all_matching: list[dict[str, bool]] = []
        if all(analysis.matching_configs.get(d) for d in dates):
            first = True
            all_matching_set: set[tuple[tuple[str, bool], ...]] = set()
            for date in dates:
                configs = analysis.matching_configs.get(date, [])
                configs_set = {tuple(sorted(c.items())) for c in configs}
                if first:
                    all_matching_set = configs_set
                    first = False
                else:
                    all_matching_set &= configs_set
            all_matching = [dict(c) for c in all_matching_set]
        
        if not all_matching:
            problem_strategies.append(analysis.strategy_name)
        elif any(all(not v for v in c.values()) for c in all_matching):
            all_t1_strategies.append(analysis.strategy_name)
        else:
            mixed_strategies.append((analysis.strategy_name, all_matching[0]))
    
    if all_t1_strategies:
        lines.append("### Strategies that work with All T-1 (recommended)")
        lines.append("")
        for s in all_t1_strategies:
            lines.append(f"- {s}")
        lines.append("")
    
    if mixed_strategies:
        lines.append("### Strategies requiring specific T0/T-1 mix")
        lines.append("")
        for s, config in mixed_strategies:
            lines.append(f"- **{s}:** {config_to_label(config)}")
        lines.append("")
    
    if problem_strategies:
        lines.append("### ⚠️ Strategies requiring investigation")
        lines.append("")
        lines.append("These strategies had no configuration that matched Composer across all dates:")
        lines.append("")
        for s in problem_strategies:
            lines.append(f"- {s}")
        lines.append("")
    
    return "\n".join(lines)


# ==============================================================================
# MAIN
# ==============================================================================


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze T0 vs T-1 indicator configurations for Composer parity"
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        help="Strategies to test (default: all)",
    )
    parser.add_argument(
        "--dates",
        nargs="+",
        default=["2026-01-15", "2026-01-16"],
        help="Dates to test (default: 2026-01-15 2026-01-16)",
    )
    parser.add_argument(
        "--output-dir",
        default="validation_results",
        help="Output directory for reports",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("INDICATOR LIVE BAR ANALYSIS")
    print("=" * 80)
    print()
    print(f"Dates: {', '.join(args.dates)}")
    print(f"Strategies: {', '.join(args.strategies) if args.strategies else 'all'}")
    print()
    
    # Run analysis
    analyses, raw_debug = run_analysis(
        strategies=args.strategies,
        dates=args.dates,
        verbose=args.verbose,
    )
    
    # Generate outputs
    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(exist_ok=True)
    
    # Markdown report
    md_report = generate_markdown_report(analyses, args.dates)
    md_path = output_dir / f"live_bar_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    md_path.write_text(md_report)
    print(f"\nMarkdown report: {md_path}")
    
    # Raw JSON debug
    json_path = output_dir / f"live_bar_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_path, "w") as f:
        json.dump(raw_debug, f, indent=2, default=str)
    print(f"Raw JSON debug: {json_path}")
    
    # Also print summary to console
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for analysis in analyses:
        # Find configs that match ALL dates
        all_matching: list[dict[str, bool]] = []
        if all(analysis.matching_configs.get(d) for d in args.dates):
            first = True
            all_matching_set: set[tuple[tuple[str, bool], ...]] = set()
            for date in args.dates:
                configs = analysis.matching_configs.get(date, [])
                configs_set = {tuple(sorted(c.items())) for c in configs}
                if first:
                    all_matching_set = configs_set
                    first = False
                else:
                    all_matching_set &= configs_set
            all_matching = [dict(c) for c in all_matching_set]
        
        if all_matching:
            all_t1 = any(all(not v for v in c.values()) for c in all_matching)
            status = "✓ All T-1 works" if all_t1 else f"✓ Need: {config_to_label(all_matching[0])}"
        else:
            status = "✗ NEEDS INVESTIGATION"
        
        print(f"  {analysis.strategy_name:25s}: {status}")
    
    print()
    print("Done!")


if __name__ == "__main__":
    main()
