;; Test strategy for backtesting integration tests
;; Only trades SPY with equal weight allocation

(defsymphony
  "Minimal test strategy for integration tests"
  {:asset-class "EQUITIES", :rebalance-threshold 0.1}
  (weight-equal
    [(asset "SPY" "S&P 500 ETF")]))
