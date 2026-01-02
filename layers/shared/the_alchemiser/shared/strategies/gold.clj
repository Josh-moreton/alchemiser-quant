(defsymphony
 "Golden Rotation 2x"
 {:asset-class "EQUITIES", :rebalance-threshold 0.05}
 (weight-equal
  [(if
    (>
     (stdev-return "GLD" {:window 10})
     (stdev-return "GLD" {:window 100}))
    [(weight-equal
      [(asset
        "BIL"
        "SPDR Series Trust - State Street SPDR Bloomberg 1-3 Month T-Bill ETF")])]
    [(weight-equal
      [(if
        (>
         (moving-average-price "UGL" {:window 50})
         (moving-average-price "UGL" {:window 200}))
        [(weight-equal
          [(if
            (> (rsi "UGL" {:window 20}) 80)
            [(asset
              "GLL"
              "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
            [(weight-equal
              [(if
                (> (rsi "UGL" {:window 10}) 90)
                [(asset
                  "GLL"
                  "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                [(weight-equal
                  [(if
                    (> (rsi "UGL" {:window 2}) 99.9)
                    [(asset
                      "GLL"
                      "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                    [(asset
                      "UGL"
                      "ProShares Trust - ProShares Ultra Gold 2x Shares")])])])])])])]
        [(weight-equal
          [(if
            (>
             (moving-average-price "UGL" {:window 20})
             (moving-average-price "UGL" {:window 50}))
            [(weight-equal
              [(if
                (> (rsi "UGL" {:window 20}) 75)
                [(asset
                  "GLL"
                  "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                [(weight-equal
                  [(if
                    (> (rsi "UGL" {:window 2}) 99.9)
                    [(asset
                      "GLL"
                      "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                    [(asset
                      "UGL"
                      "ProShares Trust - ProShares Ultra Gold 2x Shares")])])])])]
            [(weight-equal
              [(if
                (>
                 (moving-average-price "UGL" {:window 5})
                 (moving-average-price "UGL" {:window 10}))
                [(weight-equal
                  [(if
                    (> (rsi "UGL" {:window 10}) 60)
                    [(asset
                      "GLL"
                      "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                    [(asset
                      "UGL"
                      "ProShares Trust - ProShares Ultra Gold 2x Shares")])])]
                [(weight-equal
                  [(if
                    (< (rsi "UGL" {:window 20}) 30)
                    [(asset
                      "UGL"
                      "ProShares Trust - ProShares Ultra Gold 2x Shares")]
                    [(asset
                      "GLL"
                      "ProShares Trust - ProShares UltraShort Gold -2x Shares")])])])])])])])])])]))
