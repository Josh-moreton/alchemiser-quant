"""Latency model stubs."""

from dataclasses import dataclass


@dataclass
class LatencyModel:
    """Placeholder latency model."""

    inbound_ms: int
    exchange_ms: int
    outbound_ms: int

    def total(self) -> int:  # pragma: no cover - trivial
        return self.inbound_ms + self.exchange_ms + self.outbound_ms
