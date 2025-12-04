(defsymphony
 "FTLT w/2x|120,21,2007 (Public)"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
    (> (rsi "SPY" {:window 10}) 80)
    [(asset
      "QID"
      "ProShares Trust - ProShares UltraShort QQQ -2x Shares")]
    [(weight-equal
      [(if
        (> (rsi "QQQ" {:window 10}) 79)
        [(asset
          "QID"
          "ProShares Trust - ProShares UltraShort QQQ -2x Shares")]
        [(weight-equal
          [(if
            (> (rsi "XLP" {:window 10}) 77)
            [(weight-equal [(asset "QID" nil)])]
            [(weight-equal
              [(if
                (> (rsi "XLF" {:window 10}) 81)
                [(weight-equal [(asset "QID" nil)])]
                [(weight-equal
                  [(if
                    (> (rsi "XLK" {:window 10}) 79)
                    [(asset
                      "QID"
                      "ProShares Trust - ProShares UltraShort QQQ -2x Shares")]
                    [(weight-equal
                      [(if
                        (> (rsi "QQQ" {:window 3}) 98)
                        [(asset
                          "QID"
                          "ProShares Trust - ProShares UltraShort QQQ -2x Shares")]
                        [(weight-equal
                          [(if
                            (> (rsi "QQQ" {:window 6}) 88)
                            [(weight-equal
                              [(asset
                                "QID"
                                "ProShares Trust - ProShares UltraShort QQQ -2x Shares")])]
                            [(weight-equal
                              [(if
                                (> (rsi "FDL" {:window 10}) 80)
                                [(asset "QID" nil)]
                                [(weight-equal
                                  [(if
                                    (> (rsi "SPY" {:window 60}) 73)
                                    [(asset "QID" nil)]
                                    [(weight-equal
                                      [(if
                                        (>
                                         (rsi "SPY" {:window 200})
                                         61.5)
                                        [(asset
                                          "QID"
                                          "ProShares Trust - ProShares UltraShort QQQ -2x Shares")]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "SPY" {:window 25})
                                             71.5)
                                            [(asset "QID" nil)]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "QQQ"
                                                  {:window 60})
                                                 68)
                                                [(asset "QID" nil)]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "QQQ"
                                                      {:window 252})
                                                     58.5)
                                                    [(asset "QID" nil)]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "QQQ"
                                                          {:window 25})
                                                         72.5)
                                                        [(asset
                                                          "QID"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "SPY"
                                                              {:window
                                                               70})
                                                             60)
                                                            [(asset
                                                              "IAU"
                                                              "BlackRock Institutional Trust Company N.A. - iShares Gold Trust")]
                                                            [(weight-equal
                                                              [(group
                                                                "FTLT"
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (cumulative-return
                                                                      "QQQ"
                                                                      {:window
                                                                       5})
                                                                     -5)
                                                                    [(group
                                                                      "Mean Reversion"
                                                                      [(weight-equal
                                                                        [(if
                                                                          (<
                                                                           (rsi
                                                                            "SPY"
                                                                            {:window
                                                                             10})
                                                                           32.5)
                                                                          [(asset
                                                                            "ROM"
                                                                            "ProShares Trust - ProShares Ultra Technology 2x Shares")
                                                                           (asset
                                                                            "XLK"
                                                                            "SSgA Active Trust - Technology Select Sector SPDR ETF")]
                                                                          [(asset
                                                                            "TLT"
                                                                            "BlackRock Institutional Trust Company N.A. - iShares 20+ Year Treasury Bond ETF")])])])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "QQQ"
                                                                          {:window
                                                                           10})
                                                                         31)
                                                                        [(asset
                                                                          "QLD"
                                                                          "ProShares Trust - ProShares Ultra QQQ 2x Shares")
                                                                         (asset
                                                                          "USD"
                                                                          "ProShares Trust - ProShares Ultra Semiconductors 2X Shares")]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (current-price
                                                                              "SPY")
                                                                             (moving-average-price
                                                                              "SPY"
                                                                              {:window
                                                                               200}))
                                                                            [(group
                                                                              "Bull"
                                                                              [(weight-equal
                                                                                [(if
                                                                                  (>
                                                                                   (current-price
                                                                                    "QQQ")
                                                                                   (moving-average-price
                                                                                    "QQQ"
                                                                                    {:window
                                                                                     25}))
                                                                                  [(group
                                                                                    "Block from 4C"
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (rsi
                                                                                          "LQD"
                                                                                          {:window
                                                                                           15})
                                                                                         (rsi
                                                                                          "XLK"
                                                                                          {:window
                                                                                           10}))
                                                                                        [(weight-equal
                                                                                          [(asset
                                                                                            "QLD"
                                                                                            "ProShares Trust - ProShares Ultra QQQ 2x Shares")
                                                                                           (asset
                                                                                            "USD"
                                                                                            "ProShares Trust - ProShares Ultra Semiconductors 2X Shares")
                                                                                           (asset
                                                                                            "ROM"
                                                                                            "ProShares Trust - ProShares Ultra Technology 2x Shares")])]
                                                                                        [(asset
                                                                                          "QLD"
                                                                                          "ProShares Trust - ProShares Ultra QQQ 2x Shares")])])])]
                                                                                  [(weight-equal
                                                                                    [(if
                                                                                      (>
                                                                                       (cumulative-return
                                                                                        "QQQ"
                                                                                        {:window
                                                                                         20})
                                                                                       (moving-average-return
                                                                                        "QQQ"
                                                                                        {:window
                                                                                         10}))
                                                                                      [(asset
                                                                                        "QLD"
                                                                                        "ProShares Trust - ProShares Ultra QQQ 2x Shares")
                                                                                       (asset
                                                                                        "USD"
                                                                                        "ProShares Trust - ProShares Ultra Semiconductors 2X Shares")
                                                                                       (asset
                                                                                        "ROM"
                                                                                        "ProShares Trust - ProShares Ultra Technology 2x Shares")]
                                                                                      [(weight-equal
                                                                                        [(filter
                                                                                          (rsi
                                                                                           {:window
                                                                                            10})
                                                                                          (select-bottom
                                                                                           1)
                                                                                          [(asset
                                                                                            "VBF"
                                                                                            "Invesco Bond Fund")
                                                                                           (asset
                                                                                            "XLU"
                                                                                            "SSgA Active Trust - Utilities Select Sector SPDR ETF")
                                                                                           (asset
                                                                                            "TLT"
                                                                                            "BlackRock Institutional Trust Company N.A. - iShares 20+ Year Treasury Bond ETF")])
                                                                                         (asset
                                                                                          "QLD"
                                                                                          "ProShares Trust - ProShares Ultra QQQ 2x Shares")])])])])])])]
                                                                            [(weight-equal
                                                                              [(group
                                                                                "Bear"
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (<
                                                                                     (cumulative-return
                                                                                      "QQQ"
                                                                                      {:window
                                                                                       60})
                                                                                     -11)
                                                                                    [(group
                                                                                      "Bonds v0.2"
                                                                                      [(weight-equal
                                                                                        [(filter
                                                                                          (rsi
                                                                                           {:window
                                                                                            10})
                                                                                          (select-bottom
                                                                                           2)
                                                                                          [(asset
                                                                                            "BKT"
                                                                                            "BlackRock Income Trust Inc")
                                                                                           (asset
                                                                                            "NAN"
                                                                                            "Nuveen New York Quality Municipal Income Fund")
                                                                                           (asset
                                                                                            "MMU"
                                                                                            "Western Asset Managed Municipals Fund Inc")
                                                                                           (asset
                                                                                            "PMM"
                                                                                            "Putnam Managed Municipal Income Trust.")
                                                                                           (asset
                                                                                            "EVN"
                                                                                            "Eaton Vance Municipal Income Trust")
                                                                                           (asset
                                                                                            "VBF"
                                                                                            "Invesco Bond Fund")])])])]
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (current-price
                                                                                          "QQQ")
                                                                                         (moving-average-price
                                                                                          "QQQ"
                                                                                          {:window
                                                                                           25}))
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (<
                                                                                             (rsi
                                                                                              "PSQ"
                                                                                              {:window
                                                                                               10})
                                                                                             35)
                                                                                            [(weight-equal
                                                                                              [(asset
                                                                                                "QID"
                                                                                                "ProShares Trust - ProShares UltraShort QQQ -2x Shares")])]
                                                                                            [(group
                                                                                              "TLT vs PSQ"
                                                                                              [(weight-equal
                                                                                                [(if
                                                                                                  (>
                                                                                                   (rsi
                                                                                                    "TLT"
                                                                                                    {:window
                                                                                                     21})
                                                                                                   (rsi
                                                                                                    "PSQ"
                                                                                                    {:window
                                                                                                     21}))
                                                                                                  [(asset
                                                                                                    "QLD"
                                                                                                    "ProShares Trust - ProShares Ultra QQQ 2x Shares")
                                                                                                   (asset
                                                                                                    "ROM"
                                                                                                    "ProShares Trust - ProShares Ultra Technology 2x Shares")
                                                                                                   (asset
                                                                                                    "USD"
                                                                                                    "ProShares Trust - ProShares Ultra Semiconductors 2X Shares")
                                                                                                   (weight-equal
                                                                                                    [(if
                                                                                                      (>
                                                                                                       (current-price
                                                                                                        "SPY")
                                                                                                       (moving-average-price
                                                                                                        "SPY"
                                                                                                        {:window
                                                                                                         30}))
                                                                                                      [(weight-equal
                                                                                                        [(asset
                                                                                                          "QLD"
                                                                                                          "ProShares Trust - ProShares Ultra QQQ 2x Shares")
                                                                                                         (asset
                                                                                                          "ROM"
                                                                                                          "ProShares Trust - ProShares Ultra Technology 2x Shares")
                                                                                                         (asset
                                                                                                          "USD"
                                                                                                          "ProShares Trust - ProShares Ultra Semiconductors 2X Shares")])]
                                                                                                      [(group
                                                                                                        "Bonds v0.2"
                                                                                                        [(weight-equal
                                                                                                          [(filter
                                                                                                            (rsi
                                                                                                             {:window
                                                                                                              10})
                                                                                                            (select-bottom
                                                                                                             2)
                                                                                                            [(asset
                                                                                                              "BKT"
                                                                                                              "BlackRock Income Trust Inc")
                                                                                                             (asset
                                                                                                              "NAN"
                                                                                                              "Nuveen New York Quality Municipal Income Fund")
                                                                                                             (asset
                                                                                                              "MMU"
                                                                                                              "Western Asset Managed Municipals Fund Inc")
                                                                                                             (asset
                                                                                                              "PMM"
                                                                                                              "Putnam Managed Municipal Income Trust.")
                                                                                                             (asset
                                                                                                              "EVN"
                                                                                                              "Eaton Vance Municipal Income Trust")
                                                                                                             (asset
                                                                                                              "VBF"
                                                                                                              "Invesco Bond Fund")])])])])])]
                                                                                                  [(asset
                                                                                                    "QID"
                                                                                                    nil)
                                                                                                   (asset
                                                                                                    "IAU"
                                                                                                    "BlackRock Institutional Trust Company N.A. - iShares Gold Trust")])])])])])]
                                                                                        [(weight-equal
                                                                                          [(group
                                                                                            "AGG vs QQQ"
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (>
                                                                                                 (rsi
                                                                                                  "AGG"
                                                                                                  {:window
                                                                                                   21})
                                                                                                 (rsi
                                                                                                  "QQQ"
                                                                                                  {:window
                                                                                                   21}))
                                                                                                [(asset
                                                                                                  "QID"
                                                                                                  "ProShares Trust - ProShares UltraShort QQQ -2x Shares")
                                                                                                 (group
                                                                                                  "Bonds v0.2"
                                                                                                  [(weight-equal
                                                                                                    [(filter
                                                                                                      (rsi
                                                                                                       {:window
                                                                                                        10})
                                                                                                      (select-bottom
                                                                                                       2)
                                                                                                      [(asset
                                                                                                        "BKT"
                                                                                                        "BlackRock Income Trust Inc")
                                                                                                       (asset
                                                                                                        "NAN"
                                                                                                        "Nuveen New York Quality Municipal Income Fund")
                                                                                                       (asset
                                                                                                        "MMU"
                                                                                                        "Western Asset Managed Municipals Fund Inc")
                                                                                                       (asset
                                                                                                        "PMM"
                                                                                                        "Putnam Managed Municipal Income Trust.")
                                                                                                       (asset
                                                                                                        "EVN"
                                                                                                        "Eaton Vance Municipal Income Trust")
                                                                                                       (asset
                                                                                                        "VBF"
                                                                                                        "Invesco Bond Fund")])
                                                                                                     (asset
                                                                                                      "IAU"
                                                                                                      "BlackRock Institutional Trust Company N.A. - iShares Gold Trust")])])]
                                                                                                [(asset
                                                                                                  "QID"
                                                                                                  "ProShares Trust - ProShares UltraShort QQQ -2x Shares")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]))
