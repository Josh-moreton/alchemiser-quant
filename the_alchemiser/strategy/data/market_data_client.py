#!/usr/bin/env python3
"""Business Unit: strategy | Status: current..

        Args:
            symbol: Stock symbol
            start: Start datetime
            end: End datetime
            timeframe: TimeFrame enum or string

        Returns:
            List of bar objects

        Raises:
            MarketDataError: If data retrieval fails

        """
        try:
            # Handle timeframe parameter
            if timeframe is None:
                timeframe = TimeFrame.Day
            elif isinstance(timeframe, str):
                # Convert string to TimeFrame enum
                timeframe_mapping = {
                    "Day": TimeFrame.Day,
                    "Hour": TimeFrame.Hour,
                    "Minute": TimeFrame.Minute,
                    "1d": TimeFrame.Day,
                    "1h": TimeFrame.Hour,
                    "1m": TimeFrame.Minute,
                }
                timeframe = timeframe_mapping.get(timeframe, TimeFrame.Day)

            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=cast(TimeFrame, timeframe),
                start=start,
                end=end,
            )

            # Fetch data using AlpacaManager's data client
            bars = self._alpaca_manager._data_client.get_stock_bars(request)

            # Extract bars for the symbol safely
            bar_data = self._extract_bar_data(bars, symbol)
            return list(bar_data) if bar_data else []

        except Exception as e:
            raise MarketDataError(
                f"Failed to fetch historical data for {symbol} from {start} to {end}: {e}"
            ) from e

    def get_latest_quote(self, symbol: str) -> tuple[float, float]:
        """Get the latest bid and ask quote for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (bid, ask) prices

        Raises:
            MarketDataError: If quote retrieval fails

        """
        try:
            quote = self._alpaca_manager.get_latest_quote(symbol)

            if quote:
                bid = float(getattr(quote, "bid_price", 0) or 0)
                ask = float(getattr(quote, "ask_price", 0) or 0)
                return bid, ask

            return 0.0, 0.0

        except Exception as e:
            logging.error(f"Failed to fetch latest quote for {symbol}: {e}")
            return 0.0, 0.0

    def get_current_price_from_quote(self, symbol: str) -> float | None:
        """Get current price from the latest quote.

        Args:
            symbol: Stock symbol

        Returns:
            Current price or None if unavailable

        """
        try:
            quote = self._alpaca_manager.get_latest_quote(symbol)

            if quote:
                # Use mid-point of bid-ask spread
                bid = float(getattr(quote, "bid_price", 0) or 0)
                ask = float(getattr(quote, "ask_price", 0) or 0)

                if bid > 0 and ask > 0:
                    return (bid + ask) / 2

            return None

        except Exception as e:
            logging.error(f"Failed to get current price from quote for {symbol}: {e}")
            return None

    def _extract_bar_data(self, bars: Any, symbol: str) -> Any:  # noqa: ANN401  # Alpaca API response object with dynamic structure
        """Extract bar data from API response."""
        try:
            # Try direct symbol access first (most common)
            if hasattr(bars, symbol):
                return getattr(bars, symbol)
            # Try data dictionary access as fallback
            if hasattr(bars, "data"):
                data_dict = getattr(bars, "data", {})
                if hasattr(data_dict, "get"):
                    return data_dict.get(symbol, [])
                if symbol in data_dict:
                    return data_dict[symbol]
        except (AttributeError, KeyError, TypeError):
            pass

        return None

    def _convert_to_dataframe(self, bar_data: Any) -> pd.DataFrame:  # noqa: ANN401  # Bar data from Alpaca API with dynamic structure
        """Convert bar data to pandas DataFrame."""
        data_rows = []
        timestamps = []

        for bar in bar_data:
            if hasattr(bar, "open") and hasattr(bar, "high"):  # Validate bar structure
                data_rows.append(
                    {
                        "Open": float(bar.open),
                        "High": float(bar.high),
                        "Low": float(bar.low),
                        "Close": float(bar.close),
                        "Volume": int(bar.volume) if hasattr(bar, "volume") else 0,
                    }
                )
                timestamps.append(bar.timestamp)

        if not data_rows:
            return pd.DataFrame()

        # Create DataFrame with datetime index
        df = pd.DataFrame(data_rows)
        df.index = pd.to_datetime(timestamps)
        df.index.name = "Date"

        return df
