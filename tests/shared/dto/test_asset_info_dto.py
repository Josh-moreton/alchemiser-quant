"""Tests for AssetInfoDTO."""

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.dto.asset_info_dto import AssetInfoDTO


def test_asset_info_dto_creation():
    """Test basic AssetInfoDTO creation."""
    asset = AssetInfoDTO(
        symbol="AAPL",
        fractionable=True,
        name="Apple Inc.",
        exchange="NASDAQ",
        asset_class="us_equity",
        tradable=True,
        marginable=True,
        shortable=True,
    )
    
    assert asset.symbol == "AAPL"
    assert asset.fractionable is True
    assert asset.name == "Apple Inc."
    assert asset.exchange == "NASDAQ"
    assert asset.asset_class == "us_equity"
    assert asset.tradable is True
    assert asset.marginable is True
    assert asset.shortable is True


def test_asset_info_dto_symbol_normalization():
    """Test that symbol is normalized to uppercase."""
    asset = AssetInfoDTO(symbol="aapl", fractionable=True)
    assert asset.symbol == "AAPL"


def test_asset_info_dto_minimal():
    """Test AssetInfoDTO with minimal required fields."""
    asset = AssetInfoDTO(symbol="EDZ", fractionable=False)
    
    assert asset.symbol == "EDZ"
    assert asset.fractionable is False
    assert asset.name is None
    assert asset.exchange is None
    assert asset.asset_class is None
    assert asset.tradable is True  # Default value
    assert asset.marginable is None
    assert asset.shortable is None


def test_asset_info_dto_non_fractionable():
    """Test creating DTO for known non-fractionable asset."""
    asset = AssetInfoDTO(
        symbol="EDZ",
        fractionable=False,
        name="Direxion Daily MSCI Emerging Markets Bear 3X Shares",
        asset_class="us_equity",
    )
    
    assert asset.symbol == "EDZ"
    assert asset.fractionable is False


def test_asset_info_dto_validation_errors():
    """Test validation errors for invalid inputs."""
    # Missing required fractionable field
    with pytest.raises(ValidationError):
        AssetInfoDTO(symbol="AAPL")
    
    # Empty symbol
    with pytest.raises(ValidationError):
        AssetInfoDTO(symbol="", fractionable=True)
    
    # Invalid symbol type
    with pytest.raises(ValidationError):
        AssetInfoDTO(symbol=123, fractionable=True)  # type: ignore[arg-type]


def test_asset_info_dto_immutable():
    """Test that DTO is immutable."""
    asset = AssetInfoDTO(symbol="AAPL", fractionable=True)
    
    with pytest.raises(ValidationError):
        asset.symbol = "MSFT"  # type: ignore[misc]


def test_asset_info_dto_serialization():
    """Test serialization/deserialization."""
    asset = AssetInfoDTO(
        symbol="AAPL",
        fractionable=True,
        name="Apple Inc.",
        exchange="NASDAQ",
    )
    
    # Test dict serialization
    asset_dict = asset.model_dump()
    assert asset_dict["symbol"] == "AAPL"
    assert asset_dict["fractionable"] is True
    assert asset_dict["name"] == "Apple Inc."
    
    # Test deserialization
    restored_asset = AssetInfoDTO.model_validate(asset_dict)
    assert restored_asset == asset