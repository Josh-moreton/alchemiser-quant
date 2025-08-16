import os
from collections.abc import Callable

import pytest


def _set_flag(monkeypatch: pytest.MonkeyPatch, value: str | None) -> None:
    env_name = "TYPES_V2_ENABLED"
    if value is None:
        monkeypatch.delenv(env_name, raising=False)
    else:
        monkeypatch.setenv(env_name, value)


@pytest.fixture
def types_flag(monkeypatch: pytest.MonkeyPatch) -> Callable[[bool | None], None]:
    """Control the TYPES_V2 feature flag within a test.

    Pass True/False/None to enable, disable or clear the flag respectively.
    """
    def setter(enabled: bool | None) -> None:
        _set_flag(monkeypatch, "1" if enabled else ("0" if enabled is not None else None))

    return setter
