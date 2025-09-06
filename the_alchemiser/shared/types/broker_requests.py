"""Business Unit: shared | Status: current.

Broker-agnostic request types for trading operations.

This module provides abstractions for order requests that are independent
of specific broker implementations. This allows the rest of the system to
work with trading concepts without being tightly coupled to Alpaca or any
other specific broker API.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from .broker_enums import BrokerOrderSide, BrokerTimeInForce


@dataclass(frozen=True)  
class BrokerMarketOrderRequest:
    """Broker-agnostic market order request."""
    
    symbol: str
    side: BrokerOrderSide
    time_in_force: BrokerTimeInForce
    qty: Decimal | None = None
    notional: Decimal | None = None
    client_order_id: str | None = None
    
    def __post_init__(self) -> None:
        """Validate the market order request."""
        if not self.symbol or not self.symbol.strip():
            raise ValueError("Symbol cannot be empty")
        
        if not isinstance(self.side, BrokerOrderSide):
            raise ValueError("Side must be a BrokerOrderSide")
            
        if not isinstance(self.time_in_force, BrokerTimeInForce):
            raise ValueError("Time in force must be a BrokerTimeInForce")
        
        # Must specify either qty or notional, but not both
        if self.qty is None and self.notional is None:
            raise ValueError("Must specify either qty or notional")
        
        if self.qty is not None and self.notional is not None:
            raise ValueError("Cannot specify both qty and notional")
            
        if self.qty is not None and self.qty <= 0:
            raise ValueError("Quantity must be positive")
            
        if self.notional is not None and self.notional <= 0:
            raise ValueError("Notional must be positive")


@dataclass(frozen=True)
class BrokerLimitOrderRequest:
    """Broker-agnostic limit order request."""
    
    symbol: str
    side: BrokerOrderSide
    time_in_force: BrokerTimeInForce
    qty: Decimal
    limit_price: Decimal
    client_order_id: str | None = None
    
    def __post_init__(self) -> None:
        """Validate the limit order request."""
        if not self.symbol or not self.symbol.strip():
            raise ValueError("Symbol cannot be empty")
        
        if not isinstance(self.side, BrokerOrderSide):
            raise ValueError("Side must be a BrokerOrderSide")
            
        if not isinstance(self.time_in_force, BrokerTimeInForce):
            raise ValueError("Time in force must be a BrokerTimeInForce")
        
        if self.qty <= 0:
            raise ValueError("Quantity must be positive")
            
        if self.limit_price <= 0:
            raise ValueError("Limit price must be positive")


class BrokerRequestConverter(Protocol):
    """Protocol for converting broker-agnostic requests to specific broker requests."""
    
    def to_market_order(self, request: BrokerMarketOrderRequest) -> Any:
        """Convert to broker-specific market order request."""
        ...
    
    def to_limit_order(self, request: BrokerLimitOrderRequest) -> Any:
        """Convert to broker-specific limit order request."""
        ...


class AlpacaRequestConverter:
    """Converter for Alpaca-specific order requests."""
    
    @staticmethod
    def to_market_order(request: BrokerMarketOrderRequest) -> Any:
        """Convert BrokerMarketOrderRequest to Alpaca MarketOrderRequest."""
        from alpaca.trading.requests import MarketOrderRequest
        
        kwargs = {
            "symbol": request.symbol,
            "side": request.side.to_alpaca(),
            "time_in_force": request.time_in_force.to_alpaca(),
        }
        
        if request.client_order_id:
            kwargs["client_order_id"] = request.client_order_id
            
        if request.qty is not None:
            kwargs["qty"] = float(request.qty)
        else:
            kwargs["notional"] = float(request.notional)
            
        return MarketOrderRequest(**kwargs)
    
    @staticmethod
    def to_limit_order(request: BrokerLimitOrderRequest) -> Any:
        """Convert BrokerLimitOrderRequest to Alpaca LimitOrderRequest."""
        from alpaca.trading.requests import LimitOrderRequest
        
        kwargs = {
            "symbol": request.symbol,
            "side": request.side.to_alpaca(),
            "time_in_force": request.time_in_force.to_alpaca(),
            "qty": float(request.qty),
            "limit_price": float(request.limit_price),
        }
        
        if request.client_order_id:
            kwargs["client_order_id"] = request.client_order_id
            
        return LimitOrderRequest(**kwargs)


__all__ = [
    "BrokerMarketOrderRequest", 
    "BrokerLimitOrderRequest",
    "BrokerRequestConverter",
    "AlpacaRequestConverter",
]