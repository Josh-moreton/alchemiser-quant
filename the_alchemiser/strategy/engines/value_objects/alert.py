"""Business Unit: strategy | Status: current..now(UTC))

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        if self.severity not in ("INFO", "WARNING", "ERROR"):
            raise ValueError("Invalid alert severity")
