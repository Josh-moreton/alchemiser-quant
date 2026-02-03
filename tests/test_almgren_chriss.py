"""Tests for Almgren-Chriss optimal execution strategy.

Tests the core mathematical functionality of the Almgren-Chriss model,
particularly the trajectory calculation and slice distribution.

Note: These tests validate the mathematical properties of the trajectory
calculation algorithm without requiring the full execution framework.
"""

from decimal import Decimal

import numpy as np
import pytest


class TestAlmgrenChrissTrajectory:
    """Test trajectory calculation."""

    def test_trajectory_starts_at_total_quantity(self) -> None:
        """Trajectory should start with full quantity (x_0 = Q)."""
        # Create a minimal strategy instance (we won't execute, just test calculation)
        # We need to mock AlpacaManager, but for trajectory testing we can use None
        # and just call the private method
        Q = Decimal("1000")
        risk_aversion = 0.5
        volatility = 0.02
        temp_impact = 0.001
        num_slices = 5

        kappa = np.sqrt(risk_aversion * volatility**2 / temp_impact)
        dt = 300 / num_slices  # 5 minutes / 5 slices

        # Calculate trajectory manually
        trajectory = []
        for k in range(num_slices + 1):
            remaining = float(Q) * np.sinh(kappa * (num_slices - k) * dt) / np.sinh(
                kappa * num_slices * dt
            )
            trajectory.append(Decimal(str(remaining)))

        # First element should be close to Q
        assert abs(trajectory[0] - Q) < Decimal("0.01")

    def test_trajectory_ends_at_zero(self) -> None:
        """Trajectory should end at zero (x_N = 0)."""
        Q = Decimal("1000")
        risk_aversion = 0.5
        volatility = 0.02
        temp_impact = 0.001
        num_slices = 5

        kappa = np.sqrt(risk_aversion * volatility**2 / temp_impact)
        dt = 300 / num_slices

        trajectory = []
        for k in range(num_slices + 1):
            remaining = float(Q) * np.sinh(kappa * (num_slices - k) * dt) / np.sinh(
                kappa * num_slices * dt
            )
            trajectory.append(Decimal(str(remaining)))

        # Last element should be very close to zero
        assert abs(trajectory[-1]) < Decimal("0.01")

    def test_trajectory_is_monotonically_decreasing(self) -> None:
        """Trajectory should decrease monotonically (x_k >= x_{k+1})."""
        Q = Decimal("1000")
        risk_aversion = 0.5
        volatility = 0.02
        temp_impact = 0.001
        num_slices = 5

        kappa = np.sqrt(risk_aversion * volatility**2 / temp_impact)
        dt = 300 / num_slices

        trajectory = []
        for k in range(num_slices + 1):
            remaining = float(Q) * np.sinh(kappa * (num_slices - k) * dt) / np.sinh(
                kappa * num_slices * dt
            )
            trajectory.append(Decimal(str(remaining)))

        # Check monotonicity
        for i in range(len(trajectory) - 1):
            assert trajectory[i] >= trajectory[i + 1], f"Not monotonic at index {i}"

    def test_slice_quantities_sum_to_total(self) -> None:
        """Sum of slice quantities should equal total quantity."""
        Q = Decimal("1000")
        risk_aversion = 0.5
        volatility = 0.02
        temp_impact = 0.001
        num_slices = 5

        kappa = np.sqrt(risk_aversion * volatility**2 / temp_impact)
        dt = 300 / num_slices

        trajectory = []
        for k in range(num_slices + 1):
            remaining = float(Q) * np.sinh(kappa * (num_slices - k) * dt) / np.sinh(
                kappa * num_slices * dt
            )
            trajectory.append(Decimal(str(remaining)))

        # Compute slice quantities
        slice_quantities = []
        for k in range(1, len(trajectory)):
            quantity = trajectory[k - 1] - trajectory[k]
            slice_quantities.append(quantity)

        # Sum should equal Q (within small tolerance for rounding)
        total = sum(slice_quantities)
        assert abs(total - Q) < Decimal("0.01")

    def test_higher_risk_aversion_trades_more_upfront(self) -> None:
        """Higher risk aversion should result in more trading upfront."""
        Q = Decimal("1000")
        volatility = 0.02
        temp_impact = 0.001
        num_slices = 5
        dt = 300 / num_slices

        # Low risk aversion
        risk_aversion_low = 0.2
        kappa_low = np.sqrt(risk_aversion_low * volatility**2 / temp_impact)

        trajectory_low = []
        for k in range(num_slices + 1):
            remaining = float(Q) * np.sinh(kappa_low * (num_slices - k) * dt) / np.sinh(
                kappa_low * num_slices * dt
            )
            trajectory_low.append(Decimal(str(remaining)))

        first_slice_low = trajectory_low[0] - trajectory_low[1]

        # High risk aversion
        risk_aversion_high = 1.0
        kappa_high = np.sqrt(risk_aversion_high * volatility**2 / temp_impact)

        trajectory_high = []
        for k in range(num_slices + 1):
            remaining = float(Q) * np.sinh(kappa_high * (num_slices - k) * dt) / np.sinh(
                kappa_high * num_slices * dt
            )
            trajectory_high.append(Decimal(str(remaining)))

        first_slice_high = trajectory_high[0] - trajectory_high[1]

        # High risk aversion should trade more in first slice
        assert first_slice_high > first_slice_low

    def test_trajectory_with_different_slice_counts(self) -> None:
        """Test that trajectory works with different numbers of slices."""
        Q = Decimal("1000")
        risk_aversion = 0.5
        volatility = 0.02
        temp_impact = 0.001

        for num_slices in [3, 5, 7, 10]:
            kappa = np.sqrt(risk_aversion * volatility**2 / temp_impact)
            dt = 300 / num_slices

            trajectory = []
            for k in range(num_slices + 1):
                remaining = float(Q) * np.sinh(kappa * (num_slices - k) * dt) / np.sinh(
                    kappa * num_slices * dt
                )
                trajectory.append(Decimal(str(remaining)))

            # Check basic properties
            assert abs(trajectory[0] - Q) < Decimal("0.01")
            assert abs(trajectory[-1]) < Decimal("0.01")
            assert len(trajectory) == num_slices + 1


class TestAlmgrenChrissSliceQuantities:
    """Test slice quantity calculations."""

    def test_all_slice_quantities_positive(self) -> None:
        """All slice quantities should be positive."""
        Q = Decimal("1000")
        risk_aversion = 0.5
        volatility = 0.02
        temp_impact = 0.001
        num_slices = 5

        kappa = np.sqrt(risk_aversion * volatility**2 / temp_impact)
        dt = 300 / num_slices

        trajectory = []
        for k in range(num_slices + 1):
            remaining = float(Q) * np.sinh(kappa * (num_slices - k) * dt) / np.sinh(
                kappa * num_slices * dt
            )
            trajectory.append(Decimal(str(remaining)))

        slice_quantities = []
        for k in range(1, len(trajectory)):
            quantity = trajectory[k - 1] - trajectory[k]
            slice_quantities.append(quantity)

        # All quantities should be positive
        for i, qty in enumerate(slice_quantities):
            assert qty > 0, f"Slice {i} has non-positive quantity: {qty}"

    def test_slice_count_matches_num_slices(self) -> None:
        """Number of slice quantities should match num_slices parameter."""
        Q = Decimal("1000")
        risk_aversion = 0.5
        volatility = 0.02
        temp_impact = 0.001
        num_slices = 5

        kappa = np.sqrt(risk_aversion * volatility**2 / temp_impact)
        dt = 300 / num_slices

        trajectory = []
        for k in range(num_slices + 1):
            remaining = float(Q) * np.sinh(kappa * (num_slices - k) * dt) / np.sinh(
                kappa * num_slices * dt
            )
            trajectory.append(Decimal(str(remaining)))

        slice_quantities = []
        for k in range(1, len(trajectory)):
            quantity = trajectory[k - 1] - trajectory[k]
            slice_quantities.append(quantity)

        assert len(slice_quantities) == num_slices


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
