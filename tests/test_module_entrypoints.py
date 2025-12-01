from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from the_alchemiser.execution_v2.__main__ import main as execution_main
from the_alchemiser.execution_v2.adapters.transports import ExecutionTransports
from the_alchemiser.portfolio_v2.__main__ import main as portfolio_main
from the_alchemiser.portfolio_v2.adapters.transports import PortfolioTransports
from the_alchemiser.strategy_v2.__main__ import main as strategy_main
from the_alchemiser.strategy_v2.adapters.transports import StrategyTransports


@dataclass
class FakeEventBus:
    published: list[Any] = field(default_factory=list)
    subscriptions: dict[str, list[Any]] = field(default_factory=dict)

    def publish(self, event: Any) -> None:
        self.published.append(event)

    def subscribe(self, event_type: str, handler: Any) -> None:
        self.subscriptions.setdefault(event_type, []).append(handler)


@dataclass
class FakeHttpClient:
    sent: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.sent.append((path, payload))
        return {"path": path, "payload": payload}


def test_strategy_entrypoint_accepts_fake_transports() -> None:
    fake_bus = FakeEventBus()
    transports = StrategyTransports(event_bus=fake_bus, http_client=FakeHttpClient())

    container = strategy_main(env="test", transports=transports)

    assert container.strategy_transports is transports
    assert set(fake_bus.subscriptions.keys()) == {"StartupEvent", "WorkflowStarted"}


def test_portfolio_entrypoint_accepts_fake_transports() -> None:
    fake_bus = FakeEventBus()
    transports = PortfolioTransports(event_bus=fake_bus, http_client=FakeHttpClient())

    container = portfolio_main(env="test", transports=transports)

    assert container.portfolio_transports is transports
    assert set(fake_bus.subscriptions.keys()) == {"SignalGenerated"}


def test_execution_entrypoint_accepts_fake_transports() -> None:
    fake_bus = FakeEventBus()
    transports = ExecutionTransports(event_bus=fake_bus, http_client=FakeHttpClient())

    container = execution_main(env="test", transports=transports)

    assert container.execution_transports is transports
    assert set(fake_bus.subscriptions.keys()) == {"RebalancePlanned"}

