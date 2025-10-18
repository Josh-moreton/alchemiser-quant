"""Business Unit: shared | Status: current.

Test suite for AssetMetadataService.

Tests cover:
- Cache behavior and TTL
- Thread safety
- Error handling with typed exceptions
- Input validation
- Correlation ID propagation
- Cache metrics
"""

import threading
import time
from unittest.mock import Mock

import pytest

from the_alchemiser.shared.errors.exceptions import (
    DataProviderError,
    TradingClientError,
    ValidationError,
)
from the_alchemiser.shared.services.asset_metadata_service import (
    AssetMetadataService,
)


class TestAssetMetadataServiceInit:
    """Test service initialization and validation."""

    def test_init_valid_params(self):
        """Test initialization with valid parameters."""
        mock_client = Mock()
        service = AssetMetadataService(mock_client, asset_cache_ttl=300.0, max_cache_size=500)

        assert service._trading_client == mock_client
        assert service._asset_cache_ttl == 300.0
        assert service._max_cache_size == 500
        assert service._cache_hits == 0
        assert service._cache_misses == 0

    def test_init_none_trading_client(self):
        """Test initialization fails with None trading client."""
        with pytest.raises(ValidationError) as exc_info:
            AssetMetadataService(None)  # type: ignore

        assert "trading_client cannot be None" in str(exc_info.value)

    def test_init_negative_ttl(self):
        """Test initialization fails with negative TTL."""
        mock_client = Mock()
        with pytest.raises(ValidationError) as exc_info:
            AssetMetadataService(mock_client, asset_cache_ttl=-1.0)

        assert "asset_cache_ttl must be positive" in str(exc_info.value)

    def test_init_zero_cache_size(self):
        """Test initialization fails with zero cache size."""
        mock_client = Mock()
        with pytest.raises(ValidationError) as exc_info:
            AssetMetadataService(mock_client, max_cache_size=0)

        assert "max_cache_size must be positive" in str(exc_info.value)


class TestSymbolValidation:
    """Test symbol validation logic."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        mock_client = Mock()
        return AssetMetadataService(mock_client)

    def test_validate_symbol_valid(self, service):
        """Test validation of valid symbols."""
        assert service._validate_symbol("AAPL") == "AAPL"
        assert service._validate_symbol("aapl") == "AAPL"
        assert service._validate_symbol(" AAPL ") == "AAPL"
        assert service._validate_symbol("BRK.B") == "BRK.B"
        assert service._validate_symbol("SPX-W") == "SPX-W"

    def test_validate_symbol_empty(self, service):
        """Test validation fails for empty symbol."""
        with pytest.raises(ValidationError) as exc_info:
            service._validate_symbol("")
        assert "Symbol cannot be empty" in str(exc_info.value)

    def test_validate_symbol_whitespace_only(self, service):
        """Test validation fails for whitespace-only symbol."""
        with pytest.raises(ValidationError) as exc_info:
            service._validate_symbol("   ")
        assert "Symbol cannot be empty" in str(exc_info.value)

    def test_validate_symbol_invalid_chars(self, service):
        """Test validation fails for invalid characters."""
        with pytest.raises(ValidationError) as exc_info:
            service._validate_symbol("AAP@L")
        assert "Invalid symbol format" in str(exc_info.value)


class TestGetAssetInfo:
    """Test get_asset_info method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        mock_client = Mock()
        return AssetMetadataService(mock_client, asset_cache_ttl=1.0)

    @pytest.fixture
    def mock_asset(self):
        """Create mock asset object."""
        asset = Mock()
        asset.symbol = "AAPL"
        asset.name = "Apple Inc."
        asset.exchange = "NASDAQ"
        asset.asset_class = "us_equity"
        asset.tradable = True
        asset.fractionable = True
        asset.marginable = True
        asset.shortable = True
        return asset

    def test_get_asset_info_cache_miss(self, service, mock_asset):
        """Test cache miss fetches from API."""
        service._trading_client.get_asset.return_value = mock_asset

        result = service.get_asset_info("AAPL")

        assert result is not None
        assert result.symbol == "AAPL"
        assert result.fractionable is True
        assert result.tradable is True
        assert service._cache_misses == 1
        assert service._cache_hits == 0
        service._trading_client.get_asset.assert_called_once_with("AAPL")

    def test_get_asset_info_cache_hit(self, service, mock_asset):
        """Test cache hit doesn't call API."""
        service._trading_client.get_asset.return_value = mock_asset

        # First call - cache miss
        result1 = service.get_asset_info("AAPL")

        # Second call - cache hit
        result2 = service.get_asset_info("AAPL")

        assert result1 == result2
        assert service._cache_hits == 1
        assert service._cache_misses == 1
        # API called only once
        service._trading_client.get_asset.assert_called_once()

    def test_get_asset_info_cache_expiry(self, service, mock_asset):
        """Test cache expires after TTL."""
        service._trading_client.get_asset.return_value = mock_asset

        # First call
        service.get_asset_info("AAPL")

        # Wait for cache to expire
        time.sleep(1.1)

        # Second call should fetch from API
        service.get_asset_info("AAPL")

        assert service._cache_misses == 2
        assert service._trading_client.get_asset.call_count == 2

    def test_get_asset_info_with_correlation_id(self, service, mock_asset):
        """Test correlation ID is passed through."""
        service._trading_client.get_asset.return_value = mock_asset

        result = service.get_asset_info("AAPL", correlation_id="test-123")

        assert result is not None
        assert result.symbol == "AAPL"

    def test_get_asset_info_invalid_symbol(self, service):
        """Test invalid symbol raises ValidationError."""
        with pytest.raises(ValidationError):
            service.get_asset_info("")

    def test_get_asset_info_missing_fractionable_field(self, service):
        """Test missing fractionable field raises DataProviderError."""
        mock_asset = Mock()
        mock_asset.symbol = "AAPL"
        mock_asset.tradable = True
        # fractionable attribute missing
        del mock_asset.fractionable

        service._trading_client.get_asset.return_value = mock_asset

        with pytest.raises(DataProviderError) as exc_info:
            service.get_asset_info("AAPL")

        assert "fractionable" in str(exc_info.value)

    def test_get_asset_info_missing_tradable_field(self, service):
        """Test missing tradable field raises DataProviderError."""
        mock_asset = Mock()
        mock_asset.symbol = "AAPL"
        mock_asset.fractionable = True
        # tradable attribute missing
        del mock_asset.tradable

        service._trading_client.get_asset.return_value = mock_asset

        with pytest.raises(DataProviderError) as exc_info:
            service.get_asset_info("AAPL")

        assert "tradable" in str(exc_info.value)

    def test_get_asset_info_not_found(self, service):
        """Test asset not found returns None."""
        service._trading_client.get_asset.side_effect = Exception("Asset not found")

        result = service.get_asset_info("NOTFOUND")

        assert result is None

    def test_get_asset_info_api_error(self, service):
        """Test API error raises TradingClientError."""
        service._trading_client.get_asset.side_effect = Exception("API connection failed")

        with pytest.raises(TradingClientError):
            service.get_asset_info("AAPL")

    def test_get_asset_info_attribute_error(self, service):
        """Test AttributeError raises DataProviderError."""
        mock_asset = Mock()
        # Make accessing fractionable raise AttributeError
        type(mock_asset).fractionable = property(
            lambda self: (_ for _ in ()).throw(AttributeError("test"))
        )
        mock_asset.tradable = True

        service._trading_client.get_asset.return_value = mock_asset

        with pytest.raises(DataProviderError):
            service.get_asset_info("AAPL")


class TestIsFramentable:
    """Test is_fractionable method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        mock_client = Mock()
        return AssetMetadataService(mock_client)

    def test_is_fractionable_true(self, service):
        """Test fractionable asset returns True."""
        mock_asset = Mock()
        mock_asset.symbol = "AAPL"
        mock_asset.fractionable = True
        mock_asset.tradable = True

        service._trading_client.get_asset.return_value = mock_asset

        result = service.is_fractionable("AAPL")
        assert result is True

    def test_is_fractionable_false(self, service):
        """Test non-fractionable asset returns False."""
        mock_asset = Mock()
        mock_asset.symbol = "BRK.A"
        mock_asset.fractionable = False
        mock_asset.tradable = True

        service._trading_client.get_asset.return_value = mock_asset

        result = service.is_fractionable("BRK.A")
        assert result is False

    def test_is_fractionable_asset_not_found(self, service):
        """Test asset not found raises DataProviderError."""
        service._trading_client.get_asset.side_effect = Exception("Asset not found")

        with pytest.raises(DataProviderError) as exc_info:
            service.is_fractionable("NOTFOUND")

        assert "asset not found" in str(exc_info.value).lower()

    def test_is_fractionable_with_correlation_id(self, service):
        """Test correlation ID is propagated."""
        mock_asset = Mock()
        mock_asset.symbol = "AAPL"
        mock_asset.fractionable = True
        mock_asset.tradable = True

        service._trading_client.get_asset.return_value = mock_asset

        result = service.is_fractionable("AAPL", correlation_id="test-123")
        assert result is True


class TestIsMarketOpen:
    """Test is_market_open method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        mock_client = Mock()
        return AssetMetadataService(mock_client)

    def test_is_market_open_true(self, service):
        """Test market open returns True."""
        mock_clock = Mock()
        mock_clock.is_open = True
        service._trading_client.get_clock.return_value = mock_clock

        result = service.is_market_open()
        assert result is True

    def test_is_market_open_false(self, service):
        """Test market closed returns False."""
        mock_clock = Mock()
        mock_clock.is_open = False
        service._trading_client.get_clock.return_value = mock_clock

        result = service.is_market_open()
        assert result is False

    def test_is_market_open_api_error(self, service):
        """Test API error raises TradingClientError."""
        service._trading_client.get_clock.side_effect = Exception("API error")

        with pytest.raises(TradingClientError):
            service.is_market_open()

    def test_is_market_open_with_correlation_id(self, service):
        """Test correlation ID is passed through."""
        mock_clock = Mock()
        mock_clock.is_open = True
        service._trading_client.get_clock.return_value = mock_clock

        result = service.is_market_open(correlation_id="test-123")
        assert result is True


class TestGetMarketCalendar:
    """Test get_market_calendar method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        mock_client = Mock()
        return AssetMetadataService(mock_client)

    def test_get_market_calendar_success(self, service):
        """Test successful calendar retrieval."""
        mock_day1 = Mock()
        mock_day1.date = "2025-01-06"
        mock_day1.open = "09:30"
        mock_day1.close = "16:00"

        mock_day2 = Mock()
        mock_day2.date = "2025-01-07"
        mock_day2.open = "09:30"
        mock_day2.close = "16:00"

        service._trading_client.get_calendar.return_value = [mock_day1, mock_day2]

        result = service.get_market_calendar()

        assert len(result) == 2
        assert result[0]["date"] == "2025-01-06"
        assert result[1]["date"] == "2025-01-07"

    def test_get_market_calendar_api_error(self, service):
        """Test API error raises TradingClientError."""
        service._trading_client.get_calendar.side_effect = Exception("API error")

        with pytest.raises(TradingClientError):
            service.get_market_calendar()

    def test_get_market_calendar_with_correlation_id(self, service):
        """Test correlation ID is passed through."""
        service._trading_client.get_calendar.return_value = []

        result = service.get_market_calendar(correlation_id="test-123")
        assert result == []


class TestCacheManagement:
    """Test cache management functionality."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        mock_client = Mock()
        return AssetMetadataService(mock_client, max_cache_size=3)

    def test_clear_cache(self, service):
        """Test cache clearing."""
        # Populate cache
        mock_asset = Mock()
        mock_asset.symbol = "AAPL"
        mock_asset.fractionable = True
        mock_asset.tradable = True
        service._trading_client.get_asset.return_value = mock_asset

        service.get_asset_info("AAPL")
        assert len(service._asset_cache) == 1

        # Clear cache
        service.clear_cache()
        assert len(service._asset_cache) == 0
        assert len(service._asset_cache_timestamps) == 0

    def test_lru_eviction(self, service):
        """Test LRU eviction when cache is full."""
        mock_asset = Mock()
        mock_asset.fractionable = True
        mock_asset.tradable = True

        # Fill cache to max (3 entries)
        for symbol in ["AAPL", "MSFT", "GOOGL"]:
            mock_asset.symbol = symbol
            service._trading_client.get_asset.return_value = mock_asset
            service.get_asset_info(symbol)

        assert len(service._asset_cache) == 3

        # Add 4th entry - should evict oldest (AAPL)
        mock_asset.symbol = "TSLA"
        service._trading_client.get_asset.return_value = mock_asset
        service.get_asset_info("TSLA")

        assert len(service._asset_cache) == 3
        assert "AAPL" not in service._asset_cache
        assert "TSLA" in service._asset_cache

    def test_get_cache_stats(self, service):
        """Test cache statistics."""
        # Initially empty
        stats = service.get_cache_stats()
        assert stats["total_cached"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["cache_hit_ratio"] == 0.0

        # Add one entry
        mock_asset = Mock()
        mock_asset.symbol = "AAPL"
        mock_asset.fractionable = True
        mock_asset.tradable = True
        service._trading_client.get_asset.return_value = mock_asset

        service.get_asset_info("AAPL")  # Miss
        service.get_asset_info("AAPL")  # Hit

        stats = service.get_cache_stats()
        assert stats["total_cached"] == 1
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["cache_hit_ratio"] == 0.5

    def test_cache_stats_type(self, service):
        """Test cache stats returns CacheStats TypedDict."""
        stats = service.get_cache_stats()

        # Verify all required keys present
        assert "total_cached" in stats
        assert "expired_entries" in stats
        assert "cache_ttl" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "cache_hit_ratio" in stats


class TestThreadSafety:
    """Test thread safety of cache operations."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        mock_client = Mock()
        return AssetMetadataService(mock_client, asset_cache_ttl=10.0)

    def test_concurrent_cache_access(self, service):
        """Test concurrent reads/writes don't cause issues."""
        mock_asset = Mock()
        mock_asset.fractionable = True
        mock_asset.tradable = True

        symbols = [f"SYM{i}" for i in range(10)]
        errors = []

        def fetch_asset(symbol):
            try:
                mock_asset.symbol = symbol
                service._trading_client.get_asset.return_value = mock_asset
                result = service.get_asset_info(symbol)
                assert result is not None
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=fetch_asset, args=(sym,)) for sym in symbols]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # No errors should occur
        assert len(errors) == 0
        # All symbols should be cached
        assert len(service._asset_cache) == 10

    def test_concurrent_cache_stats(self, service):
        """Test concurrent stats access doesn't deadlock."""
        errors = []

        def get_stats():
            try:
                stats = service.get_cache_stats()
                assert stats is not None
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_stats) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
