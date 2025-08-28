"""Business Unit: utilities; Status: current.

Infrastructure layer integrations.

Adapters to external systems (Alpaca, AWS, WebSocket streaming, secrets, logging).
Keep side-effects minimal at import time; postpone network/service initialization until
explicit factory or builder calls. This ensures safer packaging and faster cold starts.
"""

from __future__ import annotations

__all__: list[str] = []
