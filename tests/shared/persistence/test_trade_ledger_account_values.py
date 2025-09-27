#!/usr/bin/env python3
"""Tests for trade ledger account value logging functionality."""

import os
import tempfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from the_alchemiser.shared.persistence.local_trade_ledger import LocalTradeLedger
from the_alchemiser.shared.schemas.trade_ledger import AccountValueEntry, AccountValueQuery
from the_alchemiser.shared.services.account_value_service import AccountValueService
from the_alchemiser.shared.types.account import AccountModel


class TestTradeLedgerAccountValues:
    """Test cases for trade ledger account value functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def trade_ledger(self, temp_dir):
        """Create trade ledger instance with temporary directory."""
        return LocalTradeLedger(base_path=temp_dir)

    @pytest.fixture
    def sample_entry(self):
        """Create sample account value entry."""
        return AccountValueEntry(
            entry_id="test-entry-1",
            account_id="test-account",
            portfolio_value=Decimal("10000.00"),
            cash=Decimal("2000.00"),
            equity=Decimal("8000.00"),
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            source="test",
        )

    def test_log_and_query_account_value(self, trade_ledger, sample_entry):
        """Test logging and querying account values via trade ledger."""
        # Log entry
        trade_ledger.log_account_value(sample_entry)
        
        # Query all entries
        filters = AccountValueQuery()
        entries = list(trade_ledger.query_account_values(filters))
        
        assert len(entries) == 1
        assert entries[0].entry_id == sample_entry.entry_id
        assert entries[0].portfolio_value == sample_entry.portfolio_value

    def test_account_value_date_deduplication(self, trade_ledger):
        """Test that account values are deduplicated by date."""
        # First entry
        entry1 = AccountValueEntry(
            entry_id="test-1",
            account_id="test-account",
            portfolio_value=Decimal("10000.00"),
            cash=Decimal("2000.00"),
            equity=Decimal("8000.00"),
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            source="test",
        )
        
        # Second entry same date, different value
        entry2 = AccountValueEntry(
            entry_id="test-2",
            account_id="test-account",
            portfolio_value=Decimal("11000.00"),
            cash=Decimal("2500.00"),
            equity=Decimal("8500.00"),
            timestamp=datetime(2024, 1, 15, 15, 0, 0, tzinfo=UTC),
            source="test",
        )
        
        trade_ledger.log_account_value(entry1)
        trade_ledger.log_account_value(entry2)
        
        # Should only have one entry (the updated one)
        filters = AccountValueQuery(account_id="test-account")
        entries = list(trade_ledger.query_account_values(filters))
        
        assert len(entries) == 1
        assert entries[0].portfolio_value == Decimal("11000.00")

    def test_get_latest_account_value(self, trade_ledger):
        """Test getting latest account value."""
        # Create entries
        entry1 = AccountValueEntry(
            entry_id="test-1",
            account_id="test-account",
            portfolio_value=Decimal("10000.00"),
            cash=Decimal("2000.00"),
            equity=Decimal("8000.00"),
            timestamp=datetime(2024, 1, 10, 10, 0, 0, tzinfo=UTC),
            source="test",
        )
        
        entry2 = AccountValueEntry(
            entry_id="test-2",
            account_id="test-account",
            portfolio_value=Decimal("11000.00"),
            cash=Decimal("2500.00"),
            equity=Decimal("8500.00"),
            timestamp=datetime(2024, 1, 20, 10, 0, 0, tzinfo=UTC),
            source="test",
        )
        
        trade_ledger.log_account_value(entry1)
        trade_ledger.log_account_value(entry2)
        
        # Get latest
        latest = trade_ledger.get_latest_account_value("test-account")
        
        assert latest is not None
        assert latest.portfolio_value == Decimal("11000.00")
        assert latest.timestamp == entry2.timestamp


class TestAccountValueService:
    """Test cases for AccountValueService."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_trade_ledger(self, temp_dir):
        """Create mock trade ledger for testing."""
        return LocalTradeLedger(base_path=temp_dir)

    @pytest.fixture
    def service(self, mock_trade_ledger):
        """Create service instance with mock trade ledger."""
        return AccountValueService(trade_ledger=mock_trade_ledger)

    @pytest.fixture
    def sample_account(self):
        """Create sample account model."""
        return AccountModel(
            account_id="test-account",
            equity=10000.0,
            cash=2000.0,
            buying_power=5000.0,
            day_trades_remaining=3,
            portfolio_value=12000.0,
            last_equity=9500.0,
            daytrading_buying_power=8000.0,
            regt_buying_power=5000.0,
            status="ACTIVE"
        )

    def test_service_disabled_by_default(self, service, sample_account):
        """Test that service is disabled by default (no env var set)."""
        # Service should be disabled by default (no env var set)
        result = service.log_current_account_value(sample_account)
        assert result is False

    def test_service_enabled_with_env_var(self, service, sample_account, temp_dir):
        """Test that service works when enabled via environment variable."""
        # Set environment variable to enable
        os.environ["ENABLE_ACCOUNT_VALUE_LOGGING"] = "true"
        
        # Create new service to pick up env var
        trade_ledger = LocalTradeLedger(base_path=temp_dir)
        service = AccountValueService(trade_ledger=trade_ledger)
        
        # Should be enabled now
        assert service.is_enabled() is True
        
        # Should successfully log
        result = service.log_current_account_value(sample_account)
        assert result is True
        
        # Clean up env var
        del os.environ["ENABLE_ACCOUNT_VALUE_LOGGING"]