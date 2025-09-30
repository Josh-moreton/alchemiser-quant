"""Unit tests for real-time data processor."""

from datetime import UTC, datetime, timedelta

import pytest

from the_alchemiser.shared.processors.real_time_data_processor import (
    ProcessingConfig,
    RealTimeDataProcessor,
    SymbolMetrics,
)
from the_alchemiser.shared.types.market_data import QuoteModel


class TestRealTimeDataProcessor:
    """Test suite for RealTimeDataProcessor."""

    @pytest.fixture
    def processor(self) -> RealTimeDataProcessor:
        """Create a processor instance for testing."""
        config = ProcessingConfig(
            max_quote_history=10,
            max_trade_history=10,
            vwap_window_seconds=60,
            cleanup_interval_seconds=300,
        )
        return RealTimeDataProcessor(config=config)

    @pytest.fixture
    def sample_quote(self) -> QuoteModel:
        """Create a sample quote for testing."""
        return QuoteModel(
            symbol="AAPL",
            bid_price=150.0,
            ask_price=150.10,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

    def test_processor_initialization(self, processor: RealTimeDataProcessor) -> None:
        """Test processor initializes correctly."""
        assert processor is not None
        assert processor.config.max_quote_history == 10
        assert processor.config.max_trade_history == 10

    def test_process_quote(self, processor: RealTimeDataProcessor, sample_quote: QuoteModel) -> None:
        """Test quote processing."""
        result = processor.process_quote(sample_quote)

        assert result["symbol"] == "AAPL"
        assert result["is_suspicious"] is False
        assert abs(result["spread"] - 0.10) < 0.01
        assert abs(result["mid_price"] - 150.05) < 0.01
        assert result["quote_count"] == 1

    def test_process_multiple_quotes(
        self, processor: RealTimeDataProcessor, sample_quote: QuoteModel
    ) -> None:
        """Test processing multiple quotes."""
        # Process first quote
        processor.process_quote(sample_quote)

        # Process second quote with different prices
        quote2 = QuoteModel(
            symbol="AAPL",
            bid_price=151.0,
            ask_price=151.20,
            bid_size=200.0,
            ask_size=150.0,
            timestamp=datetime.now(UTC),
        )
        result = processor.process_quote(quote2)

        assert result["quote_count"] == 2
        assert abs(result["spread"] - 0.20) < 0.01

    def test_process_trade(self, processor: RealTimeDataProcessor) -> None:
        """Test trade processing."""
        result = processor.process_trade(
            symbol="AAPL", price=150.0, size=100.0, timestamp=datetime.now(UTC)
        )

        assert result["symbol"] == "AAPL"
        assert result["price"] == 150.0
        assert result["size"] == 100.0
        assert result["total_volume"] == 100.0
        assert result["trade_count"] == 1

    def test_vwap_calculation(self, processor: RealTimeDataProcessor) -> None:
        """Test VWAP calculation."""
        now = datetime.now(UTC)

        # Process trades with different prices
        processor.process_trade(symbol="AAPL", price=150.0, size=100.0, timestamp=now)
        processor.process_trade(symbol="AAPL", price=151.0, size=200.0, timestamp=now)
        result = processor.process_trade(symbol="AAPL", price=149.0, size=100.0, timestamp=now)

        # VWAP = (150*100 + 151*200 + 149*100) / (100 + 200 + 100)
        expected_vwap = (150.0 * 100.0 + 151.0 * 200.0 + 149.0 * 100.0) / 400.0
        assert abs(result["vwap"] - expected_vwap) < 0.01

    def test_get_symbol_metrics(
        self, processor: RealTimeDataProcessor, sample_quote: QuoteModel
    ) -> None:
        """Test retrieving symbol metrics."""
        processor.process_quote(sample_quote)

        metrics = processor.get_symbol_metrics("AAPL")
        assert metrics is not None
        assert metrics.symbol == "AAPL"
        assert metrics.quote_count == 1
        assert metrics.last_quote == sample_quote

    def test_get_quote_history(
        self, processor: RealTimeDataProcessor, sample_quote: QuoteModel
    ) -> None:
        """Test retrieving quote history."""
        processor.process_quote(sample_quote)

        quote2 = QuoteModel(
            symbol="AAPL",
            bid_price=151.0,
            ask_price=151.20,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )
        processor.process_quote(quote2)

        history = processor.get_quote_history("AAPL")
        assert len(history) == 2
        assert history[0] == sample_quote
        assert history[1] == quote2

    def test_suspicious_quote_detection_negative_price(
        self, processor: RealTimeDataProcessor
    ) -> None:
        """Test detection of suspicious quotes with negative prices."""
        bad_quote = QuoteModel(
            symbol="AAPL",
            bid_price=-150.0,
            ask_price=150.10,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        result = processor.process_quote(bad_quote)
        assert result["is_suspicious"] is True

    def test_suspicious_quote_detection_inverted_bidask(
        self, processor: RealTimeDataProcessor
    ) -> None:
        """Test detection of suspicious quotes with inverted bid/ask."""
        bad_quote = QuoteModel(
            symbol="AAPL",
            bid_price=150.20,
            ask_price=150.10,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        result = processor.process_quote(bad_quote)
        assert result["is_suspicious"] is True

    def test_suspicious_quote_detection_excessive_spread(
        self, processor: RealTimeDataProcessor
    ) -> None:
        """Test detection of suspicious quotes with excessive spread."""
        bad_quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.0,
            ask_price=120.0,  # 20% spread
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        result = processor.process_quote(bad_quote)
        assert result["is_suspicious"] is True

    def test_clear_symbol(self, processor: RealTimeDataProcessor, sample_quote: QuoteModel) -> None:
        """Test clearing data for a specific symbol."""
        processor.process_quote(sample_quote)
        processor.process_trade(symbol="AAPL", price=150.0, size=100.0, timestamp=datetime.now(UTC))

        processor.clear_symbol("AAPL")

        metrics = processor.get_symbol_metrics("AAPL")
        assert metrics is None
        assert len(processor.get_quote_history("AAPL")) == 0

    def test_clear_all(self, processor: RealTimeDataProcessor, sample_quote: QuoteModel) -> None:
        """Test clearing all data."""
        processor.process_quote(sample_quote)
        processor.process_trade(symbol="AAPL", price=150.0, size=100.0, timestamp=datetime.now(UTC))

        quote2 = QuoteModel(
            symbol="MSFT",
            bid_price=300.0,
            ask_price=300.10,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )
        processor.process_quote(quote2)

        processor.clear_all()

        assert processor.get_symbol_metrics("AAPL") is None
        assert processor.get_symbol_metrics("MSFT") is None
        assert len(processor.get_all_metrics()) == 0

    def test_spread_statistics(self, processor: RealTimeDataProcessor) -> None:
        """Test spread statistics calculation."""
        quotes = [
            QuoteModel(
                symbol="AAPL",
                bid_price=150.0,
                ask_price=150.10,
                bid_size=100.0,
                ask_size=100.0,
                timestamp=datetime.now(UTC),
            ),
            QuoteModel(
                symbol="AAPL",
                bid_price=151.0,
                ask_price=151.20,
                bid_size=100.0,
                ask_size=100.0,
                timestamp=datetime.now(UTC),
            ),
            QuoteModel(
                symbol="AAPL",
                bid_price=152.0,
                ask_price=152.05,
                bid_size=100.0,
                ask_size=100.0,
                timestamp=datetime.now(UTC),
            ),
        ]

        for quote in quotes:
            processor.process_quote(quote)

        metrics = processor.get_symbol_metrics("AAPL")
        assert metrics is not None
        assert abs(metrics.min_spread - 0.05) < 0.01
        assert abs(metrics.max_spread - 0.20) < 0.01
        # Average spread = (0.10 + 0.20 + 0.05) / 3 = 0.1167
        assert abs(metrics.avg_spread - 0.1167) < 0.01

    def test_multiple_symbols(self, processor: RealTimeDataProcessor) -> None:
        """Test processing data for multiple symbols."""
        quote_aapl = QuoteModel(
            symbol="AAPL",
            bid_price=150.0,
            ask_price=150.10,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )
        quote_msft = QuoteModel(
            symbol="MSFT",
            bid_price=300.0,
            ask_price=300.20,
            bid_size=200.0,
            ask_size=150.0,
            timestamp=datetime.now(UTC),
        )

        processor.process_quote(quote_aapl)
        processor.process_quote(quote_msft)

        all_metrics = processor.get_all_metrics()
        assert len(all_metrics) == 2
        assert "AAPL" in all_metrics
        assert "MSFT" in all_metrics

    def test_quote_history_max_size(self, processor: RealTimeDataProcessor) -> None:
        """Test quote history respects max size."""
        # Process more quotes than max_quote_history (10)
        for i in range(15):
            quote = QuoteModel(
                symbol="AAPL",
                bid_price=150.0 + i,
                ask_price=150.10 + i,
                bid_size=100.0,
                ask_size=100.0,
                timestamp=datetime.now(UTC),
            )
            processor.process_quote(quote)

        history = processor.get_quote_history("AAPL")
        assert len(history) == 10  # Should not exceed max_quote_history

    def test_trade_history_max_size(self, processor: RealTimeDataProcessor) -> None:
        """Test trade history respects max size."""
        now = datetime.now(UTC)

        # Process more trades than max_trade_history (10)
        for i in range(15):
            processor.process_trade(symbol="AAPL", price=150.0 + i, size=100.0, timestamp=now)

        history = processor.get_trade_history("AAPL")
        assert len(history) == 10  # Should not exceed max_trade_history
