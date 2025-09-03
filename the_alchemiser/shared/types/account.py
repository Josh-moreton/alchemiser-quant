"""Business Unit: shared | Status: current.."""
        return self.equity[-1] if self.equity else None

    @property
    def latest_pnl(self) -> float | None:
        """Get the latest P&L value."""
        return self.profit_loss[-1] if self.profit_loss else None
