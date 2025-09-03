"""Business Unit: shared | Status: current.."""
        timestamp_raw = data["timestamp"]
        timestamp_parsed = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))

        return cls(
            symbol=data["symbol"],
            price=data["price"],
            timestamp=timestamp_parsed,
            bid=data.get("bid"),
            ask=data.get("ask"),
            volume=data.get("volume"),
        )

    def to_dict(self) -> PriceData:
        """Convert to PriceData TypedDict."""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "bid": self.bid,
            "ask": self.ask,
            "volume": self.volume,
        }

    @property
    def has_quote_data(self) -> bool:
        """Check if bid/ask data is available."""
        return self.bid is not None and self.ask is not None


def bars_to_dataframe(bars: list[BarModel]) -> pd.DataFrame:
    """Convert list of BarModel to pandas DataFrame."""
    if not bars:
        return pd.DataFrame()

    data = {
        "Open": [bar.open for bar in bars],
        "High": [bar.high for bar in bars],
        "Low": [bar.low for bar in bars],
        "Close": [bar.close for bar in bars],
        "Volume": [bar.volume for bar in bars],
    }

    df = pd.DataFrame(data, index=[bar.timestamp for bar in bars])
    df.index.name = "Date"
    return df


def dataframe_to_bars(df: pd.DataFrame, symbol: str) -> list[BarModel]:
    """Convert pandas DataFrame to list of BarModel."""
    bars = []
    for timestamp, row in df.iterrows():
        bars.append(
            BarModel(
                symbol=symbol,
                timestamp=timestamp,
                open=row["Open"],
                high=row["High"],
                low=row["Low"],
                close=row["Close"],
                volume=int(row.get("Volume", 0)),
            )
        )
    return bars
