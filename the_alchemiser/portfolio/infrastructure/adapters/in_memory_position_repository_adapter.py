"""Business Unit: portfolio assessment & management | Status: current

In-memory position repository adapter for smoke validation.

TODO: Replace with production database adapter (e.g., DynamoDB, PostgreSQL)
FIXME: This simplified adapter only stores positions in memory
"""

from collections.abc import Sequence

from the_alchemiser.portfolio.application.ports import PositionRepositoryPort
from the_alchemiser.portfolio.domain.entities.position import Position
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol


class InMemoryPositionRepositoryAdapter(PositionRepositoryPort):
    """Simple in-memory position repository for smoke validation.

    TODO: Replace with production database implementation
    FIXME: No persistence or concurrent access handling in current implementation
    """

    def __init__(self) -> None:
        self._positions: dict[str, Position] = {}

    def load_positions(self) -> Sequence[Position]:
        """Load all current position holdings.

        Returns:
            Sequence of Position entities representing current holdings

        """
        return list(self._positions.values())

    def save_positions(self, positions: Sequence[Position]) -> None:
        """Atomically persist position updates.

        Args:
            positions: Complete set of positions to persist

        """
        # Clear existing positions and save new ones
        self._positions.clear()
        for position in positions:
            self._positions[position.symbol.value] = position

    def get_position(self, symbol: Symbol) -> Position | None:
        """Get specific position by symbol.

        Args:
            symbol: Symbol to lookup

        Returns:
            Position if held, None if no position

        """
        return self._positions.get(symbol.value)

    def add_position(self, position: Position) -> None:
        """Add a position to the repository (helper for smoke validation).

        Args:
            position: Position to add

        TODO: Remove this method in production - only needed for smoke validation setup

        """
        self._positions[position.symbol.value] = position

    def clear_positions(self) -> None:
        """Clear all positions (for smoke validation purposes).

        TODO: Remove this method in production - only needed for smoke validation
        """
        self._positions.clear()
