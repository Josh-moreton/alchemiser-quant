from datetime import datetime

from the_alchemiser.accounting.ledger import Ledger
from the_alchemiser.execution.models import Fill


def test_accounting_fifo() -> None:
    ledger = Ledger()
    ledger.apply_fill(Fill("1", "AAPL", 10, 100, datetime(2024, 1, 1)))
    ledger.apply_fill(Fill("2", "AAPL", 5, 110, datetime(2024, 1, 1)))
    ledger.apply_fill(Fill("3", "AAPL", -8, 120, datetime(2024, 1, 2)))
    assert ledger.realised_pnl == 160
    remaining = ledger.positions["AAPL"].lots
    assert remaining[0].qty == 2
    assert remaining[1].qty == 5
