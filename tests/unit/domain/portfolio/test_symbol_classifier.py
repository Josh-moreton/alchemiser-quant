"""Test the SymbolClassifier."""

from the_alchemiser.domain.portfolio.attribution.symbol_classifier import SymbolClassifier


class TestSymbolClassifier:
    """Test cases for SymbolClassifier."""

    def test_classify_known_large_cap_symbols(self):
        """Test classification of known large cap symbols."""
        classifier = SymbolClassifier()

        # Test major tech stocks
        assert classifier.classify_symbol("AAPL") == "large_cap"
        assert classifier.classify_symbol("MSFT") == "large_cap"
        assert classifier.classify_symbol("GOOGL") == "large_cap"
        assert classifier.classify_symbol("AMZN") == "large_cap"
        assert classifier.classify_symbol("NVDA") == "large_cap"
        assert classifier.classify_symbol("META") == "large_cap"
        assert classifier.classify_symbol("TSLA") == "large_cap"

        # Test major financial stocks
        assert classifier.classify_symbol("JPM") == "large_cap"
        assert classifier.classify_symbol("BAC") == "large_cap"
        assert classifier.classify_symbol("WFC") == "large_cap"

        # Test major consumer stocks
        assert classifier.classify_symbol("JNJ") == "large_cap"
        assert classifier.classify_symbol("PG") == "large_cap"
        assert classifier.classify_symbol("KO") == "large_cap"

    def test_classify_known_mid_cap_symbols(self):
        """Test classification of known mid cap symbols."""
        classifier = SymbolClassifier()

        # Test known mid cap stocks
        assert classifier.classify_symbol("ROKU") == "mid_cap"
        assert classifier.classify_symbol("SNAP") == "mid_cap"
        assert classifier.classify_symbol("PINS") == "mid_cap"
        assert classifier.classify_symbol("SPOT") == "mid_cap"
        assert classifier.classify_symbol("TWLO") == "mid_cap"

    def test_classify_known_small_cap_symbols(self):
        """Test classification of known small cap symbols."""
        classifier = SymbolClassifier()

        # Test known small cap stocks
        assert classifier.classify_symbol("RBLX") == "small_cap"
        assert classifier.classify_symbol("HOOD") == "small_cap"
        assert classifier.classify_symbol("COIN") == "small_cap"

    def test_classify_crypto_symbols(self):
        """Test classification of crypto symbols."""
        classifier = SymbolClassifier()

        assert classifier.classify_symbol("BTC") == "crypto"
        assert classifier.classify_symbol("ETH") == "crypto"
        assert classifier.classify_symbol("ADA") == "crypto"
        assert classifier.classify_symbol("SOL") == "crypto"
        assert classifier.classify_symbol("DOGE") == "crypto"

    def test_classify_bond_symbols(self):
        """Test classification of bond symbols."""
        classifier = SymbolClassifier()

        # Test treasury ETFs
        assert classifier.classify_symbol("TLT") == "bonds"
        assert classifier.classify_symbol("IEF") == "bonds"
        assert classifier.classify_symbol("SHY") == "bonds"

        # Test corporate bond ETFs
        assert classifier.classify_symbol("LQD") == "bonds"
        assert classifier.classify_symbol("HYG") == "bonds"

    def test_classify_index_fund_symbols(self):
        """Test classification of index fund symbols."""
        classifier = SymbolClassifier()

        # Test major index ETFs
        assert classifier.classify_symbol("SPY") == "index_funds"
        assert classifier.classify_symbol("QQQ") == "index_funds"
        assert classifier.classify_symbol("IWM") == "index_funds"
        assert classifier.classify_symbol("VTI") == "index_funds"
        assert classifier.classify_symbol("VOO") == "index_funds"

    def test_classify_unknown_symbols(self):
        """Test classification of unknown symbols."""
        classifier = SymbolClassifier()

        # Test completely unknown symbols
        assert classifier.classify_symbol("UNKNOWN123") == "unknown"
        assert classifier.classify_symbol("XYZ") == "unknown"
        assert classifier.classify_symbol("FAKE") == "unknown"

    def test_classify_empty_symbol(self):
        """Test classification of empty symbol."""
        classifier = SymbolClassifier()

        assert classifier.classify_symbol("") == "unknown"
        assert classifier.classify_symbol(None) == "unknown"

    def test_classify_case_insensitive(self):
        """Test that classification is case insensitive."""
        classifier = SymbolClassifier()

        # Test lowercase
        assert classifier.classify_symbol("aapl") == "large_cap"
        assert classifier.classify_symbol("msft") == "large_cap"

        # Test mixed case
        assert classifier.classify_symbol("AaPl") == "large_cap"
        assert classifier.classify_symbol("MsFt") == "large_cap"

    def test_get_all_strategies(self):
        """Test getting all available strategies."""
        classifier = SymbolClassifier()

        strategies = classifier.get_all_strategies()

        expected_strategies = {
            "large_cap", "mid_cap", "small_cap", "crypto",
            "bonds", "index_funds", "unknown"
        }

        assert strategies == expected_strategies

    def test_is_equity_strategy(self):
        """Test checking if a strategy is equity-based."""
        classifier = SymbolClassifier()

        # Equity strategies
        assert classifier.is_equity_strategy("large_cap") is True
        assert classifier.is_equity_strategy("mid_cap") is True
        assert classifier.is_equity_strategy("small_cap") is True

        # Non-equity strategies
        assert classifier.is_equity_strategy("crypto") is False
        assert classifier.is_equity_strategy("bonds") is False
        assert classifier.is_equity_strategy("index_funds") is False
        assert classifier.is_equity_strategy("unknown") is False

    def test_get_strategy_description(self):
        """Test getting strategy descriptions."""
        classifier = SymbolClassifier()

        descriptions = {
            "large_cap": "Large cap stocks (market cap > $10B)",
            "mid_cap": "Mid cap stocks (market cap $2B - $10B)",
            "small_cap": "Small cap stocks (market cap < $2B)",
            "crypto": "Cryptocurrency assets",
            "bonds": "Fixed income securities",
            "index_funds": "Broad market index funds",
            "unknown": "Unclassified securities"
        }

        for strategy, expected_desc in descriptions.items():
            assert classifier.get_strategy_description(strategy) == expected_desc

        # Test unknown strategy
        assert classifier.get_strategy_description("invalid") == "Unknown strategy"
