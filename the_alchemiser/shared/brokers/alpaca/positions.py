"""Business Unit: shared | Status: current.

Alpaca position management.

Handles position retrieval, liquidation, and position-related operations.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from alpaca.trading.models import Position

from .exceptions import normalize_alpaca_error
from .models import PositionModel

if TYPE_CHECKING:
    from .client import AlpacaClient

logger = logging.getLogger(__name__)


class PositionManager:
    """Manages position information and operations."""

    def __init__(self, client: AlpacaClient) -> None:
        """Initialize with Alpaca client.
        
        Args:
            client: AlpacaClient instance

        """
        self._client = client

    def get_positions(self) -> list[Any]:
        """Get all positions as list of position objects (AccountRepository interface).

        Returns:
            List of position objects with attributes like symbol, qty, market_value, etc.
            
        Raises:
            AlpacaPositionError: If operation fails

        """
        try:
            positions = self._client.trading_client.get_all_positions()
            logger.debug(f"Successfully retrieved {len(positions)} positions")
            # Ensure consistent return type
            return list(positions)
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise normalize_alpaca_error(e, "Get positions") from e

    def get_all_positions(self) -> list[Any]:
        """Alias for `get_positions()` to mirror Alpaca SDK naming.

        Note:
        - Prefer using `get_positions()` throughout the codebase for consistency.
        - This alias exists to reduce confusion for contributors familiar with the SDK.

        Returns:
            List of position objects with attributes like symbol, qty, market_value, etc.

        """
        return self.get_positions()

    def get_positions_dict(self) -> dict[str, float]:
        """Get all positions as dict mapping symbol to quantity.

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.

        """
        # Build symbol->qty mapping from positions
        # Use qty_available to account for shares tied up in open orders
        result: dict[str, float] = {}
        try:
            for pos in self.get_positions():
                symbol = getattr(pos, "symbol", None) or (
                    pos.get("symbol") if isinstance(pos, dict) else None
                )
                # Use qty_available if available, fallback to qty for compatibility
                qty_available = (
                    getattr(pos, "qty_available", None)
                    if not isinstance(pos, dict)
                    else pos.get("qty_available")
                )
                if qty_available is not None:
                    qty_raw = qty_available
                else:
                    # Fallback to total qty if qty_available is not available
                    qty_raw = (
                        getattr(pos, "qty", None) if not isinstance(pos, dict) else pos.get("qty")
                    )

                if symbol and qty_raw is not None:
                    try:
                        result[str(symbol)] = float(qty_raw)
                    except (ValueError, TypeError):
                        continue
        except (KeyError, AttributeError, TypeError):
            # Best-effort mapping; return what we have
            pass
        return result

    def get_current_positions(self) -> dict[str, float]:
        """Get all current positions as dict mapping symbol to quantity.

        This is an alias for get_positions_dict() to satisfy OrderExecutor protocol.

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.

        """
        return self.get_positions_dict()

    def get_position(self, symbol: str) -> Position | None:
        """Get position for a specific symbol.
        
        Args:
            symbol: Symbol to get position for
            
        Returns:
            Position object if found, None otherwise

        """
        try:
            position = self._client.trading_client.get_open_position(symbol)
            logger.debug(f"Successfully retrieved position for {symbol}")
            return position
        except Exception as e:
            logger.debug(f"No position found for {symbol}: {e}")
            return None

    def get_position_model(self, symbol: str) -> PositionModel | None:
        """Get position for a specific symbol as typed model.
        
        Args:
            symbol: Symbol to get position for
            
        Returns:
            PositionModel if found, None otherwise

        """
        position = self.get_position(symbol)
        if not position:
            return None
        
        try:
            return PositionModel(
                symbol=str(getattr(position, "symbol", symbol)),
                qty=self._safe_decimal(getattr(position, "qty", 0)),
                qty_available=self._safe_decimal(getattr(position, "qty_available", None)),
                market_value=self._safe_decimal(getattr(position, "market_value", None)),
                cost_basis=self._safe_decimal(getattr(position, "cost_basis", None)),
                unrealized_pl=self._safe_decimal(getattr(position, "unrealized_pl", None)),
                unrealized_plpc=self._safe_decimal(getattr(position, "unrealized_plpc", None)),
                current_price=self._safe_decimal(getattr(position, "current_price", None)),
                lastday_price=self._safe_decimal(getattr(position, "lastday_price", None)),
                change_today=self._safe_decimal(getattr(position, "change_today", None)),
            )
        except Exception as e:
            logger.error(f"Failed to create position model for {symbol}: {e}")
            return None

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate entire position using close_position API.

        Args:
            symbol: Symbol to liquidate

        Returns:
            Order ID if successful, None if failed.

        """
        try:
            order = self._client.trading_client.close_position(symbol)
            order_id = str(getattr(order, "id", "unknown"))
            logger.info(f"Successfully liquidated position for {symbol}: {order_id}")
            return order_id
        except Exception as e:
            logger.error(f"Failed to liquidate position for {symbol}: {e}")
            return None

    def get_asset_info(self, symbol: str) -> dict[str, Any] | None:
        """Get asset information.

        Args:
            symbol: Stock symbol

        Returns:
            Asset information dictionary, or None if not found.

        """
        try:
            asset = self._client.trading_client.get_asset(symbol)
            if not asset:
                return None
            
            # Convert asset object to dict
            return {
                "id": getattr(asset, "id", None),
                "class": getattr(asset, "asset_class", None),
                "exchange": getattr(asset, "exchange", None),
                "symbol": getattr(asset, "symbol", None),
                "name": getattr(asset, "name", None),
                "status": getattr(asset, "status", None),
                "tradable": getattr(asset, "tradable", None),
                "marginable": getattr(asset, "marginable", None),
                "shortable": getattr(asset, "shortable", None),
                "easy_to_borrow": getattr(asset, "easy_to_borrow", None),
                "fractionable": getattr(asset, "fractionable", None),
            }
        except Exception as e:
            logger.error(f"Failed to get asset info for {symbol}: {e}")
            return None

    def _safe_decimal(self, value: Any) -> Decimal | None:
        """Safely convert value to Decimal.
        
        Args:
            value: Value to convert
            
        Returns:
            Decimal value or None if conversion fails

        """
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None