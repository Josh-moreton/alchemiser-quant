"""Business Unit: shared | Status: current.

Stale quote garbage collection and memory management.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .data_store import PricingDataStore

logger = logging.getLogger(__name__)


class QuoteCleanupManager:
    """Manages periodic cleanup of stale quotes to prevent memory bloat."""

    def __init__(
        self,
        data_store: PricingDataStore,
        cleanup_interval: int = 60,
        max_quote_age: int = 300,
    ) -> None:
        """Initialize cleanup manager.
        
        Args:
            data_store: Data store to clean up
            cleanup_interval: Seconds between cleanup cycles
            max_quote_age: Maximum age of quotes in seconds

        """
        self._data_store = data_store
        self._cleanup_interval = cleanup_interval
        self._max_quote_age = max_quote_age
        self._cleanup_task: asyncio.Task[None] | None = None
        self._should_cleanup = False

    def start_cleanup(self) -> None:
        """Start the periodic cleanup task."""
        if self._cleanup_task is not None and not self._cleanup_task.done():
            logger.warning("Cleanup task already running")
            return

        self._should_cleanup = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"📚 Started quote cleanup (interval: {self._cleanup_interval}s, max_age: {self._max_quote_age}s)")

    def stop_cleanup(self) -> None:
        """Stop the periodic cleanup task."""
        self._should_cleanup = False
        if self._cleanup_task is not None and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        logger.info("📚 Stopped quote cleanup")

    async def _cleanup_loop(self) -> None:
        """Run main cleanup loop in background."""
        while self._should_cleanup:
            try:
                await asyncio.sleep(self._cleanup_interval)
                
                if not self._should_cleanup:
                    break
                
                # Perform cleanup in thread to avoid blocking
                removed_count = await asyncio.to_thread(
                    self._data_store.cleanup_old_quotes, 
                    self._max_quote_age
                )
                
                if removed_count > 0:
                    logger.debug(f"📚 Cleaned up {removed_count} old quotes")
                    
            except asyncio.CancelledError:
                logger.debug("Quote cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in quote cleanup: {e}", exc_info=True)
                # Continue running despite errors
                await asyncio.sleep(1)

    def force_cleanup(self) -> int:
        """Force immediate cleanup and return number of quotes removed.
        
        Returns:
            Number of quotes removed

        """
        removed_count = self._data_store.cleanup_old_quotes(self._max_quote_age)
        if removed_count > 0:
            logger.info(f"📚 Force cleanup removed {removed_count} old quotes")
        return removed_count

    def update_settings(self, cleanup_interval: int | None = None, max_quote_age: int | None = None) -> None:
        """Update cleanup settings.
        
        Args:
            cleanup_interval: New cleanup interval in seconds
            max_quote_age: New maximum quote age in seconds

        """
        if cleanup_interval is not None:
            self._cleanup_interval = cleanup_interval
            logger.info(f"📚 Updated cleanup interval to {cleanup_interval}s")
            
        if max_quote_age is not None:
            self._max_quote_age = max_quote_age
            logger.info(f"📚 Updated max quote age to {max_quote_age}s")

    def get_settings(self) -> dict[str, int]:
        """Get current cleanup settings.
        
        Returns:
            Dictionary with current settings

        """
        return {
            "cleanup_interval": self._cleanup_interval,
            "max_quote_age": self._max_quote_age,
        }