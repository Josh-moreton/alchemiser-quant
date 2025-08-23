"""Tests for confidence configuration module."""

from decimal import Decimal

from the_alchemiser.domain.strategies.config import (
    AggregationConfig,
    ConfidenceConfig,
    KLMConfidenceConfig,
    NuclearConfidenceConfig,
    TECLConfidenceConfig,
    get_confidence_thresholds,
    load_confidence_config,
)


class TestConfidenceConfig:
    """Test the confidence configuration classes."""

    def test_tecl_config_defaults(self):
        """Test TECL configuration default values."""
        config = TECLConfidenceConfig()

        assert config.base_confidence == Decimal("0.6")
        assert config.max_confidence == Decimal("0.9")
        assert config.min_confidence == Decimal("0.3")
        assert config.rsi_oversold_threshold == Decimal("30")
        assert config.rsi_overbought_threshold == Decimal("70")

    def test_nuclear_config_defaults(self):
        """Test Nuclear configuration default values."""
        config = NuclearConfidenceConfig()

        assert config.base_confidence == Decimal("0.5")
        assert config.extremely_oversold_rsi == Decimal("20")
        assert config.extremely_oversold_confidence == Decimal("0.9")
        assert config.oversold_buy_confidence == Decimal("0.85")

    def test_klm_config_defaults(self):
        """Test KLM configuration default values."""
        config = KLMConfidenceConfig()

        assert config.base_confidence == Decimal("0.5")
        assert config.buy_base_confidence == Decimal("0.5")
        assert config.buy_weight_multiplier == Decimal("0.4")
        assert config.sell_confidence == Decimal("0.7")
        assert config.hold_confidence == Decimal("0.3")

    def test_aggregation_config_defaults(self):
        """Test aggregation configuration default values."""
        config = AggregationConfig()

        assert config.min_buy_confidence == Decimal("0.55")
        assert config.min_sell_confidence == Decimal("0.55")
        assert config.min_hold_confidence == Decimal("0.35")
        assert config.strategy_priority_order == ("NUCLEAR", "TECL", "KLM")
        assert config.enable_confidence_gating is True

    def test_master_config_composition(self):
        """Test that master config contains all sub-configs."""
        config = ConfidenceConfig()

        assert isinstance(config.tecl, TECLConfidenceConfig)
        assert isinstance(config.nuclear, NuclearConfidenceConfig)
        assert isinstance(config.klm, KLMConfidenceConfig)
        assert isinstance(config.aggregation, AggregationConfig)

    def test_load_confidence_config(self):
        """Test loading confidence configuration."""
        config = load_confidence_config()

        assert isinstance(config, ConfidenceConfig)
        assert config.tecl.base_confidence == Decimal("0.6")

    def test_get_confidence_thresholds(self):
        """Test getting confidence thresholds by action."""
        thresholds = get_confidence_thresholds()

        assert "BUY" in thresholds
        assert "SELL" in thresholds
        assert "HOLD" in thresholds
        assert thresholds["BUY"] == Decimal("0.55")
        assert thresholds["SELL"] == Decimal("0.55")
        assert thresholds["HOLD"] == Decimal("0.35")

    def test_confidence_values_in_valid_range(self):
        """Test that all confidence values are in valid [0, 1] range."""
        config = ConfidenceConfig()

        # TECL config values
        assert Decimal("0") <= config.tecl.base_confidence <= Decimal("1")
        assert Decimal("0") <= config.tecl.min_confidence <= Decimal("1")
        assert Decimal("0") <= config.tecl.max_confidence <= Decimal("1")

        # Nuclear config values
        assert Decimal("0") <= config.nuclear.base_confidence <= Decimal("1")
        assert Decimal("0") <= config.nuclear.extremely_oversold_confidence <= Decimal("1")
        assert Decimal("0") <= config.nuclear.oversold_buy_confidence <= Decimal("1")

        # KLM config values
        assert Decimal("0") <= config.klm.base_confidence <= Decimal("1")
        assert Decimal("0") <= config.klm.sell_confidence <= Decimal("1")
        assert Decimal("0") <= config.klm.hold_confidence <= Decimal("1")

        # Aggregation thresholds
        assert Decimal("0") <= config.aggregation.min_buy_confidence <= Decimal("1")
        assert Decimal("0") <= config.aggregation.min_sell_confidence <= Decimal("1")
        assert Decimal("0") <= config.aggregation.min_hold_confidence <= Decimal("1")


class TestConfidenceConfigValidation:
    """Test confidence configuration validation and constraints."""

    def test_tecl_confidence_ordering(self):
        """Test that TECL confidence values follow logical ordering."""
        config = TECLConfidenceConfig()

        assert config.min_confidence <= config.base_confidence <= config.max_confidence

    def test_nuclear_rsi_thresholds_ordering(self):
        """Test that Nuclear RSI thresholds are in correct order."""
        config = NuclearConfidenceConfig()

        assert config.extremely_oversold_rsi <= config.oversold_rsi
        assert config.overbought_rsi <= config.extremely_overbought_rsi
        assert config.oversold_rsi < config.overbought_rsi

    def test_klm_buy_confidence_calculation_bounds(self):
        """Test that KLM buy confidence calculation stays within bounds."""
        config = KLMConfidenceConfig()

        # Test at maximum weight (1.0)
        max_buy_confidence = config.buy_base_confidence + Decimal("1.0") * config.buy_weight_multiplier
        assert max_buy_confidence <= config.buy_max_confidence

    def test_aggregation_thresholds_logical(self):
        """Test that aggregation thresholds are logically ordered."""
        config = AggregationConfig()

        # HOLD should have lower threshold than BUY/SELL
        assert config.min_hold_confidence <= config.min_buy_confidence
        assert config.min_hold_confidence <= config.min_sell_confidence
