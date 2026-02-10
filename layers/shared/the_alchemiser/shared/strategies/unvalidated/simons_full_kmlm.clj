(defsymphony
 "Simons KMLM FULL BUILD"
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
                                                [(weight-equal
                                                  [(group
                                                    "Single Popped KMLM"
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "UVXY"
                                                          {:window 21})
                                                         65)
                                                        [(weight-equal
                                                          [(group
                                                            "BSC"
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   21})
                                                                 30)
                                                                [(asset
                                                                  "VIXM"
                                                                  "ProShares VIX Mid-Term Futures ETF")]
                                                                [(asset
                                                                  "SPXL"
                                                                  "Direxion Daily S&P 500 Bull 3x Shares")])])])])]
                                                        [(weight-equal
                                                          [(group
                                                            "Combined Pop Bot"
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (rsi
                                                                  "TQQQ"
                                                                  {:window
                                                                   10})
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
                                                                     31)
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
                                                                         28)
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
                                                                            [(weight-equal
                                                                              [(if
                                                                                (>
                                                                                 (rsi
                                                                                  "SOXL"
                                                                                  {:window
                                                                                   10})
                                                                                 (rsi
                                                                                  "KMLM"
                                                                                  {:window
                                                                                   10}))
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (<
                                                                                     (rsi
                                                                                      "SMH"
                                                                                      {:window
                                                                                       10})
                                                                                     75)
                                                                                    [(weight-equal
                                                                                      [(filter
                                                                                        (rsi
                                                                                         {:window
                                                                                          10})
                                                                                        (select-bottom
                                                                                         1)
                                                                                        [(asset
                                                                                          "SOXL"
                                                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                         (asset
                                                                                          "SVIX"
                                                                                          "-1x Short VIX Futures ETF")])])]
                                                                                    [(asset
                                                                                      "KMLM"
                                                                                      "KraneShares Mount Lucas Managed Futures Index Strategy ETF")])])]
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (>
                                                                                     (rsi
                                                                                      "TECL"
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
                                                                                         1)
                                                                                        [(asset
                                                                                          "TECL"
                                                                                          "Direxion Daily Technology Bull 3x Shares")
                                                                                         (asset
                                                                                          "SVIX"
                                                                                          "-1x Short VIX Futures ETF")])])]
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (rsi
                                                                                          "USD"
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
                                                                                             1)
                                                                                            [(asset
                                                                                              "TECL"
                                                                                              "Direxion Daily Technology Bull 3x Shares")
                                                                                             (asset
                                                                                              "SVIX"
                                                                                              "-1x Short VIX Futures ETF")])])]
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (>
                                                                                             (rsi
                                                                                              "SMH"
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
                                                                                                 1)
                                                                                                [(asset
                                                                                                  "TECL"
                                                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                                                 (asset
                                                                                                  "SVIX"
                                                                                                  "-1x Short VIX Futures ETF")])])]
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (>
                                                                                                 (current-price
                                                                                                  "KMLM")
                                                                                                 (moving-average-price
                                                                                                  "KMLM"
                                                                                                  {:window
                                                                                                   20}))
                                                                                                [(asset
                                                                                                  "TECS"
                                                                                                  "Direxion Daily Technology Bear 3X Shares")]
                                                                                                [(asset
                                                                                                  "KMLM"
                                                                                                  "KFA Mount Lucas Managed Futures Index Strategy ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]))
