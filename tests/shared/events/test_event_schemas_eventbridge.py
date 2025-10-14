#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for event schema EventBridge deserialization validators.

This test module validates that event schemas can properly deserialize
from EventBridge JSON where Decimal and datetime fields are serialized as strings.
"""

# ruff: noqa: S101  # Allow asserts in tests

from decimal import Decimal

import pytest

from the_alchemiser.shared.events.schemas import (
    AllocationComparisonCompleted,
    BulkSettlementCompleted,
    OrderSettlementCompleted,
    TradingNotificationRequested,
)


class TestAllocationComparisonCompletedEventBridge:
    """Test AllocationComparisonCompleted EventBridge deserialization."""

    @pytest.mark.unit
    def test_eventbridge_string_deserialization(self):
        """Test deserialization from EventBridge JSON with string Decimal values."""
        event_data = {
            "event_id": "evt-123",
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "source_module": "test",
            "timestamp": "2025-01-06T12:30:45+00:00",
            "event_type": "AllocationComparisonCompleted",
            "schema_version": "1.0",
            # EventBridge serializes Decimal to strings
            "target_allocations": {"AAPL": "0.6", "GOOGL": "0.4"},
            "current_allocations": {"AAPL": "0.5", "GOOGL": "0.5"},
            "allocation_differences": {"AAPL": "0.1", "GOOGL": "-0.1"},
            "rebalancing_required": True,
            "comparison_metadata": {},
        }

        event = AllocationComparisonCompleted.model_validate(event_data)

        assert event.target_allocations["AAPL"] == Decimal("0.6")
        assert event.current_allocations["AAPL"] == Decimal("0.5")
        assert event.allocation_differences["AAPL"] == Decimal("0.1")

    @pytest.mark.unit
    def test_eventbridge_z_suffix_timestamp(self):
        """Test handling of 'Z' suffix in timestamp from EventBridge."""
        event_data = {
            "event_id": "evt-123",
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "source_module": "test",
            "timestamp": "2025-01-06T12:30:45Z",  # Z suffix
            "event_type": "AllocationComparisonCompleted",
            "target_allocations": {"AAPL": "0.6"},
            "current_allocations": {"AAPL": "0.5"},
            "allocation_differences": {"AAPL": "0.1"},
            "rebalancing_required": True,
        }

        event = AllocationComparisonCompleted.model_validate(event_data)

        assert event.timestamp.tzinfo is not None

    @pytest.mark.unit
    def test_eventbridge_numeric_values(self):
        """Test handling of numeric values (edge case)."""
        event_data = {
            "event_id": "evt-123",
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "source_module": "test",
            "timestamp": "2025-01-06T12:30:45+00:00",
            "event_type": "AllocationComparisonCompleted",
            # Numeric types instead of strings
            "target_allocations": {"AAPL": 0.6, "GOOGL": 0.4},
            "current_allocations": {"AAPL": 0.5, "GOOGL": 0.5},
            "allocation_differences": {"AAPL": 0.1, "GOOGL": -0.1},
            "rebalancing_required": True,
        }

        event = AllocationComparisonCompleted.model_validate(event_data)

        assert event.target_allocations["AAPL"] == Decimal("0.6")


class TestOrderSettlementCompletedEventBridge:
    """Test OrderSettlementCompleted EventBridge deserialization."""

    @pytest.mark.unit
    def test_eventbridge_string_deserialization(self):
        """Test deserialization from EventBridge JSON with string Decimal values."""
        event_data = {
            "event_id": "evt-123",
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "source_module": "test",
            "timestamp": "2025-01-06T12:30:45+00:00",
            "event_type": "OrderSettlementCompleted",
            "schema_version": "1.0",
            "order_id": "order-123",
            "symbol": "AAPL",
            "side": "BUY",
            # EventBridge serializes Decimal to strings
            "settled_quantity": "10.0",
            "settlement_price": "150.50",
            "settled_value": "1505.00",
            "buying_power_released": "0.0",
        }

        event = OrderSettlementCompleted.model_validate(event_data)

        assert event.settled_quantity == Decimal("10.0")
        assert event.settlement_price == Decimal("150.50")
        assert event.settled_value == Decimal("1505.00")
        assert event.buying_power_released == Decimal("0.0")

    @pytest.mark.unit
    def test_eventbridge_numeric_values(self):
        """Test handling of numeric values (edge case)."""
        event_data = {
            "event_id": "evt-123",
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "source_module": "test",
            "timestamp": "2025-01-06T12:30:45+00:00",
            "event_type": "OrderSettlementCompleted",
            "order_id": "order-123",
            "symbol": "AAPL",
            "side": "BUY",
            # Numeric types
            "settled_quantity": 10,
            "settlement_price": 150.5,
            "settled_value": 1505.0,
            "buying_power_released": 0,
        }

        event = OrderSettlementCompleted.model_validate(event_data)

        assert event.settled_quantity == Decimal("10")
        assert event.settlement_price == Decimal("150.5")


class TestBulkSettlementCompletedEventBridge:
    """Test BulkSettlementCompleted EventBridge deserialization."""

    @pytest.mark.unit
    def test_eventbridge_string_deserialization(self):
        """Test deserialization from EventBridge JSON with string Decimal value."""
        event_data = {
            "event_id": "evt-123",
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "source_module": "test",
            "timestamp": "2025-01-06T12:30:45+00:00",
            "event_type": "BulkSettlementCompleted",
            "schema_version": "1.0",
            "settled_order_ids": ["order-1", "order-2"],
            # EventBridge serializes Decimal to string
            "total_buying_power_released": "5000.00",
            "settlement_details": {},
        }

        event = BulkSettlementCompleted.model_validate(event_data)

        assert event.total_buying_power_released == Decimal("5000.00")

    @pytest.mark.unit
    def test_eventbridge_numeric_value(self):
        """Test handling of numeric value (edge case)."""
        event_data = {
            "event_id": "evt-123",
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "source_module": "test",
            "timestamp": "2025-01-06T12:30:45+00:00",
            "event_type": "BulkSettlementCompleted",
            "settled_order_ids": ["order-1"],
            # Numeric type
            "total_buying_power_released": 5000,
            "settlement_details": {},
        }

        event = BulkSettlementCompleted.model_validate(event_data)

        assert event.total_buying_power_released == Decimal("5000")


class TestTradingNotificationRequestedEventBridge:
    """Test TradingNotificationRequested EventBridge deserialization."""

    @pytest.mark.unit
    def test_eventbridge_string_deserialization(self):
        """Test deserialization from EventBridge JSON with string Decimal value."""
        event_data = {
            "event_id": "evt-123",
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "source_module": "test",
            "timestamp": "2025-01-06T12:30:45+00:00",
            "event_type": "TradingNotificationRequested",
            "schema_version": "1.0",
            "trading_success": True,
            "trading_mode": "LIVE",
            "orders_placed": 5,
            "orders_succeeded": 5,
            # EventBridge serializes Decimal to string
            "total_trade_value": "10000.00",
            "execution_data": {},
        }

        event = TradingNotificationRequested.model_validate(event_data)

        assert event.total_trade_value == Decimal("10000.00")

    @pytest.mark.unit
    def test_eventbridge_numeric_value(self):
        """Test handling of numeric value (edge case)."""
        event_data = {
            "event_id": "evt-123",
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "source_module": "test",
            "timestamp": "2025-01-06T12:30:45+00:00",
            "event_type": "TradingNotificationRequested",
            "trading_success": True,
            "trading_mode": "LIVE",
            "orders_placed": 5,
            "orders_succeeded": 5,
            # Numeric type
            "total_trade_value": 10000,
            "execution_data": {},
        }

        event = TradingNotificationRequested.model_validate(event_data)

        assert event.total_trade_value == Decimal("10000")
