"""Business Unit: order execution/placement; Status: current.

Execution bounded context package.

This bounded context is responsible for:
- Order intent validation and lifecycle management
- Smart execution and routing strategies
- Order monitoring and fill tracking
- Broker integration and WebSocket streaming
"""

from __future__ import annotations

__all__ = [
    "application",
    "domain",
    "infrastructure",
    "interfaces", 
]