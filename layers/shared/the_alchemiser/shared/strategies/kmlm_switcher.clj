(defsymphony
 "KMLM switcher (single pops)| BT 4/13/22  (Invest Copy)"
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
                                                                          [(group
                                                                            "Copypasta YOLO GainZs Here"
                                                                            [(weight-equal
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
                                                                                         1)
                                                                                        [(asset
                                                                                          "TECL"
                                                                                          "Direxion Daily Technology Bull 3x Shares")
                                                                                         (asset
                                                                                          "SVIX"
                                                                                          "-1x Short VIX Futures ETF")])])]
                                                                                    [(group
                                                                                      "Long/Short Rotator with FTLS KMLM SSO UUP | BT 12/10/20 | 15.1/3.5  "
                                                                                      [(weight-equal
                                                                                        [(filter
                                                                                          (stdev-return
                                                                                           {:window
                                                                                            6})
                                                                                          (select-bottom
                                                                                           3)
                                                                                          [(asset
                                                                                            "TMV"
                                                                                            nil)
                                                                                           (asset
                                                                                            "TMF"
                                                                                            nil)
                                                                                           (asset
                                                                                            "SVXY"
                                                                                            nil)
                                                                                           (asset
                                                                                            "VIXM"
                                                                                            nil)
                                                                                           (asset
                                                                                            "FTLS"
                                                                                            "First Trust Long/Short Equity ETF")
                                                                                           (asset
                                                                                            "KMLM"
                                                                                            "KFA Mount Lucas Managed Futures Index Strategy ETF")
                                                                                           (asset
                                                                                            "UUP"
                                                                                            "Invesco DB US Dollar Index Bullish Fund")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]))
