(defsymphony
 "Holy Grail Revamped | Anansi | Safe Sectors"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "Aggressive VIX Frontrunner (43,17,2011)"
    [(weight-equal
      [(if
        (> (rsi "SPY" {:window 10}) 80)
        [(asset
          "UVXY"
          "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
        [(weight-equal
          [(if
            (> (rsi "QQQ" {:window 10}) 79)
            [(weight-equal
              [(if
                (> (rsi "XLP" {:window 10}) 75)
                [(asset
                  "UVXY"
                  "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
                [(asset
                  "VIXY"
                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")])])]
            [(weight-equal
              [(if
                (> (rsi "VTV" {:window 10}) 79)
                [(asset
                  "VIXY"
                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
                [(weight-equal
                  [(if
                    (> (rsi "XLK" {:window 10}) 79)
                    [(weight-equal
                      [(if
                        (> (rsi "UVXY" {:window 60}) 39.5)
                        [(asset
                          "VIXY"
                          "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(weight-equal
                      [(if
                        (> (rsi "VOX" {:window 10}) 79)
                        [(weight-equal
                          [(if
                            (> (rsi "XLP" {:window 10}) 75)
                            [(asset
                              "UVXY"
                              "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
                            [(asset
                              "VIXY"
                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")])])]
                        [(weight-equal
                          [(if
                            (> (rsi "XLF" {:window 10}) 80)
                            [(asset
                              "VIXY"
                              "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
                            [(weight-equal
                              [(if
                                (> (rsi "XLY" {:window 10}) 80)
                                [(asset
                                  "VIXY"
                                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
                                [(weight-equal
                                  [(if
                                    (> (rsi "XLP" {:window 10}) 75)
                                    [(asset
                                      "VIXY"
                                      "ProShares Trust - ProShares VIX Short-Term Futures ETF")]
                                    [(group
                                      "Holy Grail Revamped | Anansi | Safe Sectors Mod (88,40,2011)"
                                      [(weight-equal
                                        [(if
                                          (<
                                           (rsi "QQQ" {:window 10})
                                           30)
                                          [(asset
                                            "TECL"
                                            "Direxion Shares ETF Trust - Direxion Daily Technology Bull 3X Shares")]
                                          [(weight-equal
                                            [(if
                                              (<
                                               (rsi "SPY" {:window 10})
                                               30)
                                              [(asset
                                                "UPRO"
                                                "ProShares Trust - ProShares UltraPro S&P 500 ETF 3x Shares")]
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (current-price
                                                    "SPY")
                                                   (moving-average-price
                                                    "SPY"
                                                    {:window 200}))
                                                  [(group
                                                    "20d AGG vs 60d SH"
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "AGG"
                                                          {:window 20})
                                                         (rsi
                                                          "SH"
                                                          {:window
                                                           60}))
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (current-price
                                                              "SPY")
                                                             (moving-average-price
                                                              "SPY"
                                                              {:window
                                                               30}))
                                                            [(asset
                                                              "TQQQ"
                                                              "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                            [(group
                                                              "Safe Sectors or Bonds (61,29,2007)"
                                                              [(weight-equal
                                                                [(filter
                                                                  (rsi
                                                                   {:window
                                                                    10})
                                                                  (select-bottom
                                                                   1)
                                                                  [(asset
                                                                    "BSV"
                                                                    "Vanguard Group, Inc. - Vanguard Short-Term Bond ETF")
                                                                   (asset
                                                                    "TLT"
                                                                    "BlackRock Institutional Trust Company N.A. - iShares 20+ Year Treasury Bond ETF")
                                                                   (asset
                                                                    "LQD"
                                                                    "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD Investment Grade Corporate Bond ETF")
                                                                   (asset
                                                                    "VBF"
                                                                    "Invesco Bond Fund")
                                                                   (asset
                                                                    "XLP"
                                                                    "SSgA Active Trust - Consumer Staples Select Sector SPDR")
                                                                   (asset
                                                                    "UGE"
                                                                    "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                   (asset
                                                                    "XLV"
                                                                    "SSgA Active Trust - Health Care Select Sector SPDR")
                                                                   (asset
                                                                    "XLU"
                                                                    "SSgA Active Trust - Utilities Select Sector SPDR ETF")])])])])])]
                                                        [(asset
                                                          "PSQ"
                                                          nil)])])])]
                                                  [(weight-equal
                                                    [(if
                                                      (>
                                                       (cumulative-return
                                                        "QQQ"
                                                        {:window 60})
                                                       -12)
                                                      [(asset
                                                        "BIL"
                                                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")]
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (current-price
                                                            "TQQQ")
                                                           (moving-average-price
                                                            "TQQQ"
                                                            {:window
                                                             20}))
                                                          [(weight-equal
                                                            [(if
                                                              (<
                                                               (rsi
                                                                "PSQ"
                                                                {:window
                                                                 10})
                                                               35)
                                                              [(asset
                                                                "PSQ"
                                                                nil)]
                                                              [(group
                                                                "20d AGG vs 60d SH"
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "AGG"
                                                                      {:window
                                                                       20})
                                                                     (rsi
                                                                      "SH"
                                                                      {:window
                                                                       60}))
                                                                    [(asset
                                                                      "TQQQ"
                                                                      "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                                    [(asset
                                                                      "PSQ"
                                                                      "ProShares Short QQQ")])])])])])]
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (rsi
                                                                "IEF"
                                                                {:window
                                                                 10})
                                                               (rsi
                                                                "PSQ"
                                                                {:window
                                                                 20}))
                                                              [(asset
                                                                "PSQ"
                                                                nil)]
                                                              [(asset
                                                                "SQQQ"
                                                                nil)])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]))
