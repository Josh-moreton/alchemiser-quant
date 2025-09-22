(defsymphony
 "TQQQ FTLT using KMLM before going full leverage V2"
 {:asset-class "EQUITIES", :rebalance-threshold 0.1}
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
            [(weight-equal
              [(if
                (> (rsi "XLK" {:window 10}) (rsi "KMLM" {:window 10}))
                [(asset "TQQQ" "ProShares UltraPro QQQ")]
                [(asset
                  "SQQQ"
                  "ProShares UltraPro Short QQQ")])])])])])])]
    [(weight-equal
      [(if
        (< (rsi "TQQQ" {:window 10}) 31)
        [(asset "TECL" "Direxion Daily Technology Bull 3x Shares")]
        [(weight-equal
          [(if
            (< (rsi "SPY" {:window 10}) 30)
            [(asset "UPRO" "ProShares UltraPro S&P500")]
            [(weight-equal
              [(if
                (<
                 (current-price "TQQQ")
                 (moving-average-price "TQQQ" {:window 20}))
                [(weight-equal
                  [(filter
                    (rsi {:window 10})
                    (select-top 1)
                    [(asset "TLT" "iShares 20+ Year Treasury Bond ETF")
                     (group
                      "Shorting Group"
                      [(weight-equal
                        [(if
                          (<
                           (rsi "XLK" {:window 10})
                           (rsi "KMLM" {:window 10}))
                          [(asset
                            "SQQQ"
                            "ProShares UltraPro Short QQQ")]
                          [(asset
                            "TLT"
                            "iShares 20+ Year Treasury Bond ETF")])])])])])]
                [(weight-equal
                  [(if
                    (< (rsi "SQQQ" {:window 10}) 31)
                    [(asset "SQQQ" "ProShares UltraPro Short QQQ")]
                    [(asset
                      "TQQQ"
                      "ProShares UltraPro QQQ")])])])])])])])])])]))
