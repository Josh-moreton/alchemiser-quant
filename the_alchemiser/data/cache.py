"""Parquet cache management stubs."""

from pathlib import Path


class DataCache:
    """Placeholder for a Parquet-backed data cache."""

    def __init__(self, root: Path) -> None:  # pragma: no cover - stub
        self.root = root

    def get(self, symbol: str) -> Path:  # pragma: no cover - stub
        """Return path to cached data for *symbol*."""
        raise NotImplementedError("Parquet caching not yet implemented")
