(defsymphony
 "TQQQ For The Long Term V2 (242% RR/46.1% Max DD)"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
    (>
     (current-price "SPY")
     (moving-average-price "SPY" {:window 200}))
    [(weight-equal
      [(if
        (> (rsi "TQQQ" {:window 10}) 79)
        [(asset "UVXY" "ProShares Ultra VIX Short-Term Futures ETF")]
        [(weight-equal
          [(if
            (> (rsi "SPXL" {:window 10}) 80)
            [(asset
              "UVXY"
              "ProShares Ultra VIX Short-Term Futures ETF")]
            [(asset "TQQQ" "ProShares UltraPro QQQ")])])])])]
    [(weight-equal
      [(if
        (< (rsi "TQQQ" {:window 10}) 31)
        [(asset "TECL" "Direxion Daily Technology Bull 3x Shares")]
        [(weight-equal
          [(if
            (< (rsi "SPY" {:window 10}) 30)
            [(asset "SPXL" "Direxion Daily S&P 500 Bull 3x Shares")]
            [(weight-equal
              [(if
                (> (rsi "UVXY" {:window 10}) 74)
                [(weight-equal
                  [(if
                    (> (rsi "UVXY" {:window 10}) 84)
                    [(weight-equal
                      [(if
                        (>
                         (current-price "TQQQ")
                         (moving-average-price "TQQQ" {:window 20}))
                        [(weight-equal
                          [(if
                            (< (rsi "SQQQ" {:window 10}) 31)
                            [(asset
                              "SQQQ"
                              "ProShares UltraPro Short QQQ")]
                            [(asset
                              "TQQQ"
                              "ProShares UltraPro QQQ")])])]
                        [(weight-equal
                          [(filter
                            (rsi {:window 10})
                            (select-top 1)
                            [(asset
                              "SQQQ"
                              "ProShares UltraPro Short QQQ")
                             (asset
                              "BSV"
                              "Vanguard Short-Term Bond ETF")])])])])]
                    [(asset
                      "UVXY"
                      "ProShares Ultra VIX Short-Term Futures ETF")])])]
                [(weight-equal
                  [(if
                    (>
                     (current-price "TQQQ")
                     (moving-average-price "TQQQ" {:window 20}))
                    [(weight-equal
                      [(if
                        (< (rsi "SQQQ" {:window 10}) 31)
                        [(asset "SQQQ" "ProShares UltraPro Short QQQ")]
                        [(asset "TQQQ" "ProShares UltraPro QQQ")])])]
                    [(weight-equal
                      [(filter
                        (rsi {:window 10})
                        (select-top 1)
                        [(asset "SQQQ" "ProShares UltraPro Short QQQ")
                         (asset
                          "BSV"
                          "Vanguard Short-Term Bond ETF")])])])])])])])])])])])]))
