"""Business Unit: shared | Status: current.

Comprehensive unit and property-based tests for Account domain models.

Tests AccountModel and PortfolioHistoryModel value objects per guardrails.
"""

import pytest
from hypothesis import given, strategies as st

from the_alchemiser.shared.types.account import AccountModel, PortfolioHistoryModel


class TestAccountModel:
    """Test AccountModel value object."""

    @pytest.mark.unit
    def test_create_account_model(self):
        """Test creating AccountModel."""
        account = AccountModel(
            account_id="test-123",
            equity=10000.0,
            cash=5000.0,
            buying_power=15000.0,
            day_trades_remaining=3,
            portfolio_value=10000.0,
            last_equity=9500.0,
            daytrading_buying_power=15000.0,
            regt_buying_power=15000.0,
            status="ACTIVE"
        )
        
        assert account.account_id == "test-123"
        assert account.equity == 10000.0
        assert account.cash == 5000.0
        assert account.status == "ACTIVE"

    @pytest.mark.unit
    def test_from_dict(self):
        """Test creating AccountModel from dict."""
        from decimal import Decimal
        
        data = {
            "account_id": "test-456",
            "equity": Decimal("20000.0"),
            "cash": Decimal("10000.0"),
            "buying_power": Decimal("30000.0"),
            "day_trades_remaining": 2,
            "portfolio_value": Decimal("20000.0"),
            "last_equity": Decimal("19000.0"),
            "daytrading_buying_power": Decimal("30000.0"),
            "regt_buying_power": Decimal("30000.0"),
            "status": "ACTIVE"
        }
        
        account = AccountModel.from_dict(data)
        
        assert account.account_id == "test-456"
        assert account.equity == 20000.0
        assert account.portfolio_value == 20000.0

    @pytest.mark.unit
    def test_to_dict(self):
        """Test converting AccountModel to dict."""
        from decimal import Decimal
        
        account = AccountModel(
            account_id="test-789",
            equity=15000.0,
            cash=7500.0,
            buying_power=22500.0,
            day_trades_remaining=1,
            portfolio_value=15000.0,
            last_equity=14500.0,
            daytrading_buying_power=22500.0,
            regt_buying_power=22500.0,
            status="ACTIVE"
        )
        
        result = account.to_dict()
        
        assert result["account_id"] == "test-789"
        assert result["equity"] == Decimal("15000.0")
        assert result["cash"] == Decimal("7500.0")
        assert result["status"] == "ACTIVE"

    @pytest.mark.unit
    def test_roundtrip_dict_conversion(self):
        """Test round-trip dict conversion."""
        from decimal import Decimal
        
        original = {
            "account_id": "test-999",
            "equity": Decimal("50000.0"),
            "cash": Decimal("25000.0"),
            "buying_power": Decimal("75000.0"),
            "day_trades_remaining": 0,
            "portfolio_value": Decimal("50000.0"),
            "last_equity": Decimal("48000.0"),
            "daytrading_buying_power": Decimal("75000.0"),
            "regt_buying_power": Decimal("75000.0"),
            "status": "ACTIVE"
        }
        
        account = AccountModel.from_dict(original)
        result = account.to_dict()
        
        assert result == original

    @pytest.mark.unit
    def test_account_model_is_frozen(self):
        """Test that AccountModel is immutable."""
        account = AccountModel(
            account_id="test-111",
            equity=10000.0,
            cash=5000.0,
            buying_power=15000.0,
            day_trades_remaining=3,
            portfolio_value=10000.0,
            last_equity=9500.0,
            daytrading_buying_power=15000.0,
            regt_buying_power=15000.0,
            status="ACTIVE"
        )
        
        with pytest.raises(AttributeError):
            account.equity = 20000.0

    @pytest.mark.unit
    def test_inactive_status(self):
        """Test AccountModel with INACTIVE status."""
        account = AccountModel(
            account_id="test-222",
            equity=0.0,
            cash=0.0,
            buying_power=0.0,
            day_trades_remaining=0,
            portfolio_value=0.0,
            last_equity=0.0,
            daytrading_buying_power=0.0,
            regt_buying_power=0.0,
            status="INACTIVE"
        )
        
        assert account.status == "INACTIVE"


class TestPortfolioHistoryModel:
    """Test PortfolioHistoryModel value object."""

    @pytest.mark.unit
    def test_create_portfolio_history(self):
        """Test creating PortfolioHistoryModel."""
        history = PortfolioHistoryModel(
            profit_loss=[100.0, 200.0, 150.0],
            profit_loss_pct=[1.0, 2.0, 1.5],
            equity=[10100.0, 10200.0, 10150.0],
            timestamp=["2024-01-01", "2024-01-02", "2024-01-03"]
        )
        
        assert len(history.profit_loss) == 3
        assert len(history.equity) == 3
        assert len(history.timestamp) == 3

    @pytest.mark.unit
    def test_from_dict(self):
        """Test creating PortfolioHistoryModel from dict."""
        data = {
            "profit_loss": [50.0, 75.0],
            "profit_loss_pct": [0.5, 0.75],
            "equity": [10050.0, 10075.0],
            "timestamp": ["2024-01-01", "2024-01-02"]
        }
        
        history = PortfolioHistoryModel.from_dict(data)
        
        assert history.profit_loss == [50.0, 75.0]
        assert history.equity == [10050.0, 10075.0]

    @pytest.mark.unit
    def test_to_dict(self):
        """Test converting PortfolioHistoryModel to dict."""
        history = PortfolioHistoryModel(
            profit_loss=[100.0, 200.0],
            profit_loss_pct=[1.0, 2.0],
            equity=[10100.0, 10200.0],
            timestamp=["2024-01-01", "2024-01-02"]
        )
        
        result = history.to_dict()
        
        assert result["profit_loss"] == [100.0, 200.0]
        assert result["equity"] == [10100.0, 10200.0]
        assert result["timestamp"] == ["2024-01-01", "2024-01-02"]

    @pytest.mark.unit
    def test_is_empty_with_data(self):
        """Test is_empty property with data."""
        history = PortfolioHistoryModel(
            profit_loss=[100.0],
            profit_loss_pct=[1.0],
            equity=[10100.0],
            timestamp=["2024-01-01"]
        )
        
        assert history.is_empty == False

    @pytest.mark.unit
    def test_is_empty_without_data(self):
        """Test is_empty property without data."""
        history = PortfolioHistoryModel(
            profit_loss=[],
            profit_loss_pct=[],
            equity=[],
            timestamp=[]
        )
        
        assert history.is_empty == True

    @pytest.mark.unit
    def test_latest_equity(self):
        """Test latest_equity property."""
        history = PortfolioHistoryModel(
            profit_loss=[100.0, 200.0, 150.0],
            profit_loss_pct=[1.0, 2.0, 1.5],
            equity=[10100.0, 10200.0, 10150.0],
            timestamp=["2024-01-01", "2024-01-02", "2024-01-03"]
        )
        
        assert history.latest_equity == 10150.0

    @pytest.mark.unit
    def test_latest_equity_empty(self):
        """Test latest_equity with empty history."""
        history = PortfolioHistoryModel(
            profit_loss=[],
            profit_loss_pct=[],
            equity=[],
            timestamp=[]
        )
        
        assert history.latest_equity is None

    @pytest.mark.unit
    def test_latest_pnl(self):
        """Test latest_pnl property."""
        history = PortfolioHistoryModel(
            profit_loss=[100.0, 200.0, 150.0],
            profit_loss_pct=[1.0, 2.0, 1.5],
            equity=[10100.0, 10200.0, 10150.0],
            timestamp=["2024-01-01", "2024-01-02", "2024-01-03"]
        )
        
        assert history.latest_pnl == 150.0

    @pytest.mark.unit
    def test_latest_pnl_empty(self):
        """Test latest_pnl with empty history."""
        history = PortfolioHistoryModel(
            profit_loss=[],
            profit_loss_pct=[],
            equity=[],
            timestamp=[]
        )
        
        assert history.latest_pnl is None

    @pytest.mark.unit
    def test_portfolio_history_is_frozen(self):
        """Test that PortfolioHistoryModel is immutable."""
        history = PortfolioHistoryModel(
            profit_loss=[100.0],
            profit_loss_pct=[1.0],
            equity=[10100.0],
            timestamp=["2024-01-01"]
        )
        
        with pytest.raises(AttributeError):
            history.equity = [20000.0]

    @pytest.mark.unit
    def test_from_dict_with_missing_keys(self):
        """Test from_dict with missing optional keys."""
        data = {}
        
        history = PortfolioHistoryModel.from_dict(data)
        
        assert history.profit_loss == []
        assert history.equity == []
        assert history.timestamp == []
        assert history.is_empty == True


# Property-based tests using Hypothesis
class TestAccountModelProperties:
    """Property-based tests for AccountModel."""

    @pytest.mark.property
    @given(
        st.floats(min_value=0.0, max_value=1000000.0),
        st.floats(min_value=0.0, max_value=1000000.0)
    )
    def test_portfolio_value_equals_equity(self, equity, cash):
        """Property: portfolio value should typically equal equity in simple cases."""
        account = AccountModel(
            account_id="test",
            equity=equity,
            cash=cash,
            buying_power=equity + cash,
            day_trades_remaining=3,
            portfolio_value=equity,
            last_equity=equity * 0.95,
            daytrading_buying_power=equity + cash,
            regt_buying_power=equity + cash,
            status="ACTIVE"
        )
        
        assert account.equity == account.portfolio_value

    @pytest.mark.property
    @given(st.integers(min_value=0, max_value=10))
    def test_day_trades_remaining_non_negative(self, day_trades):
        """Property: day trades remaining should be non-negative."""
        account = AccountModel(
            account_id="test",
            equity=10000.0,
            cash=5000.0,
            buying_power=15000.0,
            day_trades_remaining=day_trades,
            portfolio_value=10000.0,
            last_equity=9500.0,
            daytrading_buying_power=15000.0,
            regt_buying_power=15000.0,
            status="ACTIVE"
        )
        
        assert account.day_trades_remaining >= 0


class TestPortfolioHistoryModelProperties:
    """Property-based tests for PortfolioHistoryModel."""

    @pytest.mark.property
    @given(st.lists(st.floats(min_value=-1000.0, max_value=1000.0), min_size=0, max_size=100))
    def test_latest_pnl_matches_last_element(self, pnl_list):
        """Property: latest_pnl should match the last element in profit_loss list."""
        history = PortfolioHistoryModel(
            profit_loss=pnl_list,
            profit_loss_pct=[0.0] * len(pnl_list),
            equity=[10000.0] * len(pnl_list),
            timestamp=[f"2024-{i:02d}-01" for i in range(1, len(pnl_list) + 1)]
        )
        
        if pnl_list:
            assert history.latest_pnl == pnl_list[-1]
        else:
            assert history.latest_pnl is None

    @pytest.mark.property
    @given(st.lists(st.floats(min_value=0.0, max_value=1000000.0), min_size=0, max_size=100))
    def test_latest_equity_matches_last_element(self, equity_list):
        """Property: latest_equity should match the last element in equity list."""
        history = PortfolioHistoryModel(
            profit_loss=[0.0] * len(equity_list),
            profit_loss_pct=[0.0] * len(equity_list),
            equity=equity_list,
            timestamp=[f"2024-{i:02d}-01" for i in range(1, len(equity_list) + 1)]
        )
        
        if equity_list:
            assert history.latest_equity == equity_list[-1]
        else:
            assert history.latest_equity is None

    @pytest.mark.property
    @given(st.integers(min_value=0, max_value=100))
    def test_history_length_consistency(self, length):
        """Property: all lists in history should have same length."""
        history = PortfolioHistoryModel(
            profit_loss=[0.0] * length,
            profit_loss_pct=[0.0] * length,
            equity=[10000.0] * length,
            timestamp=[f"2024-{i:02d}-01" for i in range(1, length + 1)]
        )
        
        assert len(history.profit_loss) == length
        assert len(history.equity) == length
        assert len(history.timestamp) == length
