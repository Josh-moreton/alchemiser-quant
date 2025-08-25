(defsymphony
 "(see bottom block) TECL For The Long Term (v7) | Less VIX | KMLM signal boost"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
    (>
     (current-price "SPY")
     (moving-average-price "SPY" {:window 200}))
    [(weight-equal
      [(if
        (> (rsi "TQQQ" {:window 10}) 79)
        [(group
          "UVXY+75%BIL"
          [(weight-specified
            0.25
            (asset "UVXY" "ProShares Ultra VIX Short-Term Futures ETF")
            0.75
            (asset "BIL" "SPDR Bloomberg 1-3 Month T-Bill ETF"))])]
        [(weight-equal
          [(if
            (> (rsi "SPY" {:window 10}) 80)
            [(group
              "UVXY+75%BIL"
              [(weight-specified
                0.25
                (asset
                 "UVXY"
                 "ProShares Ultra VIX Short-Term Futures ETF")
                0.75
                (asset "BIL" "SPDR Bloomberg 1-3 Month T-Bill ETF"))])]
            [(group
              "KMLM Switcher | SimplyGreen | No short"
              [(weight-equal
                [(if
                  (>
                   (rsi "XLK" {:window 10})
                   (rsi "KMLM" {:window 10}))
                  [(weight-equal
                    [(if
                      (> (rsi "XLK" {:window 10}) 81)
                      [(asset
                        "BIL"
                        "SPDR Bloomberg 1-3 Month T-Bill ETF")]
                      [(asset
                        "TECL"
                        "Direxion Daily Technology Bull 3x Shares")])])]
                  [(weight-equal
                    [(if
                      (< (rsi "XLK" {:window 10}) 29)
                      [(asset
                        "TECL"
                        "Direxion Daily Technology Bull 3x Shares")]
                      [(asset
                        "BIL"
                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
    [(weight-equal
      [(if
        (< (rsi "TQQQ" {:window 10}) 31)
        [(weight-equal
          [(asset "TECL" "Direxion Daily Technology Bull 3x Shares")])]
        [(weight-equal
          [(if
            (< (rsi "SPXL" {:window 10}) 29)
            [(weight-equal [(asset "SPXL" nil)])]
            [(weight-equal
              [(if
                (> (rsi "UVXY" {:window 10}) 74)
                [(weight-equal
                  [(if
                    (> (rsi "UVXY" {:window 10}) 84)
                    [(weight-equal
                      [(group
                        "UVXY+85%BIL"
                        [(weight-specified
                          0.15
                          (asset
                           "UVXY"
                           "ProShares Ultra VIX Short-Term Futures ETF")
                          0.85
                          (asset
                           "BIL"
                           "SPDR Bloomberg 1-3 Month T-Bill ETF"))])])]
                    [(asset
                      "BIL"
                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                [(weight-equal
                  [(if
                    (>
                     (rsi "XLK" {:window 10})
                     (rsi "KMLM" {:window 10}))
                    [(weight-equal
                      [(if
                        (> (rsi "XLK" {:window 10}) 81)
                        [(asset
                          "BIL"
                          "SPDR Bloomberg 1-3 Month T-Bill ETF")]
                        [(asset
                          "TECL"
                          "Direxion Daily Technology Bull 3x Shares")])])]
                    [(weight-equal
                      [(if
                        (< (rsi "XLK" {:window 10}) 29)
                        [(asset
                          "TECL"
                          "Direxion Daily Technology Bull 3x Shares")]
                        [(weight-equal
                          [(filter
                            (rsi {:window 9})
                            (select-top 1)
                            [(asset
                              "SQQQ"
                              "ProShares UltraPro Short QQQ")
                             (asset
                              "BSV"
                              "Vanguard Short-Term Bond ETF")])])])])])])])])])])])])])]))
