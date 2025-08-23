"""Tests for application trading ports module.

Validates that protocols can be implemented and used correctly.
"""

from decimal import Decimal
from datetime import datetime
from typing import Sequence, Iterable
import pytest

from the_alchemiser.application.trading.ports import (
    MarketDataPort,
    AccountReadPort,
    OrderExecutionPort,
    StrategyAdapterPort,
    RebalancingOrchestratorPort,
)
from the_alchemiser.domain.shared_kernel.value_objects.symbol import Symbol
from the_alchemiser.domain.trading.entities.order import Order
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal


class MockAccountReadPort:
    """Mock implementation of AccountReadPort for testing."""
    
    def get_cash(self) -> Decimal:
        return Decimal("10000.00")
    
    def get_positions(self) -> Sequence[Order]:
        return []
    
    def get_equity(self) -> Decimal:
        return Decimal("50000.00")
    
    def get_buying_power(self) -> Decimal:
        return Decimal("25000.00")


class MockOrderExecutionPort:
    """Mock implementation of OrderExecutionPort for testing."""
    
    def submit_orders(self, orders: Sequence[Order]) -> list[Order]:
        # Return orders with filled status for testing
        return list(orders)
    
    def cancel_open_orders(self, symbols: Iterable[Symbol]) -> None:
        pass


class MockStrategyAdapterPort:
    """Mock implementation of StrategyAdapterPort for testing."""
    
    def generate_signals(self, now: datetime) -> list[StrategySignal]:
        return []


class MockRebalancingOrchestratorPort:
    """Mock implementation of RebalancingOrchestratorPort for testing."""
    
    def execute_rebalance_cycle(self, now: datetime) -> None:
        pass
    
    def dry_run(self, now: datetime) -> dict[str, float]:
        return {"AAPL": 0.5, "MSFT": 0.5}


def test_account_read_port_implementation():
    """Test that AccountReadPort can be implemented and used."""
    port = MockAccountReadPort()
    
    # Test protocol compliance
    assert isinstance(port, AccountReadPort)
    
    # Test method calls
    assert port.get_cash() == Decimal("10000.00")
    assert port.get_equity() == Decimal("50000.00")
    assert port.get_buying_power() == Decimal("25000.00")
    assert isinstance(port.get_positions(), Sequence)


def test_order_execution_port_implementation():
    """Test that OrderExecutionPort can be implemented and used."""
    port = MockOrderExecutionPort()
    
    # Test protocol compliance
    assert isinstance(port, OrderExecutionPort)
    
    # Test method calls don't raise errors
    port.submit_orders([])
    port.cancel_open_orders([Symbol("AAPL")])


def test_strategy_adapter_port_implementation():
    """Test that StrategyAdapterPort can be implemented and used."""
    port = MockStrategyAdapterPort()
    
    # Test protocol compliance
    assert isinstance(port, StrategyAdapterPort)
    
    # Test method call
    signals = port.generate_signals(datetime.now())
    assert isinstance(signals, list)


def test_rebalancing_orchestrator_port_implementation():
    """Test that RebalancingOrchestratorPort can be implemented and used."""
    port = MockRebalancingOrchestratorPort()
    
    # Test protocol compliance
    assert isinstance(port, RebalancingOrchestratorPort)
    
    # Test method calls
    port.execute_rebalance_cycle(datetime.now())
    preview = port.dry_run(datetime.now())
    assert isinstance(preview, dict)
    assert "AAPL" in preview


def test_market_data_port_reexport():
    """Test that MarketDataPort is properly re-exported."""
    # This should be the canonical port from domain/market_data
    from the_alchemiser.application.trading.ports import MarketDataPort as PortsMarketDataPort
    from the_alchemiser.domain.market_data.protocols.market_data_port import MarketDataPort as CanonicalMarketDataPort
    
    # Should be the same class
    assert PortsMarketDataPort is CanonicalMarketDataPort


def test_ports_module_exports():
    """Test that all expected ports are exported."""
    from the_alchemiser.application.trading.ports import __all__
    
    expected_ports = [
        "MarketDataPort",
        "AccountReadPort", 
        "OrderExecutionPort",
        "StrategyAdapterPort",
        "RebalancingOrchestratorPort",
        "ReportingPort",
    ]
    
    for port in expected_ports:
        assert port in __all__