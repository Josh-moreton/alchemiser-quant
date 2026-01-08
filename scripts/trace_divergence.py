#!/usr/bin/env python3
"""Trace exact divergence point between our system and Composer.

Business Unit: Scripts | Status: current.

This script traces through ftl_starburst step-by-step showing each decision
with actual indicator values, to find exactly where we diverge from Composer.

Composer output (from differences.txt):
  SOXL 33.3%, TECL 44.5%, EDC 10.9%, COST 4%, LLY 2.4%, GE 3%, NVO 1.7%
"""

import os
import sys
import uuid

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, "functions", "strategy_worker"))
sys.path.insert(0, os.path.join(project_root, "layers", "shared"))

os.environ["MARKET_DATA_BUCKET"] = "alchemiser-dev-market-data"
os.environ.setdefault("AWS_REGION", "ap-southeast-2")
os.environ["LOG_LEVEL"] = "WARNING"  # Reduce noise

from the_alchemiser.shared.data_v2.cached_market_data_adapter import CachedMarketDataAdapter
from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest
from indicators.indicator_service import IndicatorService


def main() -> None:
    """Trace divergence point."""
    store = MarketDataStore()
    adapter = CachedMarketDataAdapter(market_data_store=store)
    indicator_service = IndicatorService(market_data_service=adapter)
    
    def get_indicator(symbol: str, ind_type: str, window: int) -> float:
        request = IndicatorRequest(
            request_id=str(uuid.uuid4()),
            symbol=symbol,
            indicator_type=ind_type,
            parameters={"window": window},
            correlation_id="trace",
        )
        result = indicator_service.get_indicator(request)
        return float(result.metadata.get("value", 0.0))
    
    print("=" * 80)
    print("FTL Starburst: Tracing Divergence from Composer")
    print("=" * 80)
    print("\nComposer output: SOXL 33.3%, TECL 44.5%, EDC 10.9%, COST 4%, LLY 2.4%, GE 3%, NVO 1.7%")
    print("Our output: varies (TECL 100% or TQQQ+TECL)")
    print("\n" + "=" * 80)
    
    # The outer structure is:
    # (weight-equal [(group "FTL Starburst" [(weight-equal [(filter ...)])])])
    # 
    # Inside the filter, there are multiple groups being compared by moving-average-return
    
    print("\n[STEP 1] Top-level filter: (moving-average-return {:window 10}) select-bottom 1")
    print("-" * 80)
    print("This filter selects the group with LOWEST 10-day moving average return.")
    print("The filter contains 3 groups (from strategy inspection):")
    print("  1. WYLD Mean Reversion Combo (line 12)")
    print("  2. Another copy (line 5923) - filtered by RSI")  
    print("  3. Another copy (line 11834) - filtered by stdev-return")
    
    # Let's trace the FIRST group - WYLD Mean Reversion Combo
    print("\n" + "=" * 80)
    print("[STEP 2] Inside WYLD Mean Reversion Combo - FXI check")
    print("-" * 80)
    
    fxi_cumret_5 = get_indicator("FXI", "cumulative_return", 5)
    print(f"FXI cumulative-return(5) = {fxi_cumret_5:.4f}%")
    print(f"Condition: cumret > 10 ? → {fxi_cumret_5:.4f} > 10 = {fxi_cumret_5 > 10}")
    
    if fxi_cumret_5 > 10:
        print("→ BULLISH branch: FXI is strong")
        fxi_cumret_1 = get_indicator("FXI", "cumulative_return", 1)
        print(f"  FXI cumulative-return(1) = {fxi_cumret_1:.4f}%")
        if fxi_cumret_1 < -2:
            print("  → YINN selected (mean reversion long)")
        else:
            print("  → YANG selected (momentum short)")
    else:
        print("→ NOT bullish, checking if bearish...")
        
        fxi_check_bearish = fxi_cumret_5 < -10
        print(f"Condition: cumret < -10 ? → {fxi_cumret_5:.4f} < -10 = {fxi_check_bearish}")
        
        if fxi_check_bearish:
            print("→ BEARISH branch")
            fxi_cumret_1 = get_indicator("FXI", "cumulative_return", 1)
            if fxi_cumret_1 > 2:
                print("  → YANG selected")
            else:
                print("  → YINN selected")
        else:
            print("→ NEUTRAL: Taking 'Overcompensating Frontrunner' branch")
            
            # This is where it gets interesting
            print("\n" + "=" * 80)
            print("[STEP 3] Overcompensating Frontrunner - IEF vs PSQ RSI check")
            print("-" * 80)
            
            ief_rsi_20 = get_indicator("IEF", "rsi", 20)
            psq_rsi_60 = get_indicator("PSQ", "rsi", 60)
            
            print(f"IEF RSI(20) = {ief_rsi_20:.4f}")
            print(f"PSQ RSI(60) = {psq_rsi_60:.4f}")
            print(f"Condition: IEF RSI > PSQ RSI ? → {ief_rsi_20:.4f} > {psq_rsi_60:.4f} = {ief_rsi_20 > psq_rsi_60}")
            
            if ief_rsi_20 > psq_rsi_60:
                print("→ BULLISH PATH: stdev filter on TQQQ vs alternatives")
                print("\n  This branch uses (filter stdev-return select-top 1) on 8 groups:")
                print("  Each group compares TQQQ vs another asset by max-drawdown")
                
                # Show the max-drawdown comparisons
                comparisons = [
                    ("TQQQ", "UVXY", 11),
                    ("TQQQ", "SOXL", 10),
                    ("TQQQ", "FNGU", 9),
                    ("TQQQ", "UUP", 10),
                    ("TQQQ", "VDE", 10),
                    ("TQQQ", "SMH", 11),
                    ("TQQQ", "AVUV", 12),
                    ("TQQQ", "NAIL", 12),
                ]
                
                print("\n  Max-drawdown comparisons (select-bottom 1 = lowest drawdown wins):")
                for sym1, sym2, window in comparisons:
                    dd1 = get_indicator(sym1, "max_drawdown", window)
                    dd2 = get_indicator(sym2, "max_drawdown", window)
                    winner = sym1 if dd1 < dd2 else sym2
                    print(f"    {sym1} dd({window})={dd1:.2f}% vs {sym2} dd({window})={dd2:.2f}% → {winner}")
                
            else:
                print("→ WAM PACKAGE branch")
                
                print("\n" + "=" * 80)
                print("[STEP 4] WAM Package - VIXM RSI check")
                print("-" * 80)
                
                vixm_rsi_14 = get_indicator("VIXM", "rsi", 14)
                print(f"VIXM RSI(14) = {vixm_rsi_14:.4f}")
                print(f"Condition: VIXM RSI > 70 ? → {vixm_rsi_14:.4f} > 70 = {vixm_rsi_14 > 70}")
                
                if vixm_rsi_14 > 70:
                    print("→ BIL selected (high volatility, go to cash)")
                else:
                    print("→ Continue to Muted WAMCore...")
                    
                    agg_rsi_15 = get_indicator("AGG", "rsi", 15)
                    qqq_rsi_15 = get_indicator("QQQ", "rsi", 15)
                    
                    print(f"\n  AGG RSI(15) = {agg_rsi_15:.4f}")
                    print(f"  QQQ RSI(15) = {qqq_rsi_15:.4f}")
                    print(f"  Condition: AGG RSI > QQQ RSI ? → {agg_rsi_15 > qqq_rsi_15}")
                    
                    if agg_rsi_15 > qqq_rsi_15:
                        print("  → Muted Bull branch (select from XLK, QQQ, XLRE, IWM, etc.)")
                    else:
                        print("  → Muted Bear branch (select from TECS, SQQQ, DRV, etc.)")
    
    # Now trace the KEY decision points that affect TECL/TECS and EDC/EDZ
    print("\n" + "=" * 80)
    print("[KEY DECISION] TECL vs TECS - XLK vs KMLM RSI comparison")
    print("-" * 80)
    
    xlk_rsi_10 = get_indicator("XLK", "rsi", 10)
    kmlm_rsi_10 = get_indicator("KMLM", "rsi", 10)
    
    print(f"XLK RSI(10) = {xlk_rsi_10:.4f}")
    print(f"KMLM RSI(10) = {kmlm_rsi_10:.4f}")
    print(f"Condition: XLK RSI > KMLM RSI ? → {xlk_rsi_10:.4f} > {kmlm_rsi_10:.4f} = {xlk_rsi_10 > kmlm_rsi_10}")
    
    if xlk_rsi_10 > kmlm_rsi_10:
        print("→ TECL selected (tech bullish)")
        print("✓ MATCHES COMPOSER (Composer has TECL 44.5%)")
    else:
        print("→ TECS selected (tech bearish)")
        print("✗ DIVERGES FROM COMPOSER (Composer has TECL, not TECS)")
    
    print("\n" + "=" * 80)
    print("[KEY DECISION] EDC vs EDZ - IEI vs IWM RSI comparison")
    print("-" * 80)
    
    iei_rsi_11 = get_indicator("IEI", "rsi", 11)
    iwm_rsi_16 = get_indicator("IWM", "rsi", 16)
    
    print(f"IEI RSI(11) = {iei_rsi_11:.4f}")
    print(f"IWM RSI(16) = {iwm_rsi_16:.4f}")
    print(f"Condition: IEI RSI > IWM RSI ? → {iei_rsi_11:.4f} > {iwm_rsi_16:.4f} = {iei_rsi_11 > iwm_rsi_16}")
    
    if iei_rsi_11 > iwm_rsi_16:
        print("→ EDC selected (EM bullish)")
        print("✓ MATCHES COMPOSER (Composer has EDC 10.9%)")
    else:
        print("→ EDZ selected (EM bearish)")
        print("✗ DIVERGES FROM COMPOSER (Composer has EDC, not EDZ)")
    
    # Now check SOXL - why does Composer have SOXL 33.3%?
    print("\n" + "=" * 80)
    print("[KEY QUESTION] Why does Composer have SOXL 33.3%?")
    print("-" * 80)
    print("Looking at the outer structure, there are weight-equal combinations.")
    print("Let's check the stdev-return scores for the filtered groups:")
    
    # These are the groups being filtered at the outer level
    symbols_to_check = ["TECL", "SOXL", "TQQQ"]
    
    print("\nStdev-return(10) for potential output symbols:")
    for sym in symbols_to_check:
        sd = get_indicator(sym, "stdev_return", 10)
        print(f"  {sym}: {sd:.4f}")
    
    print("\nMoving-average-return(10) for potential output symbols:")
    for sym in symbols_to_check:
        mar = get_indicator(sym, "moving_average_return", 10)
        print(f"  {sym}: {mar:.4f}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print("""
The key question: Why does Composer show SOXL 33.3%, TECL 44.5%, EDC 10.9%?

This suggests the strategy is NOT selecting a single portfolio, but combining
multiple portfolios with different weights.

Looking at the structure:
- The outer (weight-equal) at line 4 should equal-weight the results
- Inside, there's a filter (select-bottom 1) which should pick ONE winner
- But Composer shows multiple assets with different weights

This could mean:
1. The filter logic in our system differs from Composer
2. The weight combination logic differs
3. There's nested weight-equal that we're not handling correctly

Let me check what our actual evaluator produces...
""")
    
    # Run the actual strategy
    print("\n" + "=" * 80)
    print("RUNNING ACTUAL STRATEGY EVALUATION")
    print("=" * 80)
    
    from engines.dsl.dsl_evaluator import DslEvaluator
    from engines.dsl.sexpr_parser import SexprParser
    
    strategy_path = os.path.join(
        project_root,
        "layers/shared/the_alchemiser/shared/strategies/ftl_starburst.clj",
    )
    with open(strategy_path) as f:
        strategy_content = f.read()
    
    parser = SexprParser()
    ast = parser.parse(strategy_content)
    
    evaluator = DslEvaluator(indicator_service=indicator_service)
    result = evaluator.evaluate(ast, correlation_id="divergence-trace")
    
    # Extract weights
    weights = {}
    if hasattr(result, "target_weights"):
        weights = result.target_weights
    elif isinstance(result, tuple):
        for elem in result:
            if hasattr(elem, "target_weights"):
                weights = elem.target_weights
                break
    
    print("\nOUR SYSTEM OUTPUT:")
    for sym, w in sorted(weights.items(), key=lambda x: -float(x[1])):
        print(f"  {sym}: {float(w) * 100:.2f}%")
    
    print("\nCOMPOSER OUTPUT:")
    print("  SOXL: 33.30%")
    print("  TECL: 44.50%")
    print("  EDC: 10.90%")
    print("  COST: 4.00%")
    print("  GE: 3.00%")
    print("  LLY: 2.40%")
    print("  NVO: 1.70%")


if __name__ == "__main__":
    main()
