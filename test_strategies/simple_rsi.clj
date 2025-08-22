;; Simple test strategy for DSL engine
;; Tests basic RSI-based conditional logic

(if (> (rsi "SPY" {:window 10}) 50)
    (weight-equal 
        (asset "TQQQ" "ProShares UltraPro QQQ")
        (asset "UPRO" "ProShares UltraPro S&P 500"))
    (asset "UVXY" "ProShares Ultra VIX Short-Term Futures"))