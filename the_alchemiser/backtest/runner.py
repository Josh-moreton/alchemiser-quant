"""Backtest runner orchestrating data flow and execution."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..accounting.ledger import Ledger
from ..brokers.base import Broker
from ..brokers.simulated_broker import SimulatedBroker
from ..data.replayer import MarketDataReplayer
from ..execution.engine import ExecutionEngine
from .artefacts import ArtefactWriter
from .config_schema import BacktestConfig


class BacktestRunner:
    """Tie together replayer, broker and ledger."""

    def __init__(
        self,
        broker: Broker,
        replayer: MarketDataReplayer,
        ledger: Ledger,
        artefacts: ArtefactWriter,
    ) -> None:
        self.broker = broker
        self.replayer = replayer
        self.ledger = ledger
        self.artefacts = artefacts

    def run(self) -> dict[str, float]:
        for event in self.replayer:
            self.broker.on_market_event(event)
        stats = {"realised_pnl": self.ledger.realised_pnl, "cash": self.ledger.cash}
        self.artefacts.write_orders(self.broker.list_orders())
        self.artefacts.write_fills(self.broker.fills)
        self.artefacts.write_stats(stats)
        return stats

    @staticmethod
    def from_config(cfg: BacktestConfig, symbols: list[str], artefact_dir: Path) -> BacktestRunner:
        replayer = MarketDataReplayer.synthetic(
            start=datetime.combine(cfg.start, datetime.min.time()),
            end=datetime.combine(cfg.end, datetime.min.time()),
            symbols=symbols,
            seed=cfg.seed,
            interval_minutes=int(cfg.bar_interval.rstrip("m")),
        )
        ledger = Ledger()
        engine = ExecutionEngine()
        broker = SimulatedBroker(engine, ledger)
        artefacts = ArtefactWriter(artefact_dir)
        return BacktestRunner(broker=broker, replayer=replayer, ledger=ledger, artefacts=artefacts)
