"""Business Unit: utilities | Status: current."""

from __future__ import annotations

# Central place to define per-environment DSL strategy defaults.

# Strategy file name constants
STRATEGY_KMLM = "1-KMLM.clj"
STRATEGY_NUCLEAR = "2-Nuclear.clj"
STRATEGY_STARBURST = "3-Starburst.clj"
STRATEGY_WHAT = "4-What.clj"
STRATEGY_COIN = "5-Coin.clj"
STRATEGY_TQQQ_FLT = "6-TQQQ-FLT.clj"
STRATEGY_PHOENIX = "7-Phoenix.clj"

DEV_DSL_FILES: list[str] = [
    STRATEGY_KMLM,
    STRATEGY_NUCLEAR,
    STRATEGY_STARBURST,
    STRATEGY_WHAT,
    STRATEGY_COIN,
    STRATEGY_TQQQ_FLT,
    STRATEGY_PHOENIX,
]

DEV_DSL_ALLOCATIONS: dict[str, float] = {
    STRATEGY_KMLM: 0.2,
    STRATEGY_NUCLEAR: 0.15,
    STRATEGY_STARBURST: 0.15,
    STRATEGY_WHAT: 0.1,
    STRATEGY_COIN: 0.1,
    STRATEGY_TQQQ_FLT: 0.15,
    STRATEGY_PHOENIX: 0.15,
}

PROD_DSL_FILES: list[str] = [
    STRATEGY_KMLM,
    STRATEGY_NUCLEAR,
    STRATEGY_COIN,
    STRATEGY_TQQQ_FLT,
]

PROD_DSL_ALLOCATIONS: dict[str, float] = {
    STRATEGY_KMLM: 0.4,
    STRATEGY_NUCLEAR: 0.25,
    STRATEGY_COIN: 0.1,
    STRATEGY_TQQQ_FLT: 0.25,
}
