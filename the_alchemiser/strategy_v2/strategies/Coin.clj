(defsymphony
 "Papertesting //  𝓩𝓪𝓶-I-am | eQWrFo9iUgOYTkFHTtbt ( Dancing between Coin and Nvda)"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "V1b 15/15 BB + v4 Pops - K-1 Free"
    [(weight-equal
      [(if
        (< (rsi "BIL" {:window 15}) (rsi "IEF" {:window 15}))
        [(weight-equal
          [(if
            (> (rsi "SPY" {:window 6}) 75)
            [(asset
              "SOXS"
              "Direxion Daily Semiconductor Bear 3x Shares")]
            [(weight-equal
              [(if
                (<= (rsi "SOXL" {:window 5}) 75)
                [(asset "NVDL" "GraniteShares 2x Long NVDA Daily ETF")]
                [(asset
                  "SOXS"
                  "Direxion Daily Semiconductor Bear 3x Shares")])])])])]
        [(weight-equal
          [(group
            "INTERSTELLAR x FRONT RUNNER LOGIC x Zoopy"
            [(weight-equal
              [(if
                (< (rsi "CONL" {:window 10}) 30)
                [(weight-equal
                  [(filter
                    (cumulative-return {:window 2})
                    (select-top 1)
                    [(asset
                      "CONL"
                      "GraniteShares 2x Long COIN Daily ETF")
                     (asset "BITX" "2x Bitcoin Strategy ETF")])])]
                [(weight-equal
                  [(if
                    (> (rsi "QQQ" {:window 10}) 79)
                    [(asset
                      "UVXY"
                      "ProShares Ultra VIX Short-Term Futures ETF")]
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
                                    (> (rsi "TQQQ" {:window 10}) 79)
                                    [(asset
                                      "UVXY"
                                      "ProShares Ultra VIX Short-Term Futures ETF")]
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
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "XLP"
                                                      {:window 10})
                                                     75)
                                                    [(asset
                                                      "UVXY"
                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (max-drawdown
                                                          "SPY"
                                                          {:window 9})
                                                         0.1)
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               10})
                                                             31)
                                                            [(asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (exponential-moving-average-price
                                                                  "SPY"
                                                                  {:window
                                                                   210})
                                                                 (moving-average-price
                                                                  "SPY"
                                                                  {:window
                                                                   360}))
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (moving-average-return
                                                                      "SPY"
                                                                      {:window
                                                                       210})
                                                                     (moving-average-return
                                                                      "DBC"
                                                                      {:window
                                                                       360}))
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (cumulative-return
                                                                          "TQQQ"
                                                                          {:window
                                                                           6})
                                                                         -12)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (cumulative-return
                                                                              "TQQQ"
                                                                              {:window
                                                                               1})
                                                                             5.5)
                                                                            [(asset
                                                                              "SQQQ"
                                                                              "ProShares UltraPro Short QQQ")]
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (cumulative-return
                                                                                 {:window
                                                                                  2})
                                                                                (select-top
                                                                                 1)
                                                                                [(asset
                                                                                  "CONL"
                                                                                  "GraniteShares 2x Long COIN Daily ETF")
                                                                                 (asset
                                                                                  "BITX"
                                                                                  "2x Bitcoin Strategy ETF")])])])])]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (moving-average-price
                                                                              "COIN"
                                                                              {:window
                                                                               9})
                                                                             (moving-average-price
                                                                              "COIN"
                                                                              {:window
                                                                               14}))
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (cumulative-return
                                                                                 {:window
                                                                                  2})
                                                                                (select-top
                                                                                 1)
                                                                                [(asset
                                                                                  "CONL"
                                                                                  "GraniteShares 2x Long COIN Daily ETF")
                                                                                 (asset
                                                                                  "BITX"
                                                                                  "2x Bitcoin Strategy ETF")])])]
                                                                            [(weight-equal
                                                                              [(group
                                                                                "Zoopy"
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (>
                                                                                     (rsi
                                                                                      "SPY"
                                                                                      {:window
                                                                                       10})
                                                                                     79)
                                                                                    [(asset
                                                                                      "UVXY"
                                                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (rsi
                                                                                          "IOO"
                                                                                          {:window
                                                                                           10})
                                                                                         79)
                                                                                        [(asset
                                                                                          "UVXY"
                                                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (>
                                                                                             (rsi
                                                                                              "TQQQ"
                                                                                              {:window
                                                                                               10})
                                                                                             79)
                                                                                            [(asset
                                                                                              "UVXY"
                                                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (>
                                                                                                 (rsi
                                                                                                  "VTV"
                                                                                                  {:window
                                                                                                   10})
                                                                                                 79)
                                                                                                [(asset
                                                                                                  "UVXY"
                                                                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (>
                                                                                                     (rsi
                                                                                                      "XLF"
                                                                                                      {:window
                                                                                                       10})
                                                                                                     79)
                                                                                                    [(asset
                                                                                                      "UVXY"
                                                                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (<
                                                                                                         (rsi
                                                                                                          "TQQQ"
                                                                                                          {:window
                                                                                                           10})
                                                                                                         30)
                                                                                                        [(asset
                                                                                                          "NVDL"
                                                                                                          "GraniteShares 2x Long NVDA Daily ETF")]
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (<
                                                                                                             (rsi
                                                                                                              "SPY"
                                                                                                              {:window
                                                                                                               10})
                                                                                                             30)
                                                                                                            [(asset
                                                                                                              "NVDL"
                                                                                                              "GraniteShares 2x Long NVDA Daily ETF")]
                                                                                                            [(weight-equal
                                                                                                              [(if
                                                                                                                (>
                                                                                                                 (current-price
                                                                                                                  "SPY")
                                                                                                                 (moving-average-price
                                                                                                                  "SPY"
                                                                                                                  {:window
                                                                                                                   200}))
                                                                                                                [(asset
                                                                                                                  "NVDL"
                                                                                                                  "GraniteShares 2x Long NVDA Daily ETF")]
                                                                                                                [(asset
                                                                                                                  "NVDS"
                                                                                                                  "Tradr 1.5X Short NVDA Daily ETF")])])])])])])])])])])])])])])])])])])])])])])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (moving-average-price
                                                                          "COIN"
                                                                          {:window
                                                                           7})
                                                                         (moving-average-price
                                                                          "COIN"
                                                                          {:window
                                                                           14}))
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (cumulative-return
                                                                             {:window
                                                                              2})
                                                                            (select-top
                                                                             1)
                                                                            [(asset
                                                                              "CONL"
                                                                              "GraniteShares 2x Long COIN Daily ETF")
                                                                             (asset
                                                                              "BITX"
                                                                              "2x Bitcoin Strategy ETF")])])]
                                                                        [(weight-equal
                                                                          [(group
                                                                            "Zoopy"
                                                                            [(weight-equal
                                                                              [(if
                                                                                (>
                                                                                 (rsi
                                                                                  "SPY"
                                                                                  {:window
                                                                                   10})
                                                                                 79)
                                                                                [(asset
                                                                                  "UVXY"
                                                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (>
                                                                                     (rsi
                                                                                      "IOO"
                                                                                      {:window
                                                                                       10})
                                                                                     79)
                                                                                    [(asset
                                                                                      "UVXY"
                                                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (rsi
                                                                                          "TQQQ"
                                                                                          {:window
                                                                                           10})
                                                                                         79)
                                                                                        [(asset
                                                                                          "UVXY"
                                                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (>
                                                                                             (rsi
                                                                                              "VTV"
                                                                                              {:window
                                                                                               10})
                                                                                             79)
                                                                                            [(asset
                                                                                              "UVXY"
                                                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (>
                                                                                                 (rsi
                                                                                                  "XLF"
                                                                                                  {:window
                                                                                                   10})
                                                                                                 79)
                                                                                                [(asset
                                                                                                  "UVXY"
                                                                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (<
                                                                                                     (rsi
                                                                                                      "TQQQ"
                                                                                                      {:window
                                                                                                       10})
                                                                                                     30)
                                                                                                    [(asset
                                                                                                      "NVDL"
                                                                                                      "GraniteShares 2x Long NVDA Daily ETF")]
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (<
                                                                                                         (rsi
                                                                                                          "SPY"
                                                                                                          {:window
                                                                                                           10})
                                                                                                         30)
                                                                                                        [(asset
                                                                                                          "NVDL"
                                                                                                          "GraniteShares 2x Long NVDA Daily ETF")]
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (>
                                                                                                             (current-price
                                                                                                              "SPY")
                                                                                                             (moving-average-price
                                                                                                              "SPY"
                                                                                                              {:window
                                                                                                               200}))
                                                                                                            [(asset
                                                                                                              "NVDL"
                                                                                                              "GraniteShares 2x Long NVDA Daily ETF")]
                                                                                                            [(asset
                                                                                                              "NVDS"
                                                                                                              "Tradr 1.5X Short NVDA Daily ETF")])])])])])])])])])])])])])])])])])])])])])])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (moving-average-price
                                                                      "COIN"
                                                                      {:window
                                                                       7})
                                                                     (moving-average-price
                                                                      "COIN"
                                                                      {:window
                                                                       14}))
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (cumulative-return
                                                                         {:window
                                                                          2})
                                                                        (select-top
                                                                         1)
                                                                        [(asset
                                                                          "CONL"
                                                                          "GraniteShares 2x Long COIN Daily ETF")
                                                                         (asset
                                                                          "BITX"
                                                                          "2x Bitcoin Strategy ETF")])])]
                                                                    [(weight-equal
                                                                      [(group
                                                                        "Zoopy"
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "SPY"
                                                                              {:window
                                                                               10})
                                                                             79)
                                                                            [(asset
                                                                              "UVXY"
                                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                            [(weight-equal
                                                                              [(if
                                                                                (>
                                                                                 (rsi
                                                                                  "IOO"
                                                                                  {:window
                                                                                   10})
                                                                                 79)
                                                                                [(asset
                                                                                  "UVXY"
                                                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (>
                                                                                     (rsi
                                                                                      "TQQQ"
                                                                                      {:window
                                                                                       10})
                                                                                     79)
                                                                                    [(asset
                                                                                      "UVXY"
                                                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (rsi
                                                                                          "VTV"
                                                                                          {:window
                                                                                           10})
                                                                                         79)
                                                                                        [(asset
                                                                                          "UVXY"
                                                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (>
                                                                                             (rsi
                                                                                              "XLF"
                                                                                              {:window
                                                                                               10})
                                                                                             79)
                                                                                            [(asset
                                                                                              "UVXY"
                                                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (<
                                                                                                 (rsi
                                                                                                  "TQQQ"
                                                                                                  {:window
                                                                                                   10})
                                                                                                 30)
                                                                                                [(asset
                                                                                                  "NVDL"
                                                                                                  "GraniteShares 2x Long NVDA Daily ETF")]
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (<
                                                                                                     (rsi
                                                                                                      "SPY"
                                                                                                      {:window
                                                                                                       10})
                                                                                                     30)
                                                                                                    [(asset
                                                                                                      "NVDL"
                                                                                                      "GraniteShares 2x Long NVDA Daily ETF")]
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (>
                                                                                                         (current-price
                                                                                                          "SPY")
                                                                                                         (moving-average-price
                                                                                                          "SPY"
                                                                                                          {:window
                                                                                                           200}))
                                                                                                        [(asset
                                                                                                          "NVDL"
                                                                                                          "GraniteShares 2x Long NVDA Daily ETF")]
                                                                                                        [(asset
                                                                                                          "NVDS"
                                                                                                          "Tradr 1.5X Short NVDA Daily ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]))
