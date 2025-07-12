(defsymphony
 "Holy Grail simplified (Invest Copy)"
 {:asset-class "EQUITIES", :rebalance-threshold 0.03}
 (weight-equal
  [(if
    (>
     (current-price "TQQQ")
     (moving-average-price "TQQQ" {:window 200}))
    [(weight-equal
      [(if
        (> (rsi "QQQ" {:window 10}) 80)
        [(asset "UVXY" "ProShares Ultra VIX Short-Term Futures ETF")]
        [(asset "TQQQ" "ProShares UltraPro QQQ")])])]
    [(weight-equal
      [(if
        (< (rsi "TQQQ" {:window 10}) 31)
        [(asset "TECL" "Direxion Daily Technology Bull 3x Shares")]
        [(weight-equal
          [(if
            (< (rsi "UPRO" {:window 10}) 31)
            [(asset "UPRO" "ProShares UltraPro S&P500")]
            [(weight-equal
              [(if
                (>
                 (current-price "TQQQ")
                 (moving-average-price "TQQQ" {:window 20}))
                [(asset "TQQQ" "ProShares UltraPro QQQ")]
                [(weight-equal
                  [(filter
                    (rsi {:window 10})
                    (select-top 1)
                    [(asset "TLT" "iShares 20+ Year Treasury Bond ETF")
                     (asset
                      "SQQQ"
                      "ProShares UltraPro Short QQQ")])])])])])])])])])]))
