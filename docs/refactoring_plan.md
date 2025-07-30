# Refactoring Plan

This document outlines areas in the codebase where logic is repeated or overly verbose. Consolidating these into helper functions will simplify maintenance without changing trading strategy logic.

## 1. Indicator Retrieval Helper

The same `safe_get_indicator` logic appears in multiple modules.

```python
# the_alchemiser/core/trading/tecl_signals.py
```
    82	    def safe_get_indicator(self, data, indicator_func, *args, **kwargs):
    83	        """Safely get indicator value, logging exceptions to surface data problems."""
    84	        try:
    85	            result = indicator_func(data, *args, **kwargs)
    86	            if hasattr(result, 'iloc') and len(result) > 0:
    87	                value = result.iloc[-1]
    88	                # Check if value is NaN - if so, try to find the last valid value
    89	                if pd.isna(value):
    90	                    # Find the last non-NaN value
    91	                    valid_values = result.dropna()
    92	                    if len(valid_values) > 0:
    93	                        value = valid_values.iloc[-1]
    94	                    else:
    95	                        logging.error(f"No valid values for indicator {indicator_func.__name__} on data: {data}")
    96	                        return 50.0  # Fallback only if no valid values
    97	                return float(value)
    98	            logging.error(f"Indicator {indicator_func.__name__} returned no results for data: {data}")
    99	            return 50.0
   100	        except Exception as e:
   101	            logging.error(f"Exception in safe_get_indicator for {indicator_func.__name__}: {e}\nData: {data}")
   102	            return 50.0

Similar code in **nuclear_signals.py**:
```python
   108	    def safe_get_indicator(self, data, indicator_func, *args, **kwargs):
   109	        """Safely get indicator value, logging exceptions to surface data problems."""
   110	        try:
   111	            result = indicator_func(data, *args, **kwargs)
   112	            if hasattr(result, 'iloc') and len(result) > 0:
   113	                value = result.iloc[-1]
   114	                # Check if value is NaN - if so, try to find the last valid value
   115	                if pd.isna(value):
   116	                    # Find the last non-NaN value
   117	                    valid_values = result.dropna()
   118	                    if len(valid_values) > 0:
   119	                        value = valid_values.iloc[-1]
   120	                    else:
   121	                        logging.error(f"No valid values for indicator {indicator_func.__name__} on data: {data}")
   122	                        return 50.0  # Fallback only if no valid values
   123	                return float(value)
   124	            logging.error(f"Indicator {indicator_func.__name__} returned no results for data: {data}")
   125	            return 50.0
   126	        except Exception as e:
   127	            logging.error(f"Exception in safe_get_indicator for {indicator_func.__name__}: {e}\nData: {data}")
   128	            return 50.0
```
A third copy appears in **tecl_strategy_engine.py**:
```python
    80	    def safe_get_indicator(self, data, indicator_func, *args, **kwargs):
    81	        """Safely get indicator value, logging exceptions to surface data problems."""
    82	        try:
    83	            result = indicator_func(data, *args, **kwargs)
    84	            if hasattr(result, 'iloc') and len(result) > 0:
    85	                value = result.iloc[-1]
    86	                # Check if value is NaN - if so, try to find the last valid value
    87	                if pd.isna(value):
    88	                    # Find the last non-NaN value
    89	                    valid_values = result.dropna()
    90	                    if len(valid_values) > 0:
    91	                        value = valid_values.iloc[-1]
    92	                    else:
    93	                        logging.error(f"No valid values for indicator {indicator_func.__name__} on data: {data}")
    94	                        return 50.0  # Fallback only if no valid values
    95	                return float(value)
    96	            logging.error(f"Indicator {indicator_func.__name__} returned no results for data: {data}")
    97	            return 50.0
    98	        except Exception as e:
    99	            logging.error(f"Exception in safe_get_indicator for {indicator_func.__name__}: {e}\nData: {data}")
   100	            return 50.0
```

**Refactor idea:** create a shared utility like `indicator_utils.safe_get_indicator(data, func, *args, **kwargs)`.

## 2. Scalar Price Conversion

Both signal generators implement `_ensure_scalar_price` with identical logic.
```python
# the_alchemiser/core/trading/tecl_signals.py
   136	    def _ensure_scalar_price(self, price):
   137	        """Ensure price is a scalar value for JSON serialization and string formatting"""
   138	        if price is None:
   139	            return None
   140	        try:
   141	            # If it's a pandas Series or similar, get the scalar value
   142	            if hasattr(price, 'item') and callable(getattr(price, 'item')):
   143	                price = price.item()
   144	            elif hasattr(price, 'iloc'):
   145	                # If it's still a Series, get the first element
   146	                price = price.iloc[0]
   147	            # Convert to float
   148	            price = float(price)
   149	            return price if not pd.isna(price) else None
   150	        except (ValueError, TypeError, AttributeError) as e:
```
Same logic in **nuclear_signals.py**:
```python
   236	    def _ensure_scalar_price(self, price):
   237	        """Ensure price is a scalar value for JSON serialization and string formatting"""
   238	        if price is None:
   239	            return None
   240	        try:
   241	            # If it's a pandas Series or similar, get the scalar value
   242	            if hasattr(price, 'item') and callable(getattr(price, 'item')):
   243	                price = price.item()
   244	            elif hasattr(price, 'iloc'):
   245	                # If it's still a Series, get the first element
   246	                price = price.iloc[0]
   247	            # Convert to float
   248	            price = float(price)
   249	            return price if not pd.isna(price) else None
   250	        except (ValueError, TypeError, AttributeError) as e:
```

**Refactor idea:** move this logic to `utils.price.ensure_scalar(value)`.

## 3. Configuration Loading

`load_config` is almost identical in both signal generators.
```python
# the_alchemiser/core/trading/tecl_signals.py
   154	    def load_config(self):
   155	        """Load configuration"""
   156	        try:
   157	            # Try to load from S3 first, then local
   158	            from the_alchemiser.core.utils.s3_utils import get_s3_handler
   159	            import os
   160	            s3_handler = get_s3_handler()
   161	            
   162	            # Check if file exists in S3 bucket
   163	            from the_alchemiser.core.config import get_config
   164	            global_config = get_config()
   165	            s3_uri = global_config['alerts'].get('alert_config_s3', 's3://the-alchemiser-s3/alert_config.json')
   166	            if s3_handler.file_exists(s3_uri):
   167	                content = s3_handler.read_text(s3_uri)
   168	                if content:
   169	                    self.config = json.loads(content)
   170	                    return
   171	            
   172	            # Fallback to local file
   173	            if os.path.exists('alert_config.json'):
   174	                with open('alert_config.json', 'r') as f:
   175	                    self.config = json.load(f)
   176	                    return
   177	                    
   178	        except Exception as e:
   179	            logging.warning(f"Could not load alert config: {e}")
   180	            
   181	        # Default config if nothing found - use global config values
   182	        from the_alchemiser.core.config import get_config
   183	        global_config = get_config()
   184	        self.config = {
   185	            "alerts": {
   186	                "cooldown_minutes": global_config['alerts'].get('cooldown_minutes', 30)
   187	            }
   188	        }
   189	    
```
Corresponding section in **nuclear_signals.py**:
```python
   254	        """Load configuration"""
   255	        try:
   256	            # Try to load from S3 first, then local
   257	            from the_alchemiser.core.utils.s3_utils import get_s3_handler
   258	            import os
   259	            s3_handler = get_s3_handler()
   260	            
   261	            # Check if file exists in S3 bucket
   262	            from the_alchemiser.core.config import get_config
   263	            global_config = get_config()
   264	            s3_uri = global_config['alerts'].get('alert_config_s3', 's3://the-alchemiser-s3/alert_config.json')
   265	            if s3_handler.file_exists(s3_uri):
   266	                content = s3_handler.read_text(s3_uri)
   267	                if content:
   268	                    self.config = json.loads(content)
   269	                    return
   270	            
   271	            # Fallback to local file
   272	            if os.path.exists('alert_config.json'):
   273	                with open('alert_config.json', 'r') as f:
   274	                    self.config = json.load(f)
   275	                    return
   276	                    
   277	        except Exception as e:
   278	            logging.warning(f"Could not load alert config: {e}")
   279	            
   280	        # Default config if nothing found - use global config values
   281	        from the_alchemiser.core.config import get_config
   282	        global_config = get_config()
   283	        self.config = {
   284	            "alerts": {
   285	                "cooldown_minutes": global_config['alerts'].get('cooldown_minutes', 30)
   286	            }
   287	        }
   288	    
   289	    def handle_nuclear_portfolio_signal(self, symbol, action, reason, indicators, market_data=None):
```

**Refactor idea:** create a single helper (e.g., `config_loader.load_alert_config()`) used by both classes.

## 4. Repeated `run_once` Routines

The `run_once` methods share almost the same logging and display logic.
```python
# the_alchemiser/core/trading/tecl_signals.py
   228	    def run_once(self):
   229	        """Run analysis once"""
   230	        alerts = self.run_analysis()
   231	        
   232	        if alerts and len(alerts) > 0:
   233	            # Log all alerts
   234	            for alert in alerts:
   235	                self.log_alert(alert)
   236	            
   237	            # Display results
   238	            if len(alerts) > 1:
   239	                # Multi-asset TECL portfolio signal
   240	                print(f"🚨 TECL PORTFOLIO SIGNAL: {len(alerts)} assets allocated")
   241	                print(f"\n🔵 TECL PORTFOLIO ALLOCATION:")
   242	                for alert in alerts:
   243	                    if alert.action != 'HOLD':
   244	                        print(f"   🟢 {alert.action} {alert.symbol} at ${alert.price:.2f}")
   245	                        print(f"      Reason: {alert.reason}")
   246	                    else:
   247	                        print(f"   ⚪ {alert.action} {alert.symbol} at ${alert.price:.2f}")
   248	                        print(f"      Reason: {alert.reason}")
   249	            else:
   250	                # Single signal
   251	                alert = alerts[0]
   252	                if alert.action != 'HOLD':
   253	                    print(f"🚨 TECL TRADING SIGNAL: {alert.action} {alert.symbol} at ${alert.price:.2f}")
   254	                    print(f"   Reason: {alert.reason}")
   255	                else:
   256	                    print(f"📊 TECL Analysis: {alert.action} {alert.symbol} at ${alert.price:.2f}")
   257	                    print(f"   Reason: {alert.reason}")
   258	            
   259	            # Print technical indicator values for key symbols
   260	            if alerts and hasattr(self.strategy, 'calculate_indicators'):
   261	                market_data = self.strategy.get_market_data()
   262	                indicators = self.strategy.calculate_indicators(market_data)
   263	                logging.info("\n🔬 Technical Indicators Used for TECL Signal Generation:")
   264	                for symbol in ['SPY', 'XLK', 'KMLM', 'TECL']:
   265	                    if symbol in indicators:
   266	                        logging.info(f"  {symbol}: RSI(10)={indicators[symbol].get('rsi_10'):.1f}, RSI(20)={indicators[symbol].get('rsi_20'):.1f}")
   267	            
   268	            return alerts[0]  # Return first alert for compatibility
```
Another copy in **nuclear_signals.py**:
```python
   327	    def run_once(self):
   328	        """Run analysis once"""
   329	        alerts = self.run_analysis()
   330	        
   331	        if alerts and len(alerts) > 0:
   332	            # Log all alerts
   333	            for alert in alerts:
   334	                self.log_alert(alert)
   335	            
   336	            # Display results
   337	            if len(alerts) > 1:
   338	                # Nuclear portfolio signal
   339	                logging.info(f"NUCLEAR PORTFOLIO SIGNAL: {len(alerts)} stocks allocated")
   340	                logging.info(f"NUCLEAR PORTFOLIO ALLOCATION:")
   341	                for alert in alerts:
   342	                    if alert.action != 'HOLD':
   343	                        logging.info(f"   {alert.action} {alert.symbol} at ${alert.price:.2f}")
   344	                        logging.info(f"      Reason: {alert.reason}")
   345	                    else:
   346	                        logging.info(f"   {alert.action} {alert.symbol} at ${alert.price:.2f}")
   347	                        logging.info(f"      Reason: {alert.reason}")
   348	                        
   349	                # Show portfolio allocation details
   350	                portfolio = self.get_current_portfolio_allocation()
   351	                if portfolio:
   352	                    logging.info(f"PORTFOLIO DETAILS:")
   353	                    for symbol, data in portfolio.items():
   354	                        logging.info(f"   {symbol}: {data['weight']:.1%}")
   355	            else:
   356	                # Single signal
   357	                alert = alerts[0]
   358	                if alert.action != 'HOLD':
   359	                    logging.info(f"NUCLEAR TRADING SIGNAL: {alert.action} {alert.symbol} at ${alert.price:.2f}")
   360	                    logging.info(f"   Reason: {alert.reason}")
   361	                else:
   362	                    logging.info(f"Nuclear Analysis: {alert.action} {alert.symbol} at ${alert.price:.2f}")
   363	                    logging.info(f"   Reason: {alert.reason}")
   364	            
   365	            # Print technical indicator values for key symbols
   366	            if alerts and hasattr(self.strategy, 'calculate_indicators'):
   367	                market_data = self.strategy.get_market_data()
   368	                indicators = self.strategy.calculate_indicators(market_data)
   369	                logging.info("Technical Indicators Used for Signal Generation:")
   370	                for symbol in ['IOO', 'SPY', 'TQQQ', 'VTV', 'XLF']:
   371	                    if symbol in indicators:
   372	                        logging.info(f"  {symbol}: RSI(10)={indicators[symbol].get('rsi_10')}, RSI(20)={indicators[symbol].get('rsi_20')}")
   373	            
   374	            return alerts[0]  # Return first alert for compatibility
```

**Refactor idea:** factor out a helper `display_signal_results(alerts)` used by both classes.

## 5. Verbose Price Fetching

`data_provider.get_current_price_for_order` contains lengthy subscription and fallback logic.
```python
# the_alchemiser/core/data/data_provider.py
   244	    def get_current_price_for_order(self, symbol):
   245	        """
   246	        Get current price specifically for order placement with optimized subscription management.
   247	        
   248	        This method:
   249	        1. Subscribes to real-time data for the symbol
   250	        2. Gets the most accurate price available
   251	        3. Returns both price and cleanup function
   252	        
   253	        Args:
   254	            symbol: Stock symbol
   255	        Returns:
   256	            tuple: (price, cleanup_function) where cleanup_function unsubscribes
   257	        """
   258	        def cleanup():
   259	            """Cleanup function to unsubscribe after order placement."""
   260	            if self.real_time_pricing:
   261	                self.real_time_pricing.unsubscribe_after_trading(symbol)
   262	                logging.debug(f"Unsubscribed from real-time data for {symbol}")
   263	        
   264	        # Try real-time pricing with just-in-time subscription
   265	        if self.real_time_pricing and self.real_time_pricing.is_connected():
   266	            # Subscribe for trading with high priority
   267	            self.real_time_pricing.subscribe_for_trading(symbol)
   268	            logging.debug(f"Subscribed to real-time data for {symbol} (order placement)")
   269	            
   270	            # Give a moment for real-time data to flow
   271	            import time
   272	            time.sleep(0.8)  # Slightly longer wait for order placement accuracy
   273	            
   274	            # Try to get real-time price
   275	            price = self.real_time_pricing.get_current_price(symbol)
   276	            if price is not None:
   277	                logging.info(f"Using real-time price for {symbol} order: ${price:.2f}")
   278	                return price, cleanup
   279	            else:
   280	                logging.debug(f"Real-time price not yet available for {symbol}, using REST API")
   281	        
   282	        # Fallback to REST API
   283	        price = self.get_current_price_rest(symbol)
   284	        logging.info(f"Using REST API price for {symbol} order: ${price:.2f}")
   285	        return price, cleanup
   286	    
   287	    def get_current_price_rest(self, symbol):
   288	        """
   289	        Get current market price for a symbol using REST API.
   290	        
   291	        Args:
   292	            symbol: Stock symbol
   293	        Returns:
   294	            float: Current price or None if unavailable
   295	        """
   296	        try:
   297	            # Try to get latest quote
   298	            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
   299	            latest_quote = self.data_client.get_stock_latest_quote(request)
   300	            if latest_quote and symbol in latest_quote:
   301	                quote = latest_quote[symbol]
   302	                # Extract bid/ask prices safely
   303	                bid = 0.0
   304	                ask = 0.0
   305	                if hasattr(quote, 'bid_price') and quote.bid_price:
   306	                    bid = float(quote.bid_price)
   307	                if hasattr(quote, 'ask_price') and quote.ask_price:
   308	                    ask = float(quote.ask_price)
   308	                    ask = float(quote.ask_price)
   309	                # Return midpoint if both available
   310	                if bid > 0 and ask > 0:
   311	                    return (bid + ask) / 2
   312	                elif bid > 0:
   313	                    return bid
   314	                elif ask > 0:
   315	                    return ask
   316	            # Fallback to recent historical data
   317	            logging.debug(f"No current quote for {symbol}, falling back to historical data")
   318	            df = self.get_data(symbol, period="1d", interval="1m")
   319	            if df is not None and not df.empty and 'Close' in df.columns:
   320	                price = df['Close'].iloc[-1]
   321	                # Ensure scalar value
   322	                if hasattr(price, 'item'):
   323	                    price = price.item()
   324	                price = float(price)
   325	                return price if not pd.isna(price) else None
   326	            return None
   327	        except Exception as e:
   328	            logging.error(f"Error getting current price for {symbol}: {e}")
   329	            return None
   330	
   331	    def get_latest_quote(self, symbol):
   332	        """Get the latest bid and ask quote for a symbol."""
```

**Refactor idea:** break this method into helpers such as `subscribe_for_real_time(symbol)` and `extract_bid_ask(quote)`.

By consolidating these repeated patterns into utilities, the codebase will be easier to maintain without altering the trading strategies themselves.
