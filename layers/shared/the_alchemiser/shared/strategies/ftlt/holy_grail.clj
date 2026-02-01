(defsymphony
 "The Holy Grail"
 {:asset-class "EQUITIES", :rebalance-threshold 0.05}
 (weight-equal
  [(if
    (>
     (current-price "TQQQ")
     (moving-average-price "TQQQ" {:window 200}))
    [(weight-equal
      [(if
        (> (rsi "TQQQ" {:window 10}) 79)
        [(asset "UVXY" "ProShares Ultra VIX Short-Term Futures ETF")]
        [(asset "TQQQ" "ProShares UltraPro QQQ")])])]
    [(weight-equal
      [(if
        (< (rsi "TQQQ" {:window 10}) 31)
        [(asset "TECL" "Direxion Daily Technology Bull 3x Shares")]
        [(weight-equal
          [(if
            (< (rsi "SOXL" {:window 10}) 30)
            [(asset
              "SOXL"
              "Direxion Daily Semiconductor Bull 3x Shares")]
            [(weight-equal
              [(if
                (<
                 (current-price "TQQQ")
                 (moving-average-price "TQQQ" {:window 20}))
                [(weight-equal
                  [(filter
                    (rsi {:window 10})
                    (select-top 1)
                    [(asset "SQQQ" "ProShares UltraPro Short QQQ")
                     (asset "BSV" "Vanguard Short-Term Bond ETF")])])]
                [(asset
                  "TQQQ" 
                  "ProShares UltraPro QQQ")])])])])])])])]))
