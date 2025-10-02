"""Business Unit: utilities | Status: current."""

from __future__ import annotations

# Central place to define per-environment DSL strategy defaults.

# Strategy file name constants
_STRATEGY_KMLM = "1-KMLM.clj"
_STRATEGY_NUCLEAR = "2-Nuclear.clj"
_STRATEGY_STARBURST = "3-Starburst.clj"
_STRATEGY_WHAT = "4-What.clj"
_STRATEGY_COIN = "5-Coin.clj"
_STRATEGY_TQQQ_FLT = "6-TQQQ-FLT.clj"
_STRATEGY_PHOENIX = "7-Phoenix.clj"

DEV_DSL_FILES: list[str] = [
    _STRATEGY_KMLM,
    _STRATEGY_NUCLEAR,
    _STRATEGY_STARBURST,
    _STRATEGY_WHAT,
    _STRATEGY_COIN,
    _STRATEGY_TQQQ_FLT,
    _STRATEGY_PHOENIX,
]

DEV_DSL_ALLOCATIONS: dict[str, float] = {
    _STRATEGY_KMLM: 0.2,
    _STRATEGY_NUCLEAR: 0.15,
    _STRATEGY_STARBURST: 0.15,
    _STRATEGY_WHAT: 0.1,
    _STRATEGY_COIN: 0.1,
    _STRATEGY_TQQQ_FLT: 0.15,
    _STRATEGY_PHOENIX: 0.15,
}

PROD_DSL_FILES: list[str] = [
    _STRATEGY_KMLM,
    _STRATEGY_NUCLEAR,
    _STRATEGY_COIN,
    _STRATEGY_TQQQ_FLT,
]

PROD_DSL_ALLOCATIONS: dict[str, float] = {
    _STRATEGY_KMLM: 0.4,
    _STRATEGY_NUCLEAR: 0.25,
    _STRATEGY_COIN: 0.1,
    _STRATEGY_TQQQ_FLT: 0.25,
}
