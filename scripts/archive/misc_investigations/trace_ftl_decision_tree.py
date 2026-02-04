#!/usr/bin/env python3
"""Trace ftl_starburst decision tree with full indicator values.

Business Unit: Scripts | Status: current.

This script traces through the ftl_starburst strategy showing each
conditional branch with actual indicator values to identify where
our system diverges from Composer.
"""

import os
import sys
import uuid
from datetime import date
from decimal import Decimal

# Set up paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, "functions", "strategy_worker"))
sys.path.insert(0, os.path.join(project_root, "layers", "shared"))

os.environ["MARKET_DATA_BUCKET"] = "alchemiser-dev-market-data"
os.environ.setdefault("AWS_REGION", "ap-southeast-2")

from the_alchemiser.shared.data_v2.cached_market_data_adapter import CachedMarketDataAdapter
from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest
from indicators.indicator_service import IndicatorService


def trace_decision_tree(as_of_date: date | None = None) -> None:
    """Trace the ftl_starburst decision tree with actual values."""
    # Set up services
    store = MarketDataStore()
    adapter = CachedMarketDataAdapter(market_data_store=store)
    indicator_service = IndicatorService(market_data_service=adapter)
    
    print("=" * 80)
    print("FTL Starburst Decision Tree Trace")
    print(f"As-of date: {as_of_date or 'latest'}")
    print("=" * 80)
    
    # Helper to get indicator values
    def get_cumret(symbol: str, window: int) -> float:
        request = IndicatorRequest(
            request_id=str(uuid.uuid4()),
            symbol=symbol,
            indicator_type="cumulative_return",
            parameters={"window": window},
            correlation_id="trace",
        )
        result = indicator_service.get_indicator(request)
        return float(result.metadata.get("value", 0.0))
    
    def get_rsi(symbol: str, window: int) -> float:
        request = IndicatorRequest(
            request_id=str(uuid.uuid4()),
            symbol=symbol,
            indicator_type="rsi",
            parameters={"window": window},
            correlation_id="trace",
        )
        result = indicator_service.get_indicator(request)
        return float(result.metadata.get("value", 0.0))
    
    def get_mar(symbol: str, window: int) -> float:
        """Moving average return."""
        request = IndicatorRequest(
            request_id=str(uuid.uuid4()),
            symbol=symbol,
            indicator_type="moving_average_return",
            parameters={"window": window},
            correlation_id="trace",
        )
        result = indicator_service.get_indicator(request)
        return float(result.metadata.get("value", 0.0))
    
    def get_max_dd(symbol: str, window: int) -> float:
        request = IndicatorRequest(
            request_id=str(uuid.uuid4()),
            symbol=symbol,
            indicator_type="max_drawdown",
            parameters={"window": window},
            correlation_id="trace",
        )
        result = indicator_service.get_indicator(request)
        return float(result.metadata.get("value", 0.0))
    
    def get_stdev_ret(symbol: str, window: int) -> float:
        request = IndicatorRequest(
            request_id=str(uuid.uuid4()),
            symbol=symbol,
            indicator_type="stdev_return",
            parameters={"window": window},
            correlation_id="trace",
        )
        result = indicator_service.get_indicator(request)
        return float(result.metadata.get("value", 0.0))

    # ==== LEVEL 1: FXI cumulative return 5-day check ====
    print("\n" + "─" * 80)
    print("LEVEL 1: FXI Momentum Check")
    print("─" * 80)
    
    fxi_cumret_5 = get_cumret("FXI", 5)
    print(f"  FXI cumulative-return(5) = {fxi_cumret_5:.4f}%")
    print(f"  Condition: cumret > 10 ?  {fxi_cumret_5:.4f} > 10 = {fxi_cumret_5 > 10}")
    
    if fxi_cumret_5 > 10:
        print("  → Taking BULLISH branch (FXI strong)")
        # Bullish mean reversion
        fxi_cumret_1 = get_cumret("FXI", 1)
        print(f"\n  LEVEL 1a: FXI short-term check")
        print(f"    FXI cumulative-return(1) = {fxi_cumret_1:.4f}%")
        print(f"    Condition: cumret < -2 ? = {fxi_cumret_1 < -2}")
        if fxi_cumret_1 < -2:
            print("    → YINN selected")
        else:
            print("    → YANG selected")
    else:
        print("  → Taking BEARISH/NEUTRAL branch")
        
        # Check for strong bearish
        fxi_cumret_5_neg = get_cumret("FXI", 5)
        print(f"\n  LEVEL 1b: Strong bearish check")
        print(f"    Condition: cumret < -10 ? {fxi_cumret_5_neg:.4f} < -10 = {fxi_cumret_5_neg < -10}")
        
        if fxi_cumret_5_neg < -10:
            print("    → Taking STRONG BEARISH branch")
            fxi_cumret_1 = get_cumret("FXI", 1)
            print(f"    FXI cumulative-return(1) = {fxi_cumret_1:.4f}%")
            if fxi_cumret_1 > 2:
                print("    → YANG selected")
            else:
                print("    → YINN selected")
        else:
            print("    → Taking OVERCOMPENSATING FRONTRUNNER branch")
            
            # ==== LEVEL 2: IEF vs PSQ RSI ====
            print("\n" + "─" * 80)
            print("LEVEL 2: IEF vs PSQ RSI Check (Overcompensating Frontrunner)")
            print("─" * 80)
            
            ief_rsi_20 = get_rsi("IEF", 20)
            psq_rsi_60 = get_rsi("PSQ", 60)
            print(f"  IEF RSI(20) = {ief_rsi_20:.4f}")
            print(f"  PSQ RSI(60) = {psq_rsi_60:.4f}")
            print(f"  Condition: IEF RSI > PSQ RSI ? {ief_rsi_20:.4f} > {psq_rsi_60:.4f} = {ief_rsi_20 > psq_rsi_60}")
            
            if ief_rsi_20 > psq_rsi_60:
                print("  → Taking BULLISH PATH (stdev filter on TQQQ groups)")
                
                # Stdev filter on multiple groups
                print("\n  LEVEL 2a: Stdev-return filter (select-top 1)")
                groups = [
                    ("TQQQ vs UVXY", 11),
                    ("TQQQ vs SOXL", 10),
                    ("TQQQ vs FNGU", 9),
                    ("TQQQ vs UUP", 10),
                    ("TQQQ vs VDE", 10),
                    ("TQQQ vs SMH", 11),
                    ("TQQQ vs AVUV", 12),
                    ("TQQQ vs NAIL", 12),
                ]
                # Each group needs max-dd filter results
                # This is complex - let's trace individual max-dd comparisons
                
                print("\n  Computing max-drawdown for each sub-group...")
                dd_tqqq_11 = get_max_dd("TQQQ", 11)
                dd_uvxy_11 = get_max_dd("UVXY", 11)
                print(f"    TQQQ max-dd(11) = {dd_tqqq_11:.4f}, UVXY max-dd(11) = {dd_uvxy_11:.4f}")
                print(f"    → select-bottom: {'TQQQ' if dd_tqqq_11 < dd_uvxy_11 else 'UVXY'}")
                
                dd_tqqq_10 = get_max_dd("TQQQ", 10)
                dd_soxl_10 = get_max_dd("SOXL", 10)
                print(f"    TQQQ max-dd(10) = {dd_tqqq_10:.4f}, SOXL max-dd(10) = {dd_soxl_10:.4f}")
                print(f"    → select-bottom: {'TQQQ' if dd_tqqq_10 < dd_soxl_10 else 'SOXL'}")
                
                dd_fngu_9 = get_max_dd("FNGU", 9)
                dd_tqqq_9 = get_max_dd("TQQQ", 9)
                print(f"    TQQQ max-dd(9) = {dd_tqqq_9:.4f}, FNGU max-dd(9) = {dd_fngu_9:.4f}")
                print(f"    → select-bottom: {'TQQQ' if dd_tqqq_9 < dd_fngu_9 else 'FNGU'}")
                
            else:
                print("  → Taking WAM PACKAGE branch")
                
                # ==== LEVEL 3: VIXM RSI check ====
                print("\n" + "─" * 80)
                print("LEVEL 3: WAM Package - VIXM RSI Check")
                print("─" * 80)
                
                vixm_rsi_14 = get_rsi("VIXM", 14)
                print(f"  VIXM RSI(14) = {vixm_rsi_14:.4f}")
                print(f"  Condition: VIXM RSI > 70 ? = {vixm_rsi_14 > 70}")
                
                if vixm_rsi_14 > 70:
                    print("  → BIL selected (high volatility)")
                else:
                    print("  → Taking Muted WAMCore branch")
                    
                    # ==== LEVEL 4: AGG vs QQQ RSI ====
                    print("\n" + "─" * 80)
                    print("LEVEL 4: Muted WAMCore - AGG vs QQQ RSI")
                    print("─" * 80)
                    
                    agg_rsi_15 = get_rsi("AGG", 15)
                    qqq_rsi_15 = get_rsi("QQQ", 15)
                    print(f"  AGG RSI(15) = {agg_rsi_15:.4f}")
                    print(f"  QQQ RSI(15) = {qqq_rsi_15:.4f}")
                    print(f"  Condition: AGG RSI > QQQ RSI ? {agg_rsi_15:.4f} > {qqq_rsi_15:.4f} = {agg_rsi_15 > qqq_rsi_15}")
                    
                    if agg_rsi_15 > qqq_rsi_15:
                        print("  → Muted Bull branch")
                    else:
                        print("  → Muted Bear branch")
    
    # ==== Second major branch: XLK vs KMLM RSI ====
    print("\n" + "=" * 80)
    print("SECOND PARALLEL BRANCH: Tech Momentum Check")
    print("=" * 80)
    
    xlk_rsi_10 = get_rsi("XLK", 10)
    kmlm_rsi_10 = get_rsi("KMLM", 10)
    print(f"  XLK RSI(10) = {xlk_rsi_10:.4f}")
    print(f"  KMLM RSI(10) = {kmlm_rsi_10:.4f}")
    print(f"  Condition: XLK RSI > KMLM RSI ? {xlk_rsi_10:.4f} > {kmlm_rsi_10:.4f} = {xlk_rsi_10 > kmlm_rsi_10}")
    
    if xlk_rsi_10 > kmlm_rsi_10:
        print("  → TECL selected (tech bullish)")
    else:
        print("  → TECS selected (tech bearish)")
    
    # ==== Third parallel branch: IEI vs IWM RSI ====
    print("\n" + "─" * 80)
    print("THIRD PARALLEL BRANCH: EDC/EDZ Selection")
    print("─" * 80)
    
    iei_rsi_11 = get_rsi("IEI", 11)
    iwm_rsi_16 = get_rsi("IWM", 16)
    print(f"  IEI RSI(11) = {iei_rsi_11:.4f}")
    print(f"  IWM RSI(16) = {iwm_rsi_16:.4f}")
    print(f"  Condition: IEI RSI > IWM RSI ? {iei_rsi_11:.4f} > {iwm_rsi_16:.4f} = {iei_rsi_11 > iwm_rsi_16}")
    
    if iei_rsi_11 > iwm_rsi_16:
        print("  → EDC selected (EM bullish)")
    else:
        print("  → EDZ selected (EM bearish)")
        
    print("\n" + "=" * 80)
    print("END OF DECISION TREE TRACE")
    print("=" * 80)


if __name__ == "__main__":
    trace_decision_tree()
