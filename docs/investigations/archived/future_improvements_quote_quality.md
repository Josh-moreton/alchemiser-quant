# Future Improvements: Quote Data Quality & Provider Redundancy

**Status:** Recommendations for Future Implementation  
**Priority:** Medium  
**Related Issue:** Quote data quality investigation (Oct 2025)

## Context

While investigating negative price issues, we assessed the current data provider redundancy architecture. The system already has robust redundancy, but there are opportunities for improvement.

## Current State

### Strengths ✅
- **Dual-source architecture:** Streaming (primary) + REST (validation/fallback)
- **Suspicious quote detection:** Automatically validates questionable data
- **Smart fallback logic:** Seamlessly switches between sources
- **Thread-safe quote storage:** Concurrent access handled properly

### Identified Gaps
1. **Single provider dependency:** All data comes from Alpaca (streaming + REST)
2. **No quote freshness TTL:** Stale quotes can persist in cache
3. **Limited data quality metrics:** No tracking of validation trigger rates
4. **No per-symbol price boundaries:** Can't detect extreme price movements

## Recommended Improvements

### Priority 1: Enhanced Source Validation

#### Quote Freshness TTL
**Problem:** Stale quotes can cause execution at outdated prices  
**Solution:** Implement time-to-live mechanism

```python
class QuoteWithExpiry:
    quote: QuoteModel
    expires_at: datetime
    
    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at

# In RealTimePriceStore:
def get_quote_data(self, symbol: str) -> QuoteModel | None:
    with self._quotes_lock:
        quote_entry = self._quote_data_with_ttl.get(symbol)
        if quote_entry and not quote_entry.is_expired:
            return quote_entry.quote
        return None  # Expired, force refresh
```

**Benefits:**
- Prevents execution on stale data
- Forces fresh quote fetch when needed
- Configurable TTL per use case (order placement vs. monitoring)

#### Upstream Validation in Price Store
**Problem:** Invalid quotes reach calculation logic  
**Solution:** Reject at ingestion point

```python
def update_quote_data(self, symbol: str, bid_price: Decimal, ...) -> None:
    # Validate inputs before storing
    if bid_price <= 0 or ask_price <= 0:
        logger.error(
            f"REJECTED quote for {symbol}: invalid prices "
            f"(bid={bid_price}, ask={ask_price})"
        )
        # Don't update the stored quote - keep last good value
        return
    
    # Store only valid quotes
    ...
```

**Benefits:**
- Prevents invalid data from entering system
- Maintains last known good quote
- Reduces downstream error handling

### Priority 2: Data Quality Metrics

#### Metric Collection
Track key indicators of data quality:

```python
class QuoteQualityMetrics:
    suspicious_quotes_count: Counter  # By symbol
    rest_validation_triggers: Counter  # By symbol
    quote_rejections: Counter  # By symbol and reason
    avg_quote_age: Gauge  # In milliseconds
    streaming_gaps: Counter  # Missed updates
```

**Alerting Thresholds:**
- Suspicious quotes > 10/hour for a symbol
- REST validation triggers > 20% of quotes
- Average quote age > 2000ms
- Streaming gaps > 5/minute

#### Dashboard Integration
- Real-time quote quality dashboard
- Symbol-specific health indicators
- Historical trend analysis
- Automated alerts on degradation

### Priority 3: Multiple Data Providers (Long-term)

#### Additional Provider Options
1. **Polygon.io** - High-frequency market data
2. **IEX Cloud** - Reliable institutional data
3. **Twelve Data** - Cost-effective backup

#### Quote Consensus Algorithm
When multiple providers available:

```python
def get_consensus_quote(symbol: str) -> QuoteModel:
    quotes = [
        alpaca_provider.get_quote(symbol),
        polygon_provider.get_quote(symbol),
        iex_provider.get_quote(symbol),
    ]
    
    # Remove None values
    valid_quotes = [q for q in quotes if q]
    
    if len(valid_quotes) >= 2:
        # Use median bid/ask across providers
        return calculate_median_quote(valid_quotes)
    
    # Fallback to single provider
    return valid_quotes[0] if valid_quotes else None
```

**Benefits:**
- Protection against single provider outages
- Detection of provider-specific data issues
- Improved data reliability through consensus

**Costs:**
- Additional API subscription costs
- Increased latency (multiple provider calls)
- More complex error handling

### Priority 4: Symbol-Specific Safeguards

#### Price Movement Circuit Breakers
**Problem:** Extreme price movements may indicate bad data  
**Solution:** Per-symbol price boundaries

```python
class SymbolPriceBounds:
    symbol: str
    last_known_price: Decimal
    max_move_percent: Decimal = Decimal("20.0")  # 20% max move
    
    def is_price_reasonable(self, new_price: Decimal) -> bool:
        if not self.last_known_price:
            return True  # No history, accept
        
        move_percent = abs((new_price - self.last_known_price) / self.last_known_price * 100)
        return move_percent <= self.max_move_percent

# Usage:
bounds = SymbolPriceBounds(symbol="AAPL", last_known_price=Decimal("150.00"))
if not bounds.is_price_reasonable(new_quote.mid_price):
    logger.warning(f"Extreme price move detected for {symbol}, validating...")
    # Trigger additional validation
```

**Benefits:**
- Catches obviously bad data
- Prevents execution at extreme prices
- Configurable per symbol volatility

#### Volume-Based Validation
**Problem:** Zero or extremely low volume may indicate data issues  
**Solution:** Validate bid/ask sizes

```python
def validate_quote_volume(quote: QuoteModel) -> bool:
    MIN_VOLUME = Decimal("10.0")  # Minimum 10 shares
    
    if quote.bid_size < MIN_VOLUME or quote.ask_size < MIN_VOLUME:
        logger.warning(
            f"Low volume quote for {quote.symbol}: "
            f"bid_size={quote.bid_size}, ask_size={quote.ask_size}"
        )
        return False
    
    return True
```

## Implementation Roadmap

### Phase 1: Quick Wins (1-2 weeks)
- [ ] Implement quote freshness TTL
- [ ] Add upstream validation in RealTimePriceStore
- [ ] Deploy data quality metrics collection
- [ ] Set up basic alerting

### Phase 2: Enhanced Monitoring (2-4 weeks)
- [ ] Build quote quality dashboard
- [ ] Implement per-symbol price boundaries
- [ ] Add volume-based validation
- [ ] Create runbooks for common issues

### Phase 3: Multi-Provider (8-12 weeks)
- [ ] Evaluate additional provider options
- [ ] Implement quote consensus algorithm
- [ ] Build provider health monitoring
- [ ] Conduct cost-benefit analysis
- [ ] Gradual rollout with A/B testing

## Cost Considerations

### Development Time
- Phase 1: 40-60 hours
- Phase 2: 60-80 hours
- Phase 3: 160-200 hours

### Operational Costs
- Additional data providers: $200-500/month per provider
- Monitoring/alerting infrastructure: $50-100/month
- Increased API usage: ~10-20% higher costs

### Expected Benefits
- **Reduced failed orders:** 90%+ reduction in price-related failures
- **Improved fill quality:** Better execution prices
- **Lower support burden:** Fewer data quality incidents
- **Risk mitigation:** Protection against single provider issues

## Success Metrics

Track these KPIs after implementation:

1. **Quote Quality Score:** % of quotes passing validation (target: >99%)
2. **Failed Order Rate:** Orders failing due to price issues (target: <0.1%)
3. **Average Quote Age:** Time from quote generation to usage (target: <500ms)
4. **Provider Uptime:** Availability of quote data (target: >99.9%)
5. **REST Validation Rate:** % of streaming quotes requiring validation (target: <5%)

## References

- **Investigation Report:** `docs/investigations/quote_data_quality_investigation.md`
- **Current Implementation:** `the_alchemiser/execution_v2/core/smart_execution_strategy/quotes.py`
- **Price Store:** `the_alchemiser/shared/services/real_time_price_store.py`
- **Pricing Service:** `the_alchemiser/shared/services/real_time_pricing.py`
