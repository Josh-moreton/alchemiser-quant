"""Business Unit: order execution/placement; Status: current.

Canonical lowercase order status literals for system boundaries.

Purpose
-------
These literals are the *interface contract* for order status values that move
across serialization boundaries (DTOs, TypedDicts, CLI / API responses). They
are intentionally lowercase and minimal. The domain core uses the
`OrderStatus` enum (uppercase) for internal logic; conversion between the two
is performed in the application mapping layer (anti-corruption layer).

Why keep ``expired`` separate here?
----------------------------------
Externally we may receive ``expired`` from upstream providers or internal
timed-out workflows. Strategically we want to preserve that nuance for
reporting / observability (e.g. distinguishing an order that lapsed vs one
explicitly rejected by the broker). However, the current domain enum does not
model that distinction; both ``expired`` and any hard failures collapse to
``REJECTED`` inside the core domain (see mapping in `OrderModel.from_dict`).

Rationale:
* Interface layer: fidelity & user messaging (show "expired" if that is what
    the upstream produced).
* Domain layer: simplified state machine (avoids an additional terminal state
    until business rules need to branch on it).
* Future-proofing: if the domain later differentiates expiration handling we
    can promote ``EXPIRED`` to the enum without breaking boundary contracts.

Mapping policy summary
----------------------
raw/provider statuses  -->  normalized literal  -->  domain enum
``expired``            -->  ``expired``         -->  ``REJECTED`` (currently)
Other terminal rejects -->  ``rejected``        -->  ``REJECTED``

Any unknown raw status defaults conservatively to ``new`` while emitting a
warning (see `normalize_order_status`). This avoids silent data loss while
remaining resilient to upstream drift.
"""

from __future__ import annotations

from typing import Literal

# Keep "expired" as a distinct literal for interface/display purposes even
# though the domain enum collapses it into REJECTED. Normalization returns
# "expired" when the raw status is exactly that token so downstream code can
# differentiate if desired at the presentation layer.
OrderStatusLiteral = Literal[
    "new",
    "partially_filled",
    "filled",
    "canceled",
    "expired",
    "rejected",
]

__all__ = ["OrderStatusLiteral"]
