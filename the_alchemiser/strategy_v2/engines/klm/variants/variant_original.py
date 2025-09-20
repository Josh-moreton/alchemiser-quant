"""Business Unit: strategy | Status: current

Original KLM strategy - exact match to CLJ implementation.
"""

from typing import Any

from the_alchemiser.strategy_v2.engines.klm.base_variant import BaseKLMVariant


class KlmVariantOriginal(BaseKLMVariant):
    """Original KLM variant - exact match to 'Simons KMLM switcher (single pops)'.

    This is the EXACT implementation of the original CLJ strategy:
    - Simons KMLM switcher (single pops)| BT 4/13/22 = A.R. 466% / D.D. 22% V2
    - Specific RSI thresholds per symbol (not uniform)
    - Nested if-else structure preserved in logic flow
    - Original KMLM Switcher with select-bottom 2 and select-top 1
    """

    def get_overbought_config(self) -> dict[str, Any]:
        """Overbought detection with EXACT thresholds from CLJ.

        Note: Different thresholds for XLP (75), XLY (80), FAS (80), SPY (80).
        """
        return {
            "symbols": [
                ("QQQE", 79),
                ("VTV", 79),
                ("VOX", 79),
                ("TECL", 79),
                ("VOOG", 79),
                ("VOOV", 79),
                ("XLP", 75),  # Different threshold: 75 not 79
                ("TQQQ", 79),
                ("XLY", 80),  # Different threshold: 80 not 79
                ("FAS", 80),  # Different threshold: 80 not 79
                ("SPY", 80),  # Different threshold: 80 not 79
            ],
            "hedge_symbol": "UVXY",
            "rsi_window": 10,
        }

    def get_combined_pop_config(self) -> dict[str, Any]:
        """Combined Pop Bot with EXACT thresholds from CLJ.

        Note: LABU has different threshold (25) vs others (30).
        """
        return {
            "pops": [
                {"symbol": "TQQQ", "target": "TECL", "threshold": 30},
                {"symbol": "SOXL", "target": "SOXL", "threshold": 30},
                {"symbol": "SPXL", "target": "SPXL", "threshold": 30},
                {
                    "symbol": "LABU",
                    "target": "LABU",
                    "threshold": 25,
                },  # Different threshold: 25 not 30
            ],
            "rsi_window": 10,
        }

    def get_kmlm_switcher_config(self) -> dict[str, Any]:
        """KMLM Switcher - exact CLJ implementation.

        When XLK RSI > KMLM RSI:
        - Select bottom 2 from [TECL, SOXL, SVIX]
        Otherwise (L/S Rotator):
        - Select top 1 from [SQQQ, TLT]
        """
        return {
            "compare_symbols": ("XLK", "KMLM"),
            "tech_symbols": ["TECL", "SOXL", "SVIX"],
            "ls_symbols": ["SQQQ", "TLT"],
            "rsi_window": 10,
            "selection": {
                "tech": ("bottom", 2),  # select-bottom 2
                "ls": ("top", 1),  # select-top 1
            },
        }

    def get_variant_name(self) -> str:
        """Return variant name."""
        return "Original_CLJ"

    def get_description(self) -> str:
        """Return variant description."""
        return (
            "Simons KMLM switcher (single pops) | BT 4/13/22 = A.R. 466% / D.D. 22% V2"
        )

    def has_single_popped_kmlm(self) -> bool:
        """Original strategy does NOT have Single Popped KMLM logic."""
        return False

    def has_bond_check(self) -> bool:
        """Original strategy does NOT have Bond Check logic."""
        return False

    def get_scale_in_config(self) -> dict[str, Any] | None:
        """Original strategy does NOT have scale-in logic."""
        return None
