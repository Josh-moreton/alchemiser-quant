(defsymphony
 "Simons KMLM switcher (single pops)| BT 4/13/22 = A.R. 466% / D.D. 22% V2"
 {:asset-class "EQUITIES", :rebalance-threshold 0.1}
 (weight-equal
  [(group
    "KMLM switcher (single pops)| BT 4/13/22 = A.R. 466% / D.D. 22%"
    [(weight-equal
      [(if
        (> (rsi "QQQE" {:window 10}) 79)
        [(asset "UVXY" "ProShares Ultra VIX Short-Term Futures ETF")]
        [(weight-equal
          [(if
            (> (rsi "VTV" {:window 10}) 79)
            [(asset
              "UVXY"
              "ProShares Ultra VIX Short-Term Futures ETF")]
            [(weight-equal
              [(if
                (> (rsi "VOX" {:window 10}) 79)
                [(asset
                  "UVXY"
                  "ProShares Ultra VIX Short-Term Futures ETF")]
                [(weight-equal
                  [(if
                    (> (rsi "TECL" {:window 10}) 79)
                    [(asset
                      "UVXY"
                      "ProShares Ultra VIX Short-Term Futures ETF")]
                    [(weight-equal
                      [(if
                        (> (rsi "VOOG" {:window 10}) 79)
                        [(asset
                          "UVXY"
                          "ProShares Ultra VIX Short-Term Futures ETF")]
                        [(weight-equal
                          [(if
                            (> (rsi "VOOV" {:window 10}) 79)
                            [(asset
                              "UVXY"
                              "ProShares Ultra VIX Short-Term Futures ETF")]
                            [(weight-equal
                              [(if
                                (> (rsi "XLP" {:window 10}) 75)
                                [(asset
                                  "UVXY"
                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                [(weight-equal
                                  [(if
                                    (> (rsi "TQQQ" {:window 10}) 79)
                                    [(weight-equal
                                      [(asset
                                        "UVXY"
                                        "ProShares Ultra VIX Short-Term Futures ETF")])]
                                    [(weight-equal
                                      [(if
                                        (> (rsi "XLY" {:window 10}) 80)
                                        [(asset
                                          "UVXY"
                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "FAS" {:window 10})
                                             80)
                                            [(asset
                                              "UVXY"
                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "SPY"
                                                  {:window 10})
                                                 80)
                                                [(asset
                                                  "UVXY"
                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                [(group
                                                  "Combined Pop Bot"
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (rsi
                                                        "TQQQ"
                                                        {:window 10})
                                                       30)
                                                      [(asset
                                                        "TECL"
                                                        "Direxion Daily Technology Bull 3x Shares")]
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (rsi
                                                            "SOXL"
                                                            {:window
                                                             10})
                                                           30)
                                                          [(asset
                                                            "SOXL"
                                                            "Direxion Daily Semiconductor Bull 3x Shares")]
                                                          [(weight-equal
                                                            [(if
                                                              (<
                                                               (rsi
                                                                "SPXL"
                                                                {:window
                                                                 10})
                                                               30)
                                                              [(asset
                                                                "SPXL"
                                                                "Direxion Daily S&P 500 Bull 3x Shares")]
                                                              [(weight-equal
                                                                [(if
                                                                  (<
                                                                   (rsi
                                                                    "LABU"
                                                                    {:window
                                                                     10})
                                                                   25)
                                                                  [(asset
                                                                    "LABU"
                                                                    "Direxion Daily S&P Biotech Bull 3X Shares")]
                                                                  [(group
                                                                    "KMLM switcher: TECL, SVIX, or L/S Rotator | BT 4/13/22 = AR 164% / DD 22.2%"
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLK"
                                                                          {:window
                                                                           10})
                                                                         (rsi
                                                                          "KMLM"
                                                                          {:window
                                                                           10}))
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (rsi
                                                                             {:window
                                                                              10})
                                                                            (select-bottom
                                                                             2)
                                                                            [(asset
                                                                              "TECL"
                                                                              "Direxion Daily Technology Bull 3x Shares")
                                                                             (asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "SVIX"
                                                                              "-1x Short VIX Futures ETF")])])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (rsi
                                                                             {:window
                                                                              10})
                                                                            (select-top
                                                                             1)
                                                                            [(asset
                                                                              "SQQQ"
                                                                              "ProShares UltraPro Short QQQ")
                                                                             (asset
                                                                              "TLT"
                                                                              "iShares 20+ Year Treasury Bond ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]))
