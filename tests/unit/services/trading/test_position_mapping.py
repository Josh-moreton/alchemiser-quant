from decimal import Decimal

from the_alchemiser.application.mapping.position_mapping import (
    PositionSummary,
    alpaca_position_to_summary,
)


class Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_alpaca_position_to_summary_from_dict():
    data = {
        "symbol": "AAPL",
        "qty": "10",
        "avg_entry_price": "150.00",
        "current_price": 155.25,
        "market_value": "1552.50",
        "unrealized_pl": "52.50",
        "unrealized_plpc": "0.0339",
    }

    s = alpaca_position_to_summary(data)
    assert isinstance(s, PositionSummary)
    assert s.symbol == "AAPL"
    assert s.qty == Decimal("10")
    assert s.avg_entry_price == Decimal("150.00")
    assert s.current_price == Decimal("155.25")
    assert s.market_value == Decimal("1552.50")
    assert s.unrealized_pl == Decimal("52.50")
    assert s.unrealized_plpc == Decimal("0.0339")


def test_alpaca_position_to_summary_from_obj():
    obj = Obj(
        symbol="MSFT",
        qty=5,
        avg_entry_price=310,
        current_price="315.10",
        market_value=1575.5,
        unrealized_pl=25.5,
        unrealized_plpc=0.0165,
    )

    s = alpaca_position_to_summary(obj)
    assert s.symbol == "MSFT"
    assert s.qty == Decimal("5")
    assert s.avg_entry_price == Decimal("310")
    assert s.current_price == Decimal("315.10")
    assert s.market_value == Decimal("1575.5")
    assert s.unrealized_pl == Decimal("25.5")
    assert s.unrealized_plpc == Decimal("0.0165")
