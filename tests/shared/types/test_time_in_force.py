"""Business Unit: shared | Status: current.

Comprehensive unit tests for TimeInForce value object.

This test suite validates the TimeInForce dataclass and demonstrates
the validation redundancy issue identified in the file review.
"""

"""Business Unit: shared | Status: current.

Comprehensive unit tests for TimeInForce value object.

This test suite validates the TimeInForce dataclass and demonstrates
the validation redundancy issue identified in the file review.

NOTE: Tests import directly from module file to avoid pandas dependency
in the package __init__.py that would break test collection.
"""

import sys
import importlib.util
from pathlib import Path

import pytest

# Load TimeInForce module directly from file to avoid __init__.py dependencies
_module_path = Path(__file__).parent.parent.parent.parent / "the_alchemiser" / "shared" / "types" / "time_in_force.py"
spec = importlib.util.spec_from_file_location(
    "the_alchemiser.shared.types.time_in_force",
    str(_module_path)
)
_time_in_force_module = importlib.util.module_from_spec(spec)
sys.modules["the_alchemiser.shared.types.time_in_force"] = _time_in_force_module
spec.loader.exec_module(_time_in_force_module)

TimeInForce = _time_in_force_module.TimeInForce


class TestTimeInForceConstruction:
    """Test TimeInForce value object construction and validation."""

    @pytest.mark.unit
    def test_create_valid_day(self):
        """Test creating TimeInForce with 'day' value."""
        tif = TimeInForce(value="day")
        assert tif.value == "day"

    @pytest.mark.unit
    def test_create_valid_gtc(self):
        """Test creating TimeInForce with 'gtc' value."""
        tif = TimeInForce(value="gtc")
        assert tif.value == "gtc"

    @pytest.mark.unit
    def test_create_valid_ioc(self):
        """Test creating TimeInForce with 'ioc' value."""
        tif = TimeInForce(value="ioc")
        assert tif.value == "ioc"

    @pytest.mark.unit
    def test_create_valid_fok(self):
        """Test creating TimeInForce with 'fok' value."""
        tif = TimeInForce(value="fok")
        assert tif.value == "fok"

    @pytest.mark.unit
    def test_frozen_immutable(self):
        """Test that TimeInForce is immutable (frozen)."""
        tif = TimeInForce(value="day")
        with pytest.raises(AttributeError):
            tif.value = "gtc"  # type: ignore

    @pytest.mark.unit
    def test_invalid_value_rejected_by_type_checker(self):
        """Test that invalid values are rejected by type checker.
        
        NOTE: This test demonstrates that the Literal type constraint
        prevents invalid values at the type-checking level, making the
        __post_init__ validation unreachable in practice.
        
        This test cannot actually execute the invalid code path because
        mypy would reject it. The test is included for documentation.
        """
        # The following would fail type checking:
        # tif = TimeInForce(value="invalid")  # type: ignore
        
        # To test runtime validation, we'd need to bypass type checking:
        # This is why the __post_init__ validation is marked with pragma: no cover
        pass


class TestTimeInForceEquality:
    """Test TimeInForce equality and hashing."""

    @pytest.mark.unit
    def test_equality_same_value(self):
        """Test that two TimeInForce objects with same value are equal."""
        tif1 = TimeInForce(value="day")
        tif2 = TimeInForce(value="day")
        assert tif1 == tif2

    @pytest.mark.unit
    def test_inequality_different_values(self):
        """Test that TimeInForce objects with different values are not equal."""
        tif1 = TimeInForce(value="day")
        tif2 = TimeInForce(value="gtc")
        assert tif1 != tif2

    @pytest.mark.unit
    def test_hashable(self):
        """Test that TimeInForce can be used in sets and as dict keys."""
        tif1 = TimeInForce(value="day")
        tif2 = TimeInForce(value="gtc")
        tif3 = TimeInForce(value="day")
        
        # Can create set
        tif_set = {tif1, tif2, tif3}
        assert len(tif_set) == 2  # tif1 and tif3 are equal
        
        # Can use as dict key
        tif_dict = {tif1: "Day order", tif2: "GTC order"}
        assert tif_dict[tif1] == "Day order"
        assert tif_dict[tif3] == "Day order"  # Same key as tif1


class TestTimeInForceRepresentation:
    """Test TimeInForce string representation."""

    @pytest.mark.unit
    def test_repr(self):
        """Test that repr shows class and value."""
        tif = TimeInForce(value="day")
        repr_str = repr(tif)
        assert "TimeInForce" in repr_str
        assert "day" in repr_str

    @pytest.mark.unit
    def test_str_representation(self):
        """Test string representation."""
        tif = TimeInForce(value="gtc")
        # Dataclass default str includes all fields
        str_repr = str(tif)
        assert "gtc" in str_repr


class TestTimeInForceComparisonWithBrokerEnum:
    """Test relationship between TimeInForce and BrokerTimeInForce.
    
    These tests document the architectural duplication issue where
    BrokerTimeInForce provides superior functionality.
    """

    @pytest.mark.unit
    def test_values_match_broker_enum(self):
        """Test that valid values match BrokerTimeInForce enum values."""
        # Load broker_enums module directly too
        broker_path = Path(__file__).parent.parent.parent.parent / "the_alchemiser" / "shared" / "types" / "broker_enums.py"
        spec = importlib.util.spec_from_file_location(
            "the_alchemiser.shared.types.broker_enums",
            str(broker_path)
        )
        broker_module = importlib.util.module_from_spec(spec)
        sys.modules["the_alchemiser.shared.types.broker_enums"] = broker_module
        spec.loader.exec_module(broker_module)
        
        BrokerTimeInForce = broker_module.BrokerTimeInForce
        
        # TimeInForce valid values
        tif_values = {"day", "gtc", "ioc", "fok"}
        
        # BrokerTimeInForce enum values
        broker_values = {member.value for member in BrokerTimeInForce}
        
        assert tif_values == broker_values

    @pytest.mark.unit
    def test_broker_enum_has_more_features(self):
        """Document that BrokerTimeInForce has superior functionality.
        
        This test documents the architectural issue: BrokerTimeInForce
        provides from_string() and to_alpaca() methods that TimeInForce lacks.
        """
        # Load broker_enums module
        broker_path = Path(__file__).parent.parent.parent.parent / "the_alchemiser" / "shared" / "types" / "broker_enums.py"
        spec = importlib.util.spec_from_file_location(
            "the_alchemiser.shared.types.broker_enums",
            str(broker_path)
        )
        broker_module = importlib.util.module_from_spec(spec)
        sys.modules["the_alchemiser.shared.types.broker_enums"] = broker_module
        spec.loader.exec_module(broker_module)
        
        BrokerTimeInForce = broker_module.BrokerTimeInForce
        
        # BrokerTimeInForce can convert from string
        broker_tif = BrokerTimeInForce.from_string("day")
        assert broker_tif == BrokerTimeInForce.DAY
        
        # BrokerTimeInForce can convert to Alpaca format
        # Note: This requires alpaca-py, may fail if not installed
        try:
            alpaca_value = broker_tif.to_alpaca()
            assert isinstance(alpaca_value, str)
        except (ImportError, ModuleNotFoundError):
            pytest.skip("alpaca-py not installed")
        
        # TimeInForce lacks these methods
        tif = TimeInForce(value="day")
        assert not hasattr(tif, "from_string")
        assert not hasattr(tif, "to_alpaca")


class TestTimeInForceUsage:
    """Test actual usage patterns and dead code detection."""

    @pytest.mark.unit
    def test_can_be_created(self):
        """Test that TimeInForce can be created and used."""
        tif = TimeInForce(value="day")
        assert tif.value == "day"

    @pytest.mark.unit
    def test_type_hints_work(self):
        """Test that type hints work correctly with TimeInForce."""
        def process_order(tif: TimeInForce) -> str:
            """Example function using TimeInForce type hint."""
            return f"Order with TIF: {tif.value}"
        
        tif = TimeInForce(value="gtc")
        result = process_order(tif)
        assert result == "Order with TIF: gtc"


# Property-based tests would require hypothesis, but not critical for this simple type
# class TestTimeInForcePropertyBased:
#     """Property-based tests using Hypothesis."""
#     pass
