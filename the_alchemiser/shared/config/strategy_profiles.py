"""Business Unit: utilities | Status: current."""

from __future__ import annotations

# Central place to define per-environment DSL strategy defaults.

DEV_DSL_FILES: list[str] = [
    "1-KMLM.clj",
    "2-Nuclear.clj",
    "3-Starburst.clj",
    "4-What.clj",
    "5-Coin.clj",
    "6-TQQQ-FLT.clj",
    "7-Phoenix.clj",
]

DEV_DSL_ALLOCATIONS: dict[str, float] = {
    "1-KMLM.clj": 0.2,
    "2-Nuclear.clj": 0.15,
    "3-Starburst.clj": 0.15,
    "4-What.clj": 0.1,
    "5-Coin.clj": 0.1,
    "6-TQQQ-FLT.clj": 0.15,
    "7-Phoenix.clj": 0.15,
}

PROD_DSL_FILES: list[str] = [
    "1-KMLM.clj",
    "2-Nuclear.clj",
    "5-Coin.clj",
    "6-TQQQ-FLT.clj",
]

PROD_DSL_ALLOCATIONS: dict[str, float] = {
    "1-KMLM.clj": 0.4,
    "2-Nuclear.clj": 0.25,
    "5-Coin.clj": 0.1,
    "6-TQQQ-FLT.clj": 0.25,
}
