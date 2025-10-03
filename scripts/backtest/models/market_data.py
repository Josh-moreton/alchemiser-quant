"""Business Unit: shared | Status: current.

Market data models for backtesting system.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class HistoricalBar(BaseModel):
    """Historical OHLCV bar data.
    
    All prices use Decimal for precision. Adjusted close is required for
    accurate backtesting to account for splits and dividends.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    date: datetime = Field(description="Trading date (UTC)")
    symbol: str = Field(description="Trading symbol")
    open_price: Decimal = Field(description="Opening price")
    high_price: Decimal = Field(description="High price")
    low_price: Decimal = Field(description="Low price")
    close_price: Decimal = Field(description="Closing price")
    volume: int = Field(description="Trading volume")
    adjusted_close: Decimal = Field(description="Split/dividend adjusted close")

    def to_dict(self) -> dict[str, str | int]:
        """Convert to dictionary for storage.
        
        Returns:
            Dictionary with string representations for Decimal values

        """
        return {
            "date": self.date.isoformat(),
            "symbol": self.symbol,
            "open": str(self.open_price),
            "high": str(self.high_price),
            "low": str(self.low_price),
            "close": str(self.close_price),
            "volume": self.volume,
            "adjusted_close": str(self.adjusted_close),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | int]) -> HistoricalBar:
        """Create from dictionary.
        
        Args:
            data: Dictionary with bar data
            
        Returns:
            HistoricalBar instance

        """
        return cls(
            date=datetime.fromisoformat(str(data["date"])),
            symbol=str(data["symbol"]),
            open_price=Decimal(str(data["open"])),
            high_price=Decimal(str(data["high"])),
            low_price=Decimal(str(data["low"])),
            close_price=Decimal(str(data["close"])),
            volume=int(data["volume"]),
            adjusted_close=Decimal(str(data["adjusted_close"])),
        )
