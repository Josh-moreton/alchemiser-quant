"""Disable outbound network access for tests by default."""

import socket

import pytest


class NetworkBlockedError(RuntimeError):
    pass


def _guard(*args, **kwargs):  # pragma: no cover - simple guard
    raise NetworkBlockedError("Network access disabled during tests")


@pytest.fixture(autouse=True)
def disable_network(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    if request.node.get_closest_marker("enable_network"):
        return
    monkeypatch.setattr(socket, "socket", _guard)
