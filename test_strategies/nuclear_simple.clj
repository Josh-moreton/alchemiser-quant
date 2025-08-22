;; Simplified Nuclear Strategy for DSL Testing
;; Tests nested conditionals and portfolio construction similar to Nuclear.clj

(if (> (rsi "SPY" {:window 10}) 79)
    (if (> (rsi "SPY" {:window 10}) 81) 
        (asset "UVXY" "ProShares Ultra VIX Short-Term Futures ETF")
        (weight-equal 
            (asset "UVXY" "ProShares Ultra VIX Short-Term Futures ETF")
            (asset "BTAL" "AGF U.S. Market Neutral Anti-Beta Fund")))
    (weight-equal
        (asset "TQQQ" "ProShares UltraPro QQQ")
        (asset "UPRO" "ProShares UltraPro S&P 500")))