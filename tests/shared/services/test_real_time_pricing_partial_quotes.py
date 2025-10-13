"""Business Unit: shared | Status: current.

Tests for RealTimePricingService partial quote handling.

Tests cover:
- Partial quote handling (bid-only, ask-only)
- Empty quote handling (both None)
- Full quote handling (both present)
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from the_alchemiser.shared.services.real_time_data_processor import (
    RealTimeDataProcessor,
)
from the_alchemiser.shared.services.real_time_price_store import RealTimePriceStore
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService
from the_alchemiser.shared.types.market_data import QuoteExtractionResult


class TestPartialQuoteHandling:
    """Test handling of partial quotes (when only bid or ask is available)."""

    @pytest.fixture
    def price_store(self):
        """Create a real price store for testing."""
        return RealTimePriceStore()

    @pytest.fixture
    def data_processor(self):
        """Create a mock data processor."""
        processor = Mock(spec=RealTimeDataProcessor)
        processor.extract_symbol_from_quote = Mock(return_value="AAPL")
        processor.get_quote_timestamp = Mock(return_value=datetime.now(UTC))
        processor.log_quote_debug = AsyncMock()
        return processor

    @pytest.fixture
    def pricing_service(self, price_store, data_processor):
        """Create pricing service with mocked dependencies."""
        with patch(
            "the_alchemiser.shared.services.real_time_pricing.RealTimeDataProcessor"
        ) as mock_processor_class:
            mock_processor_class.return_value = data_processor
            
            with patch(
                "the_alchemiser.shared.services.real_time_pricing.RealTimePriceStore"
            ) as mock_store_class:
                mock_store_class.return_value = price_store
                
                service = RealTimePricingService(
                    api_key="test_key",
                    secret_key="test_secret",
                    paper_trading=True,
                )
                # Replace with our real instances
                service._price_store = price_store
                service._data_processor = data_processor
                
                return service

    @pytest.mark.asyncio
    async def test_bid_only_quote_uses_bid_for_both_sides(
        self, pricing_service, data_processor, price_store
    ):
        """Test that when only bid is available, it's used for both bid and ask."""
        # Setup: quote with only bid
        data_processor.extract_quote_values.return_value = QuoteExtractionResult(
            bid_price=Decimal("150.00"),
            ask_price=None,  # Ask is None
            bid_size=Decimal("100"),
            ask_size=Decimal("0"),
            timestamp_raw=datetime.now(UTC),
        )

        # Execute
        await pricing_service._on_quote({"S": "AAPL", "bp": 150.00})

        # Verify: bid was used for both sides
        quote_data = price_store.get_quote_data("AAPL")
        assert quote_data is not None
        assert quote_data.bid_price == Decimal("150.00")
        assert quote_data.ask_price == Decimal("150.00")  # Should use bid
        assert quote_data.symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_ask_only_quote_uses_ask_for_both_sides(
        self, pricing_service, data_processor, price_store
    ):
        """Test that when only ask is available, it's used for both bid and ask."""
        # Setup: quote with only ask
        data_processor.extract_quote_values.return_value = QuoteExtractionResult(
            bid_price=None,  # Bid is None
            ask_price=Decimal("151.00"),
            bid_size=Decimal("0"),
            ask_size=Decimal("200"),
            timestamp_raw=datetime.now(UTC),
        )

        # Execute
        await pricing_service._on_quote({"S": "AAPL", "ap": 151.00})

        # Verify: ask was used for both sides
        quote_data = price_store.get_quote_data("AAPL")
        assert quote_data is not None
        assert quote_data.bid_price == Decimal("151.00")  # Should use ask
        assert quote_data.ask_price == Decimal("151.00")
        assert quote_data.symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_both_none_keeps_previous_quote(
        self, pricing_service, data_processor, price_store
    ):
        """Test that when both bid and ask are None, previous quote is kept."""
        # Setup: store an initial quote
        initial_timestamp = datetime.now(UTC)
        price_store.update_quote_data(
            symbol="AAPL",
            bid_price=Decimal("150.00"),
            ask_price=Decimal("150.50"),
            bid_size=Decimal("100"),
            ask_size=Decimal("200"),
            timestamp=initial_timestamp,
        )

        # Setup: new quote with both None
        data_processor.extract_quote_values.return_value = QuoteExtractionResult(
            bid_price=None,
            ask_price=None,
            bid_size=None,
            ask_size=None,
            timestamp_raw=datetime.now(UTC),
        )

        # Execute
        await pricing_service._on_quote({"S": "AAPL"})

        # Verify: previous quote is still there unchanged
        quote_data = price_store.get_quote_data("AAPL")
        assert quote_data is not None
        assert quote_data.bid_price == Decimal("150.00")  # Original bid
        assert quote_data.ask_price == Decimal("150.50")  # Original ask
        assert quote_data.timestamp == initial_timestamp  # Original timestamp

    @pytest.mark.asyncio
    async def test_full_quote_updates_normally(
        self, pricing_service, data_processor, price_store
    ):
        """Test that when both bid and ask are present, quote updates normally."""
        # Setup: quote with both sides
        data_processor.extract_quote_values.return_value = QuoteExtractionResult(
            bid_price=Decimal("150.00"),
            ask_price=Decimal("150.50"),
            bid_size=Decimal("100"),
            ask_size=Decimal("200"),
            timestamp_raw=datetime.now(UTC),
        )

        # Execute
        await pricing_service._on_quote({"S": "AAPL", "bp": 150.00, "ap": 150.50})

        # Verify: both sides updated
        quote_data = price_store.get_quote_data("AAPL")
        assert quote_data is not None
        assert quote_data.bid_price == Decimal("150.00")
        assert quote_data.ask_price == Decimal("150.50")
        assert quote_data.symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_partial_quote_updates_after_full_quote(
        self, pricing_service, data_processor, price_store
    ):
        """Test that partial quotes can update after full quotes."""
        # Setup: First, store a full quote
        data_processor.extract_quote_values.return_value = QuoteExtractionResult(
            bid_price=Decimal("150.00"),
            ask_price=Decimal("150.50"),
            bid_size=Decimal("100"),
            ask_size=Decimal("200"),
            timestamp_raw=datetime.now(UTC),
        )
        await pricing_service._on_quote({"S": "AAPL", "bp": 150.00, "ap": 150.50})

        # Execute: Now update with bid-only quote
        data_processor.extract_quote_values.return_value = QuoteExtractionResult(
            bid_price=Decimal("151.00"),
            ask_price=None,  # Ask is None
            bid_size=Decimal("150"),
            ask_size=Decimal("0"),
            timestamp_raw=datetime.now(UTC),
        )
        await pricing_service._on_quote({"S": "AAPL", "bp": 151.00})

        # Verify: both sides now use the new bid
        quote_data = price_store.get_quote_data("AAPL")
        assert quote_data is not None
        assert quote_data.bid_price == Decimal("151.00")
        assert quote_data.ask_price == Decimal("151.00")  # Should use new bid

    @pytest.mark.asyncio
    async def test_empty_quote_does_not_create_new_entry(
        self, pricing_service, data_processor, price_store
    ):
        """Test that empty quotes don't create entries for symbols without previous data."""
        # Setup: quote with both None for a symbol that doesn't exist yet
        data_processor.extract_quote_values.return_value = QuoteExtractionResult(
            bid_price=None,
            ask_price=None,
            bid_size=None,
            ask_size=None,
            timestamp_raw=datetime.now(UTC),
        )

        # Execute
        await pricing_service._on_quote({"S": "NEWSTOCK"})

        # Verify: no quote data created
        quote_data = price_store.get_quote_data("NEWSTOCK")
        assert quote_data is None
