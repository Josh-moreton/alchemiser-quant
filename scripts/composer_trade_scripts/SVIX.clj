(defsymphony
 "SVIX/XXXX KMLM switcher (single pops)| BT 12/19/23 = 786/10.5"
 {:asset-class "EQUITIES", :rebalance-threshold 0.1}
 (weight-equal
  [(group
    "SVIX/XXXX/KMLM switcher | BT 12/19/23 = 786/10.5"
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
                                                    "Vol Check"
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
                                                                  "SPYU"
                                                                  nil)])])])])]
                                                        [(weight-equal
                                                          [(group
                                                            "Pop Bots"
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
                                                                          "SPYU"
                                                                          nil)]
                                                                        [(weight-equal
                                                                          [(group
                                                                            "YOLO GainZs"
                                                                            [(weight-equal
                                                                              [(group
                                                                                "KMLM switcher XXXX-SVIX-L/S Rotator"
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (>
                                                                                     (rsi
                                                                                      "SPY"
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
                                                                                          "SPYU"
                                                                                          nil)
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
