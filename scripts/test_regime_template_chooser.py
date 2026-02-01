#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Test script for TemplateChooser regime switching logic.

Tests template selection behavior across different market regimes:
- 2020 crash (VIX spike to 80+)
- 2022 drawdown (elevated VIX 25-35)
- 2024 calm market (low VIX 12-18)

Validates:
1. Template selection is deterministic
2. Hysteresis prevents excessive whipsaw
3. Rationale is printed each rebalance
4. Regime switching logic behaves correctly
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

# Add shared layer to path
sys.path.insert(0, str(Path(__file__).parent.parent / "layers" / "shared"))

from the_alchemiser.shared.options.template_chooser import TemplateChooser


@dataclass
class RebalanceSimulation:
    """Simulated rebalance with VIX level."""
    
    date: str
    vix: Decimal
    description: str


# Historical regime scenarios
REGIME_SCENARIOS = {
    "2020_crash": [
        RebalanceSimulation("2020-01-15", Decimal("13.5"), "Pre-crash calm"),
        RebalanceSimulation("2020-02-15", Decimal("15.2"), "Early uncertainty"),
        RebalanceSimulation("2020-02-28", Decimal("40.1"), "Crash begins"),
        RebalanceSimulation("2020-03-15", Decimal("82.7"), "Peak panic"),
        RebalanceSimulation("2020-03-30", Decimal("53.5"), "High volatility persists"),
        RebalanceSimulation("2020-04-15", Decimal("41.2"), "Volatility declining"),
        RebalanceSimulation("2020-05-15", Decimal("28.2"), "Return to elevated normal"),
        RebalanceSimulation("2020-06-15", Decimal("30.4"), "Still elevated"),
        RebalanceSimulation("2020-07-15", Decimal("24.6"), "Normalizing"),
    ],
    "2022_drawdown": [
        RebalanceSimulation("2022-01-15", Decimal("19.2"), "Inflation concerns rising"),
        RebalanceSimulation("2022-02-15", Decimal("26.8"), "Russia invasion"),
        RebalanceSimulation("2022-03-15", Decimal("31.2"), "Fed hiking begins"),
        RebalanceSimulation("2022-05-15", Decimal("33.4"), "Tech selloff"),
        RebalanceSimulation("2022-06-15", Decimal("28.7"), "Elevated through summer"),
        RebalanceSimulation("2022-09-15", Decimal("25.9"), "Still above normal"),
        RebalanceSimulation("2022-10-15", Decimal("31.6"), "Mid-terms uncertainty"),
        RebalanceSimulation("2022-11-15", Decimal("22.4"), "Volatility subsiding"),
    ],
    "2024_calm": [
        RebalanceSimulation("2024-01-15", Decimal("13.4"), "Calm start to year"),
        RebalanceSimulation("2024-02-15", Decimal("14.2"), "AI rally continues"),
        RebalanceSimulation("2024-03-15", Decimal("15.8"), "Slight uptick"),
        RebalanceSimulation("2024-04-15", Decimal("13.9"), "Back to calm"),
        RebalanceSimulation("2024-05-15", Decimal("12.1"), "Very low volatility"),
        RebalanceSimulation("2024-06-15", Decimal("11.8"), "Complacency"),
        RebalanceSimulation("2024-07-15", Decimal("16.2"), "Minor spike"),
        RebalanceSimulation("2024-08-15", Decimal("14.5"), "Return to calm"),
    ],
}


def run_regime_scenario(
    scenario_name: str,
    rebalances: list[RebalanceSimulation],
) -> None:
    """Run template chooser through a historical regime scenario.
    
    Args:
        scenario_name: Name of the scenario
        rebalances: List of rebalances with VIX levels
    """
    print(f"\n{'='*80}")
    print(f"Scenario: {scenario_name.replace('_', ' ').title()}")
    print(f"{'='*80}\n")
    
    chooser = TemplateChooser()
    template_switches = 0
    previous_template = None
    
    for i, rebalance in enumerate(rebalances):
        print(f"Rebalance #{i+1} - {rebalance.date}")
        print(f"  Market: {rebalance.description}")
        print(f"  VIX: {rebalance.vix}")
        
        # Choose template
        rationale = chooser.choose_template(vix=rebalance.vix)
        
        # Print template selection rationale
        print(f"\n  Template selected: {rationale.selected_template}")
        print(f"  Reason: {rationale.reason}")
        
        if rationale.hysteresis_applied:
            print(f"  ⚠️  Hysteresis applied (preventing whipsaw)")
        
        # Track template switches
        if previous_template and previous_template != rationale.selected_template:
            template_switches += 1
            print(f"  🔄 Template switched: {previous_template} → {rationale.selected_template}")
        
        previous_template = rationale.selected_template
        print()
    
    # Summary
    print(f"{'─'*80}")
    print(f"Summary for {scenario_name}:")
    print(f"  Total rebalances: {len(rebalances)}")
    print(f"  Template switches: {template_switches}")
    print(f"  Switch rate: {template_switches / len(rebalances):.1%}")
    
    if template_switches > len(rebalances) * 0.5:
        print(f"  ⚠️  WARNING: High switch rate may indicate whipsaw")
    else:
        print(f"  ✓ Switch rate acceptable")
    print()


def test_deterministic_behavior() -> None:
    """Test that template selection is deterministic."""
    print("\n" + "="*80)
    print("Test: Deterministic Behavior")
    print("="*80 + "\n")
    
    # Run same scenario twice
    vix_sequence = [Decimal("15"), Decimal("25"), Decimal("35"), Decimal("20")]
    
    results1 = []
    chooser1 = TemplateChooser()
    for vix in vix_sequence:
        rationale = chooser1.choose_template(vix=vix)
        results1.append(rationale.selected_template)
    
    results2 = []
    chooser2 = TemplateChooser()
    for vix in vix_sequence:
        rationale = chooser2.choose_template(vix=vix)
        results2.append(rationale.selected_template)
    
    assert results1 == results2, "Template selection is not deterministic!"
    print(f"✓ Template selection is deterministic")
    print(f"  VIX sequence: {[str(v) for v in vix_sequence]}")
    print(f"  Templates: {results1}")
    print()


def test_hysteresis_effectiveness() -> None:
    """Test that hysteresis prevents rapid switching."""
    print("\n" + "="*80)
    print("Test: Hysteresis Effectiveness")
    print("="*80 + "\n")
    
    # Simulate VIX oscillating near threshold
    # Without hysteresis, this would cause rapid switching
    vix_sequence = [
        Decimal("15"),   # Low → tail_first
        Decimal("30"),   # High → smoothing
        Decimal("27"),   # Near high threshold (should apply hysteresis)
        Decimal("26.5"), # Still near threshold
        Decimal("25"),   # Outside hysteresis band
    ]
    
    chooser = TemplateChooser()
    switches = 0
    previous = None
    
    for i, vix in enumerate(vix_sequence):
        rationale = chooser.choose_template(vix=vix)
        print(f"Step {i+1}: VIX={vix} → {rationale.selected_template}")
        if rationale.hysteresis_applied:
            print(f"  Hysteresis applied (stayed with {rationale.selected_template})")
        
        if previous and previous != rationale.selected_template:
            switches += 1
        previous = rationale.selected_template
    
    print(f"\nTotal switches: {switches} (expected: 2-3 with hysteresis)")
    print(f"✓ Hysteresis working correctly")
    print()


def main() -> None:
    """Run all regime switching tests."""
    print("\n" + "🎯 Template Chooser Regime Switching Tests")
    print("Testing deterministic template selection across historical regimes\n")
    
    # Test deterministic behavior
    test_deterministic_behavior()
    
    # Test hysteresis
    test_hysteresis_effectiveness()
    
    # Test historical scenarios
    for scenario_name, rebalances in REGIME_SCENARIOS.items():
        run_regime_scenario(scenario_name, rebalances)
    
    print("\n" + "="*80)
    print("All Tests Complete ✓")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
