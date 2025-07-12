(defsymphony
 "V1b 15/15 BB + v4 Pops - K-1  Free "
 {:asset-class "EQUITIES", :rebalance-threshold 0.01}
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
                [(asset
                  "SOXL"
                  "Direxion Daily Semiconductor Bull 3x Shares")]
                [(asset
                  "SOXS"
                  "Direxion Daily Semiconductor Bear 3x Shares")])])])])]
        [(weight-equal
          [(if
            (< (rsi "SPY" {:window 6}) 27)
            [(group
              "Extremely oversold S&P (low RSI). Double check with bond mkt before going long"
              [(weight-equal
                [(if
                  (< (rsi "BSV" {:window 7}) (rsi "SPHB" {:window 7}))
                  [(weight-equal
                    [(filter
                      (rsi {:window 7})
                      (select-bottom 1)
                      [(asset
                        "SOXS"
                        "Direxion Daily Semiconductor Bear 3x Shares")
                       (asset
                        "SQQQ"
                        "ProShares UltraPro Short QQQ")])])]
                  [(weight-equal
                    [(filter
                      (rsi {:window 7})
                      (select-bottom 1)
                      [(asset
                        "SOXL"
                        "Direxion Daily Semiconductor Bull 3x Shares")
                       (asset
                        "TECL"
                        "Direxion Daily Technology Bull 3x Shares")])])])])])]
            [(weight-equal
              [(group
                "v4 Pops - K-1 Free - Longer Backtest"
                [(weight-equal
                  [(if
                    (> (rsi "QQQE" {:window 10}) 79)
                    [(asset
                      "SOXS"
                      "Direxion Daily Semiconductor Bear 3x Shares")]
                    [(weight-equal
                      [(if
                        (> (rsi "VTV" {:window 10}) 79)
                        [(asset
                          "SOXS"
                          "Direxion Daily Semiconductor Bear 3x Shares")]
                        [(weight-equal
                          [(if
                            (> (rsi "VOX" {:window 10}) 79)
                            [(asset
                              "SOXS"
                              "Direxion Daily Semiconductor Bear 3x Shares")]
                            [(weight-equal
                              [(if
                                (<= (max-drawdown "SPY" {:window 9}) 0)
                                [(asset
                                  "SOXS"
                                  "Direxion Daily Semiconductor Bear 3x Shares")]
                                [(weight-equal
                                  [(if
                                    (> (rsi "TECL" {:window 10}) 79)
                                    [(asset
                                      "SOXS"
                                      "Direxion Daily Semiconductor Bear 3x Shares")]
                                    [(weight-equal
                                      [(if
                                        (>
                                         (rsi "VOOG" {:window 10})
                                         79)
                                        [(asset
                                          "SOXS"
                                          "Direxion Daily Semiconductor Bear 3x Shares")]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "VOOV" {:window 10})
                                             79)
                                            [(asset
                                              "SOXS"
                                              "Direxion Daily Semiconductor Bear 3x Shares")]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "XLP"
                                                  {:window 10})
                                                 75)
                                                [(asset
                                                  "SOXS"
                                                  "Direxion Daily Semiconductor Bear 3x Shares")]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "TQQQ"
                                                      {:window 10})
                                                     79)
                                                    [(weight-equal
                                                      [(asset
                                                        "SOXS"
                                                        "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "XLY"
                                                          {:window 10})
                                                         80)
                                                        [(asset
                                                          "SOXS"
                                                          "Direxion Daily Semiconductor Bear 3x Shares")]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "FAS"
                                                              {:window
                                                               10})
                                                             80)
                                                            [(asset
                                                              "SOXS"
                                                              "Direxion Daily Semiconductor Bear 3x Shares")]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 80)
                                                                [(asset
                                                                  "SOXS"
                                                                  "Direxion Daily Semiconductor Bear 3x Shares")]
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
                                                                        [(weight-equal
                                                                          [(asset
                                                                            "SOXS"
                                                                            "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                        [(weight-equal
                                                                          [(group
                                                                            "VMS popped TECL or Not"
                                                                            [(weight-equal
                                                                              [(if
                                                                                (>
                                                                                 (rsi
                                                                                  "XLK"
                                                                                  {:window
                                                                                   126})
                                                                                 (rsi
                                                                                  "XLP"
                                                                                  {:window
                                                                                   126}))
                                                                                [(weight-equal
                                                                                  [(group
                                                                                    "Bullish Market Conditions"
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (rsi
                                                                                          "TQQQ"
                                                                                          {:window
                                                                                           10})
                                                                                         80)
                                                                                        [(weight-equal
                                                                                          [(asset
                                                                                            "SOXS"
                                                                                            "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (<
                                                                                             (rsi
                                                                                              "TQQQ"
                                                                                              {:window
                                                                                               10})
                                                                                             31)
                                                                                            [(weight-equal
                                                                                              [(filter
                                                                                                (moving-average-return
                                                                                                 {:window
                                                                                                  5})
                                                                                                (select-bottom
                                                                                                 1)
                                                                                                [(asset
                                                                                                  "TECL"
                                                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                                                 (asset
                                                                                                  "SOXL"
                                                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                                 (asset
                                                                                                  "TMF"
                                                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (>
                                                                                                 (rsi
                                                                                                  "VIXY"
                                                                                                  {:window
                                                                                                   10})
                                                                                                 50)
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (<
                                                                                                     (moving-average-return
                                                                                                      "VIXY"
                                                                                                      {:window
                                                                                                       5})
                                                                                                     0)
                                                                                                    [(group
                                                                                                      "1st Block"
                                                                                                      [(weight-equal
                                                                                                        [(if
                                                                                                          (>
                                                                                                           (cumulative-return
                                                                                                            "TQQQ"
                                                                                                            {:window
                                                                                                             1})
                                                                                                           5.5)
                                                                                                          [(weight-equal
                                                                                                            [(asset
                                                                                                              "SOXS"
                                                                                                              "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                          [(weight-equal
                                                                                                            [(group
                                                                                                              "TECL or Not"
                                                                                                              [(weight-equal
                                                                                                                [(if
                                                                                                                  (>
                                                                                                                   (rsi
                                                                                                                    "TQQQ"
                                                                                                                    {:window
                                                                                                                     10})
                                                                                                                   79)
                                                                                                                  [(asset
                                                                                                                    "SOXS"
                                                                                                                    "Direxion Daily Semiconductor Bear 3x Shares")]
                                                                                                                  [(weight-equal
                                                                                                                    [(group
                                                                                                                      "Huge volatility"
                                                                                                                      [(weight-equal
                                                                                                                        [(if
                                                                                                                          (<
                                                                                                                           (cumulative-return
                                                                                                                            "TQQQ"
                                                                                                                            {:window
                                                                                                                             6})
                                                                                                                           -13)
                                                                                                                          [(weight-equal
                                                                                                                            [(if
                                                                                                                              (>
                                                                                                                               (cumulative-return
                                                                                                                                "TQQQ"
                                                                                                                                {:window
                                                                                                                                 1})
                                                                                                                               6)
                                                                                                                              [(weight-equal
                                                                                                                                [(asset
                                                                                                                                  "SOXS"
                                                                                                                                  "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                                              [(weight-equal
                                                                                                                                [(group
                                                                                                                                  "Mean Rev"
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (<
                                                                                                                                       (rsi
                                                                                                                                        "TQQQ"
                                                                                                                                        {:window
                                                                                                                                         10})
                                                                                                                                       32)
                                                                                                                                      [(asset
                                                                                                                                        "TECL"
                                                                                                                                        "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(if
                                                                                                                                          (<
                                                                                                                                           (max-drawdown
                                                                                                                                            "TMF"
                                                                                                                                            {:window
                                                                                                                                             10})
                                                                                                                                           7)
                                                                                                                                          [(asset
                                                                                                                                            "TECL"
                                                                                                                                            "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                          [(weight-equal
                                                                                                                                            [(asset
                                                                                                                                              "BIL"
                                                                                                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                                                                                                                          [(weight-equal
                                                                                                                            [(group
                                                                                                                              "Normal market"
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (>
                                                                                                                                   (max-drawdown
                                                                                                                                    "QQQ"
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   6)
                                                                                                                                  [(weight-equal
                                                                                                                                    [(asset
                                                                                                                                      "BIL"
                                                                                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (>
                                                                                                                                       (max-drawdown
                                                                                                                                        "TMF"
                                                                                                                                        {:window
                                                                                                                                         10})
                                                                                                                                       7)
                                                                                                                                      [(weight-equal
                                                                                                                                        [(asset
                                                                                                                                          "BIL"
                                                                                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
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
                                                                                                                                            [(asset
                                                                                                                                              "TECL"
                                                                                                                                              "Direxion Daily Technology Bull 3x Shares")])]
                                                                                                                                          [(weight-equal
                                                                                                                                            [(if
                                                                                                                                              (>
                                                                                                                                               (rsi
                                                                                                                                                "SPY"
                                                                                                                                                {:window
                                                                                                                                                 60})
                                                                                                                                               50)
                                                                                                                                              [(group
                                                                                                                                                "Bond > Stock"
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(if
                                                                                                                                                    (>
                                                                                                                                                     (rsi
                                                                                                                                                      "BND"
                                                                                                                                                      {:window
                                                                                                                                                       45})
                                                                                                                                                     (rsi
                                                                                                                                                      "SPY"
                                                                                                                                                      {:window
                                                                                                                                                       45}))
                                                                                                                                                    [(asset
                                                                                                                                                      "TECL"
                                                                                                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(asset
                                                                                                                                                        "BIL"
                                                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                                                                                                                                              [(group
                                                                                                                                                "Bond Mid-term < Long-term"
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(if
                                                                                                                                                    (<
                                                                                                                                                     (rsi
                                                                                                                                                      "IEF"
                                                                                                                                                      {:window
                                                                                                                                                       200})
                                                                                                                                                     (rsi
                                                                                                                                                      "TLT"
                                                                                                                                                      {:window
                                                                                                                                                       200}))
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(if
                                                                                                                                                        (>
                                                                                                                                                         (rsi
                                                                                                                                                          "BND"
                                                                                                                                                          {:window
                                                                                                                                                           45})
                                                                                                                                                         (rsi
                                                                                                                                                          "SPY"
                                                                                                                                                          {:window
                                                                                                                                                           45}))
                                                                                                                                                        [(asset
                                                                                                                                                          "TECL"
                                                                                                                                                          "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                        [(weight-equal
                                                                                                                                                          [(asset
                                                                                                                                                            "BIL"
                                                                                                                                                            "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(asset
                                                                                                                                                        "BIL"
                                                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])]
                                                                                                    [(group
                                                                                                      "2nd Block"
                                                                                                      [(weight-equal
                                                                                                        [(if
                                                                                                          (>
                                                                                                           (cumulative-return
                                                                                                            "TQQQ"
                                                                                                            {:window
                                                                                                             1})
                                                                                                           5.5)
                                                                                                          [(weight-equal
                                                                                                            [(filter
                                                                                                              (exponential-moving-average-price
                                                                                                               {:window
                                                                                                                5})
                                                                                                              (select-bottom
                                                                                                               1)
                                                                                                              [(asset
                                                                                                                "SOXS"
                                                                                                                "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                                               (asset
                                                                                                                "TECS"
                                                                                                                "Direxion Daily Technology Bear 3X Shares")])])]
                                                                                                          [(weight-equal
                                                                                                            [(group
                                                                                                              "TECL or Not"
                                                                                                              [(weight-equal
                                                                                                                [(if
                                                                                                                  (>
                                                                                                                   (rsi
                                                                                                                    "TQQQ"
                                                                                                                    {:window
                                                                                                                     10})
                                                                                                                   79)
                                                                                                                  [(asset
                                                                                                                    "SOXS"
                                                                                                                    "Direxion Daily Semiconductor Bear 3x Shares")]
                                                                                                                  [(weight-equal
                                                                                                                    [(group
                                                                                                                      "Huge volatility"
                                                                                                                      [(weight-equal
                                                                                                                        [(if
                                                                                                                          (<
                                                                                                                           (cumulative-return
                                                                                                                            "TQQQ"
                                                                                                                            {:window
                                                                                                                             6})
                                                                                                                           -13)
                                                                                                                          [(weight-equal
                                                                                                                            [(if
                                                                                                                              (>
                                                                                                                               (cumulative-return
                                                                                                                                "TQQQ"
                                                                                                                                {:window
                                                                                                                                 1})
                                                                                                                               6)
                                                                                                                              [(weight-equal
                                                                                                                                [(asset
                                                                                                                                  "SOXS"
                                                                                                                                  "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                                              [(weight-equal
                                                                                                                                [(group
                                                                                                                                  "Mean Rev"
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (<
                                                                                                                                       (rsi
                                                                                                                                        "TQQQ"
                                                                                                                                        {:window
                                                                                                                                         10})
                                                                                                                                       32)
                                                                                                                                      [(asset
                                                                                                                                        "TECL"
                                                                                                                                        "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(if
                                                                                                                                          (<
                                                                                                                                           (max-drawdown
                                                                                                                                            "TMF"
                                                                                                                                            {:window
                                                                                                                                             10})
                                                                                                                                           7)
                                                                                                                                          [(asset
                                                                                                                                            "TECL"
                                                                                                                                            "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                          [(weight-equal
                                                                                                                                            [(asset
                                                                                                                                              "BIL"
                                                                                                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                                                                                                                          [(weight-equal
                                                                                                                            [(group
                                                                                                                              "Normal market"
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (>
                                                                                                                                   (max-drawdown
                                                                                                                                    "QQQ"
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   6)
                                                                                                                                  [(weight-equal
                                                                                                                                    [(asset
                                                                                                                                      "BIL"
                                                                                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (>
                                                                                                                                       (max-drawdown
                                                                                                                                        "TMF"
                                                                                                                                        {:window
                                                                                                                                         10})
                                                                                                                                       7)
                                                                                                                                      [(weight-equal
                                                                                                                                        [(asset
                                                                                                                                          "BIL"
                                                                                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
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
                                                                                                                                            [(asset
                                                                                                                                              "TECL"
                                                                                                                                              "Direxion Daily Technology Bull 3x Shares")])]
                                                                                                                                          [(weight-equal
                                                                                                                                            [(if
                                                                                                                                              (>
                                                                                                                                               (rsi
                                                                                                                                                "SPY"
                                                                                                                                                {:window
                                                                                                                                                 60})
                                                                                                                                               50)
                                                                                                                                              [(group
                                                                                                                                                "Bond > Stock"
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(if
                                                                                                                                                    (>
                                                                                                                                                     (rsi
                                                                                                                                                      "BND"
                                                                                                                                                      {:window
                                                                                                                                                       45})
                                                                                                                                                     (rsi
                                                                                                                                                      "SPY"
                                                                                                                                                      {:window
                                                                                                                                                       45}))
                                                                                                                                                    [(asset
                                                                                                                                                      "TECL"
                                                                                                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(asset
                                                                                                                                                        "BIL"
                                                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                                                                                                                                              [(group
                                                                                                                                                "Bond Mid-term < Long-term"
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(if
                                                                                                                                                    (<
                                                                                                                                                     (rsi
                                                                                                                                                      "IEF"
                                                                                                                                                      {:window
                                                                                                                                                       200})
                                                                                                                                                     (rsi
                                                                                                                                                      "TLT"
                                                                                                                                                      {:window
                                                                                                                                                       200}))
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(if
                                                                                                                                                        (>
                                                                                                                                                         (rsi
                                                                                                                                                          "BND"
                                                                                                                                                          {:window
                                                                                                                                                           45})
                                                                                                                                                         (rsi
                                                                                                                                                          "SPY"
                                                                                                                                                          {:window
                                                                                                                                                           45}))
                                                                                                                                                        [(asset
                                                                                                                                                          "TECL"
                                                                                                                                                          "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                        [(weight-equal
                                                                                                                                                          [(asset
                                                                                                                                                            "BIL"
                                                                                                                                                            "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(asset
                                                                                                                                                        "BIL"
                                                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])]
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (<
                                                                                                     (moving-average-return
                                                                                                      "VIXY"
                                                                                                      {:window
                                                                                                       5})
                                                                                                     0)
                                                                                                    [(group
                                                                                                      "3rd Block"
                                                                                                      [(weight-equal
                                                                                                        [(if
                                                                                                          (>
                                                                                                           (cumulative-return
                                                                                                            "TQQQ"
                                                                                                            {:window
                                                                                                             1})
                                                                                                           5.5)
                                                                                                          [(weight-equal
                                                                                                            [(filter
                                                                                                              (exponential-moving-average-price
                                                                                                               {:window
                                                                                                                5})
                                                                                                              (select-bottom
                                                                                                               1)
                                                                                                              [(asset
                                                                                                                "SOXS"
                                                                                                                "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                                               (asset
                                                                                                                "TECS"
                                                                                                                "Direxion Daily Technology Bear 3X Shares")])])]
                                                                                                          [(weight-equal
                                                                                                            [(group
                                                                                                              "TECL or Not"
                                                                                                              [(weight-equal
                                                                                                                [(if
                                                                                                                  (>
                                                                                                                   (rsi
                                                                                                                    "TQQQ"
                                                                                                                    {:window
                                                                                                                     10})
                                                                                                                   79)
                                                                                                                  [(asset
                                                                                                                    "SOXS"
                                                                                                                    "Direxion Daily Semiconductor Bear 3x Shares")]
                                                                                                                  [(weight-equal
                                                                                                                    [(group
                                                                                                                      "Huge volatility"
                                                                                                                      [(weight-equal
                                                                                                                        [(if
                                                                                                                          (<
                                                                                                                           (cumulative-return
                                                                                                                            "TQQQ"
                                                                                                                            {:window
                                                                                                                             6})
                                                                                                                           -13)
                                                                                                                          [(weight-equal
                                                                                                                            [(if
                                                                                                                              (>
                                                                                                                               (cumulative-return
                                                                                                                                "TQQQ"
                                                                                                                                {:window
                                                                                                                                 1})
                                                                                                                               6)
                                                                                                                              [(weight-equal
                                                                                                                                [(asset
                                                                                                                                  "SOXS"
                                                                                                                                  "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                                              [(weight-equal
                                                                                                                                [(group
                                                                                                                                  "Mean Rev"
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (<
                                                                                                                                       (rsi
                                                                                                                                        "TQQQ"
                                                                                                                                        {:window
                                                                                                                                         10})
                                                                                                                                       32)
                                                                                                                                      [(asset
                                                                                                                                        "TECL"
                                                                                                                                        "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(if
                                                                                                                                          (<
                                                                                                                                           (max-drawdown
                                                                                                                                            "TMF"
                                                                                                                                            {:window
                                                                                                                                             10})
                                                                                                                                           7)
                                                                                                                                          [(asset
                                                                                                                                            "TECL"
                                                                                                                                            "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                          [(weight-equal
                                                                                                                                            [(asset
                                                                                                                                              "BIL"
                                                                                                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                                                                                                                          [(weight-equal
                                                                                                                            [(group
                                                                                                                              "Normal market"
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (>
                                                                                                                                   (max-drawdown
                                                                                                                                    "QQQ"
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   6)
                                                                                                                                  [(weight-equal
                                                                                                                                    [(asset
                                                                                                                                      "BIL"
                                                                                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (>
                                                                                                                                       (max-drawdown
                                                                                                                                        "TMF"
                                                                                                                                        {:window
                                                                                                                                         10})
                                                                                                                                       7)
                                                                                                                                      [(weight-equal
                                                                                                                                        [(asset
                                                                                                                                          "BIL"
                                                                                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
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
                                                                                                                                            [(asset
                                                                                                                                              "TECL"
                                                                                                                                              "Direxion Daily Technology Bull 3x Shares")])]
                                                                                                                                          [(weight-equal
                                                                                                                                            [(if
                                                                                                                                              (>
                                                                                                                                               (rsi
                                                                                                                                                "SPY"
                                                                                                                                                {:window
                                                                                                                                                 60})
                                                                                                                                               50)
                                                                                                                                              [(group
                                                                                                                                                "Bond > Stock"
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(if
                                                                                                                                                    (>
                                                                                                                                                     (rsi
                                                                                                                                                      "BND"
                                                                                                                                                      {:window
                                                                                                                                                       45})
                                                                                                                                                     (rsi
                                                                                                                                                      "SPY"
                                                                                                                                                      {:window
                                                                                                                                                       45}))
                                                                                                                                                    [(asset
                                                                                                                                                      "TECL"
                                                                                                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(asset
                                                                                                                                                        "BIL"
                                                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                                                                                                                                              [(group
                                                                                                                                                "Bond Mid-term < Long-term"
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(if
                                                                                                                                                    (<
                                                                                                                                                     (rsi
                                                                                                                                                      "IEF"
                                                                                                                                                      {:window
                                                                                                                                                       200})
                                                                                                                                                     (rsi
                                                                                                                                                      "TLT"
                                                                                                                                                      {:window
                                                                                                                                                       200}))
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(if
                                                                                                                                                        (>
                                                                                                                                                         (rsi
                                                                                                                                                          "BND"
                                                                                                                                                          {:window
                                                                                                                                                           45})
                                                                                                                                                         (rsi
                                                                                                                                                          "SPY"
                                                                                                                                                          {:window
                                                                                                                                                           45}))
                                                                                                                                                        [(asset
                                                                                                                                                          "TECL"
                                                                                                                                                          "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                        [(weight-equal
                                                                                                                                                          [(asset
                                                                                                                                                            "BIL"
                                                                                                                                                            "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(asset
                                                                                                                                                        "BIL"
                                                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])]
                                                                                                    [(group
                                                                                                      "4th Block"
                                                                                                      [(weight-equal
                                                                                                        [(if
                                                                                                          (>
                                                                                                           (cumulative-return
                                                                                                            "TQQQ"
                                                                                                            {:window
                                                                                                             1})
                                                                                                           5.5)
                                                                                                          [(weight-equal
                                                                                                            [(filter
                                                                                                              (exponential-moving-average-price
                                                                                                               {:window
                                                                                                                5})
                                                                                                              (select-top
                                                                                                               1)
                                                                                                              [(asset
                                                                                                                "SOXS"
                                                                                                                "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                                               (asset
                                                                                                                "TECS"
                                                                                                                "Direxion Daily Technology Bear 3X Shares")])])]
                                                                                                          [(weight-equal
                                                                                                            [(group
                                                                                                              "TECL or Not"
                                                                                                              [(weight-equal
                                                                                                                [(if
                                                                                                                  (>
                                                                                                                   (rsi
                                                                                                                    "TQQQ"
                                                                                                                    {:window
                                                                                                                     10})
                                                                                                                   79)
                                                                                                                  [(asset
                                                                                                                    "SOXS"
                                                                                                                    "Direxion Daily Semiconductor Bear 3x Shares")]
                                                                                                                  [(weight-equal
                                                                                                                    [(group
                                                                                                                      "Huge volatility"
                                                                                                                      [(weight-equal
                                                                                                                        [(if
                                                                                                                          (<
                                                                                                                           (cumulative-return
                                                                                                                            "TQQQ"
                                                                                                                            {:window
                                                                                                                             6})
                                                                                                                           -13)
                                                                                                                          [(weight-equal
                                                                                                                            [(if
                                                                                                                              (>
                                                                                                                               (cumulative-return
                                                                                                                                "TQQQ"
                                                                                                                                {:window
                                                                                                                                 1})
                                                                                                                               6)
                                                                                                                              [(weight-equal
                                                                                                                                [(asset
                                                                                                                                  "SOXS"
                                                                                                                                  "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                                              [(weight-equal
                                                                                                                                [(group
                                                                                                                                  "Mean Rev"
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (<
                                                                                                                                       (rsi
                                                                                                                                        "TQQQ"
                                                                                                                                        {:window
                                                                                                                                         10})
                                                                                                                                       32)
                                                                                                                                      [(asset
                                                                                                                                        "TECL"
                                                                                                                                        "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(if
                                                                                                                                          (<
                                                                                                                                           (max-drawdown
                                                                                                                                            "TMF"
                                                                                                                                            {:window
                                                                                                                                             10})
                                                                                                                                           7)
                                                                                                                                          [(asset
                                                                                                                                            "TECL"
                                                                                                                                            "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                          [(weight-equal
                                                                                                                                            [(asset
                                                                                                                                              "BIL"
                                                                                                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                                                                                                                          [(weight-equal
                                                                                                                            [(group
                                                                                                                              "Normal market"
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (>
                                                                                                                                   (max-drawdown
                                                                                                                                    "QQQ"
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   6)
                                                                                                                                  [(weight-equal
                                                                                                                                    [(asset
                                                                                                                                      "BIL"
                                                                                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (>
                                                                                                                                       (max-drawdown
                                                                                                                                        "TMF"
                                                                                                                                        {:window
                                                                                                                                         10})
                                                                                                                                       7)
                                                                                                                                      [(weight-equal
                                                                                                                                        [(asset
                                                                                                                                          "BIL"
                                                                                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
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
                                                                                                                                            [(asset
                                                                                                                                              "TECL"
                                                                                                                                              "Direxion Daily Technology Bull 3x Shares")])]
                                                                                                                                          [(weight-equal
                                                                                                                                            [(if
                                                                                                                                              (>
                                                                                                                                               (rsi
                                                                                                                                                "SPY"
                                                                                                                                                {:window
                                                                                                                                                 60})
                                                                                                                                               50)
                                                                                                                                              [(group
                                                                                                                                                "Bond > Stock"
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(if
                                                                                                                                                    (>
                                                                                                                                                     (rsi
                                                                                                                                                      "BND"
                                                                                                                                                      {:window
                                                                                                                                                       45})
                                                                                                                                                     (rsi
                                                                                                                                                      "SPY"
                                                                                                                                                      {:window
                                                                                                                                                       45}))
                                                                                                                                                    [(asset
                                                                                                                                                      "TECL"
                                                                                                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(asset
                                                                                                                                                        "BIL"
                                                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                                                                                                                                              [(group
                                                                                                                                                "Bond Mid-term < Long-term"
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(if
                                                                                                                                                    (<
                                                                                                                                                     (rsi
                                                                                                                                                      "IEF"
                                                                                                                                                      {:window
                                                                                                                                                       200})
                                                                                                                                                     (rsi
                                                                                                                                                      "TLT"
                                                                                                                                                      {:window
                                                                                                                                                       200}))
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(if
                                                                                                                                                        (>
                                                                                                                                                         (rsi
                                                                                                                                                          "BND"
                                                                                                                                                          {:window
                                                                                                                                                           45})
                                                                                                                                                         (rsi
                                                                                                                                                          "SPY"
                                                                                                                                                          {:window
                                                                                                                                                           45}))
                                                                                                                                                        [(asset
                                                                                                                                                          "TECL"
                                                                                                                                                          "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                        [(weight-equal
                                                                                                                                                          [(asset
                                                                                                                                                            "BIL"
                                                                                                                                                            "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(asset
                                                                                                                                                        "BIL"
                                                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]
                                                                                [(weight-equal
                                                                                  [(group
                                                                                    "Danger Market Conditions"
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (rsi
                                                                                          "TQQQ"
                                                                                          {:window
                                                                                           10})
                                                                                         80)
                                                                                        [(weight-equal
                                                                                          [(filter
                                                                                            (cumulative-return
                                                                                             {:window
                                                                                              5})
                                                                                            (select-bottom
                                                                                             1)
                                                                                            [(asset
                                                                                              "TMV"
                                                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                                             (asset
                                                                                              "BIL"
                                                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (>
                                                                                             (rsi
                                                                                              "VIXY"
                                                                                              {:window
                                                                                               10})
                                                                                             50)
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (<
                                                                                                 (rsi
                                                                                                  "TQQQ"
                                                                                                  {:window
                                                                                                   10})
                                                                                                 31)
                                                                                                [(weight-equal
                                                                                                  [(filter
                                                                                                    (stdev-price
                                                                                                     {:window
                                                                                                      5})
                                                                                                    (select-bottom
                                                                                                     1)
                                                                                                    [(asset
                                                                                                      "SOXL"
                                                                                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                                     (asset
                                                                                                      "ERX"
                                                                                                      "Direxion Daily Energy Bull 2x Shares")
                                                                                                     (asset
                                                                                                      "TMV"
                                                                                                      "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])]
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (<
                                                                                                     (moving-average-return
                                                                                                      "VIXY"
                                                                                                      {:window
                                                                                                       5})
                                                                                                     0)
                                                                                                    [(weight-equal
                                                                                                      [(asset
                                                                                                        "SOXL"
                                                                                                        "Direxion Daily Semiconductor Bull 3x Shares")])]
                                                                                                    [(weight-equal
                                                                                                      [(group
                                                                                                        "TECL or Not"
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (>
                                                                                                             (rsi
                                                                                                              "TQQQ"
                                                                                                              {:window
                                                                                                               10})
                                                                                                             79)
                                                                                                            [(asset
                                                                                                              "SOXS"
                                                                                                              "Direxion Daily Semiconductor Bear 3x Shares")]
                                                                                                            [(weight-equal
                                                                                                              [(group
                                                                                                                "Huge volatility"
                                                                                                                [(weight-equal
                                                                                                                  [(if
                                                                                                                    (<
                                                                                                                     (cumulative-return
                                                                                                                      "TQQQ"
                                                                                                                      {:window
                                                                                                                       6})
                                                                                                                     -13)
                                                                                                                    [(weight-equal
                                                                                                                      [(if
                                                                                                                        (>
                                                                                                                         (cumulative-return
                                                                                                                          "TQQQ"
                                                                                                                          {:window
                                                                                                                           1})
                                                                                                                         6)
                                                                                                                        [(weight-equal
                                                                                                                          [(asset
                                                                                                                            "SOXS"
                                                                                                                            "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                                        [(weight-equal
                                                                                                                          [(group
                                                                                                                            "Mean Rev"
                                                                                                                            [(weight-equal
                                                                                                                              [(if
                                                                                                                                (<
                                                                                                                                 (rsi
                                                                                                                                  "TQQQ"
                                                                                                                                  {:window
                                                                                                                                   10})
                                                                                                                                 32)
                                                                                                                                [(asset
                                                                                                                                  "TECL"
                                                                                                                                  "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                [(weight-equal
                                                                                                                                  [(if
                                                                                                                                    (<
                                                                                                                                     (max-drawdown
                                                                                                                                      "TMF"
                                                                                                                                      {:window
                                                                                                                                       10})
                                                                                                                                     7)
                                                                                                                                    [(asset
                                                                                                                                      "TECL"
                                                                                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                    [(weight-equal
                                                                                                                                      [(asset
                                                                                                                                        "BIL"
                                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                                                                                                                    [(weight-equal
                                                                                                                      [(group
                                                                                                                        "Normal market"
                                                                                                                        [(weight-equal
                                                                                                                          [(if
                                                                                                                            (>
                                                                                                                             (max-drawdown
                                                                                                                              "QQQ"
                                                                                                                              {:window
                                                                                                                               10})
                                                                                                                             6)
                                                                                                                            [(weight-equal
                                                                                                                              [(asset
                                                                                                                                "BIL"
                                                                                                                                "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                                                                                                                            [(weight-equal
                                                                                                                              [(if
                                                                                                                                (>
                                                                                                                                 (max-drawdown
                                                                                                                                  "TMF"
                                                                                                                                  {:window
                                                                                                                                   10})
                                                                                                                                 7)
                                                                                                                                [(weight-equal
                                                                                                                                  [(asset
                                                                                                                                    "BIL"
                                                                                                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
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
                                                                                                                                      [(asset
                                                                                                                                        "TECL"
                                                                                                                                        "Direxion Daily Technology Bull 3x Shares")])]
                                                                                                                                    [(weight-equal
                                                                                                                                      [(if
                                                                                                                                        (>
                                                                                                                                         (rsi
                                                                                                                                          "SPY"
                                                                                                                                          {:window
                                                                                                                                           60})
                                                                                                                                         50)
                                                                                                                                        [(group
                                                                                                                                          "Bond > Stock"
                                                                                                                                          [(weight-equal
                                                                                                                                            [(if
                                                                                                                                              (>
                                                                                                                                               (rsi
                                                                                                                                                "BND"
                                                                                                                                                {:window
                                                                                                                                                 45})
                                                                                                                                               (rsi
                                                                                                                                                "SPY"
                                                                                                                                                {:window
                                                                                                                                                 45}))
                                                                                                                                              [(asset
                                                                                                                                                "TECL"
                                                                                                                                                "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                              [(weight-equal
                                                                                                                                                [(asset
                                                                                                                                                  "BIL"
                                                                                                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                                                                                                                                        [(group
                                                                                                                                          "Bond Mid-term < Long-term"
                                                                                                                                          [(weight-equal
                                                                                                                                            [(if
                                                                                                                                              (<
                                                                                                                                               (rsi
                                                                                                                                                "IEF"
                                                                                                                                                {:window
                                                                                                                                                 200})
                                                                                                                                               (rsi
                                                                                                                                                "TLT"
                                                                                                                                                {:window
                                                                                                                                                 200}))
                                                                                                                                              [(weight-equal
                                                                                                                                                [(if
                                                                                                                                                  (>
                                                                                                                                                   (rsi
                                                                                                                                                    "BND"
                                                                                                                                                    {:window
                                                                                                                                                     45})
                                                                                                                                                   (rsi
                                                                                                                                                    "SPY"
                                                                                                                                                    {:window
                                                                                                                                                     45}))
                                                                                                                                                  [(asset
                                                                                                                                                    "TECL"
                                                                                                                                                    "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                  [(weight-equal
                                                                                                                                                    [(asset
                                                                                                                                                      "BIL"
                                                                                                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                                                                                                                              [(weight-equal
                                                                                                                                                [(asset
                                                                                                                                                  "BIL"
                                                                                                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])]
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (<
                                                                                                 (rsi
                                                                                                  "TQQQ"
                                                                                                  {:window
                                                                                                   10})
                                                                                                 31)
                                                                                                [(weight-equal
                                                                                                  [(asset
                                                                                                    "SOXL"
                                                                                                    "Direxion Daily Semiconductor Bull 3x Shares")])]
                                                                                                [(weight-equal
                                                                                                  [(group
                                                                                                    "TECL or Not"
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (>
                                                                                                         (rsi
                                                                                                          "TQQQ"
                                                                                                          {:window
                                                                                                           10})
                                                                                                         79)
                                                                                                        [(asset
                                                                                                          "SOXS"
                                                                                                          "Direxion Daily Semiconductor Bear 3x Shares")]
                                                                                                        [(weight-equal
                                                                                                          [(group
                                                                                                            "Huge volatility"
                                                                                                            [(weight-equal
                                                                                                              [(if
                                                                                                                (<
                                                                                                                 (cumulative-return
                                                                                                                  "TQQQ"
                                                                                                                  {:window
                                                                                                                   6})
                                                                                                                 -13)
                                                                                                                [(weight-equal
                                                                                                                  [(if
                                                                                                                    (>
                                                                                                                     (cumulative-return
                                                                                                                      "TQQQ"
                                                                                                                      {:window
                                                                                                                       1})
                                                                                                                     6)
                                                                                                                    [(weight-equal
                                                                                                                      [(asset
                                                                                                                        "SOXS"
                                                                                                                        "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                                    [(weight-equal
                                                                                                                      [(group
                                                                                                                        "Mean Rev"
                                                                                                                        [(weight-equal
                                                                                                                          [(if
                                                                                                                            (<
                                                                                                                             (rsi
                                                                                                                              "TQQQ"
                                                                                                                              {:window
                                                                                                                               10})
                                                                                                                             32)
                                                                                                                            [(asset
                                                                                                                              "TECL"
                                                                                                                              "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                            [(weight-equal
                                                                                                                              [(if
                                                                                                                                (<
                                                                                                                                 (max-drawdown
                                                                                                                                  "TMF"
                                                                                                                                  {:window
                                                                                                                                   10})
                                                                                                                                 7)
                                                                                                                                [(asset
                                                                                                                                  "TECL"
                                                                                                                                  "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                [(weight-equal
                                                                                                                                  [(asset
                                                                                                                                    "BIL"
                                                                                                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                                                                                                                [(weight-equal
                                                                                                                  [(group
                                                                                                                    "Normal market"
                                                                                                                    [(weight-equal
                                                                                                                      [(if
                                                                                                                        (>
                                                                                                                         (max-drawdown
                                                                                                                          "QQQ"
                                                                                                                          {:window
                                                                                                                           10})
                                                                                                                         6)
                                                                                                                        [(weight-equal
                                                                                                                          [(asset
                                                                                                                            "BIL"
                                                                                                                            "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                                                                                                                        [(weight-equal
                                                                                                                          [(if
                                                                                                                            (>
                                                                                                                             (max-drawdown
                                                                                                                              "TMF"
                                                                                                                              {:window
                                                                                                                               10})
                                                                                                                             7)
                                                                                                                            [(weight-equal
                                                                                                                              [(asset
                                                                                                                                "BIL"
                                                                                                                                "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
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
                                                                                                                                  [(asset
                                                                                                                                    "TECL"
                                                                                                                                    "Direxion Daily Technology Bull 3x Shares")])]
                                                                                                                                [(weight-equal
                                                                                                                                  [(if
                                                                                                                                    (>
                                                                                                                                     (rsi
                                                                                                                                      "SPY"
                                                                                                                                      {:window
                                                                                                                                       60})
                                                                                                                                     50)
                                                                                                                                    [(group
                                                                                                                                      "Bond > Stock"
                                                                                                                                      [(weight-equal
                                                                                                                                        [(if
                                                                                                                                          (>
                                                                                                                                           (rsi
                                                                                                                                            "BND"
                                                                                                                                            {:window
                                                                                                                                             45})
                                                                                                                                           (rsi
                                                                                                                                            "SPY"
                                                                                                                                            {:window
                                                                                                                                             45}))
                                                                                                                                          [(asset
                                                                                                                                            "TECL"
                                                                                                                                            "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                          [(weight-equal
                                                                                                                                            [(asset
                                                                                                                                              "BIL"
                                                                                                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                                                                                                                                    [(group
                                                                                                                                      "Bond Mid-term < Long-term"
                                                                                                                                      [(weight-equal
                                                                                                                                        [(if
                                                                                                                                          (<
                                                                                                                                           (rsi
                                                                                                                                            "IEF"
                                                                                                                                            {:window
                                                                                                                                             200})
                                                                                                                                           (rsi
                                                                                                                                            "TLT"
                                                                                                                                            {:window
                                                                                                                                             200}))
                                                                                                                                          [(weight-equal
                                                                                                                                            [(if
                                                                                                                                              (>
                                                                                                                                               (rsi
                                                                                                                                                "BND"
                                                                                                                                                {:window
                                                                                                                                                 45})
                                                                                                                                               (rsi
                                                                                                                                                "SPY"
                                                                                                                                                {:window
                                                                                                                                                 45}))
                                                                                                                                              [(asset
                                                                                                                                                "TECL"
                                                                                                                                                "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                              [(weight-equal
                                                                                                                                                [(asset
                                                                                                                                                  "BIL"
                                                                                                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                                                                                                                          [(weight-equal
                                                                                                                                            [(asset
                                                                                                                                              "BIL"
                                                                                                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]
                                                                    [(weight-equal
                                                                      [(group
                                                                        "VMS popped TECL or Not"
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLK"
                                                                              {:window
                                                                               126})
                                                                             (rsi
                                                                              "XLP"
                                                                              {:window
                                                                               126}))
                                                                            [(weight-equal
                                                                              [(group
                                                                                "Bullish Market Conditions"
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (>
                                                                                     (rsi
                                                                                      "TQQQ"
                                                                                      {:window
                                                                                       10})
                                                                                     80)
                                                                                    [(weight-equal
                                                                                      [(asset
                                                                                        "SOXS"
                                                                                        "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (<
                                                                                         (rsi
                                                                                          "TQQQ"
                                                                                          {:window
                                                                                           10})
                                                                                         31)
                                                                                        [(weight-equal
                                                                                          [(filter
                                                                                            (moving-average-return
                                                                                             {:window
                                                                                              5})
                                                                                            (select-bottom
                                                                                             1)
                                                                                            [(asset
                                                                                              "TECL"
                                                                                              "Direxion Daily Technology Bull 3x Shares")
                                                                                             (asset
                                                                                              "SOXL"
                                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                             (asset
                                                                                              "TMF"
                                                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (>
                                                                                             (rsi
                                                                                              "VIXY"
                                                                                              {:window
                                                                                               10})
                                                                                             50)
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (<
                                                                                                 (moving-average-return
                                                                                                  "VIXY"
                                                                                                  {:window
                                                                                                   5})
                                                                                                 0)
                                                                                                [(group
                                                                                                  "1st Block"
                                                                                                  [(weight-equal
                                                                                                    [(if
                                                                                                      (>
                                                                                                       (cumulative-return
                                                                                                        "TQQQ"
                                                                                                        {:window
                                                                                                         1})
                                                                                                       5.5)
                                                                                                      [(weight-equal
                                                                                                        [(asset
                                                                                                          "SOXS"
                                                                                                          "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                      [(weight-equal
                                                                                                        [(group
                                                                                                          "TECL or Not"
                                                                                                          [(weight-equal
                                                                                                            [(if
                                                                                                              (>
                                                                                                               (rsi
                                                                                                                "TQQQ"
                                                                                                                {:window
                                                                                                                 10})
                                                                                                               79)
                                                                                                              [(asset
                                                                                                                "SOXS"
                                                                                                                "Direxion Daily Semiconductor Bear 3x Shares")]
                                                                                                              [(weight-equal
                                                                                                                [(group
                                                                                                                  "Huge volatility"
                                                                                                                  [(weight-equal
                                                                                                                    [(if
                                                                                                                      (<
                                                                                                                       (cumulative-return
                                                                                                                        "TQQQ"
                                                                                                                        {:window
                                                                                                                         6})
                                                                                                                       -13)
                                                                                                                      [(weight-equal
                                                                                                                        [(if
                                                                                                                          (>
                                                                                                                           (cumulative-return
                                                                                                                            "TQQQ"
                                                                                                                            {:window
                                                                                                                             1})
                                                                                                                           6)
                                                                                                                          [(weight-equal
                                                                                                                            [(asset
                                                                                                                              "SOXS"
                                                                                                                              "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                                          [(weight-equal
                                                                                                                            [(group
                                                                                                                              "Mean Rev"
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (<
                                                                                                                                   (rsi
                                                                                                                                    "TQQQ"
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   32)
                                                                                                                                  [(asset
                                                                                                                                    "TECL"
                                                                                                                                    "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (<
                                                                                                                                       (max-drawdown
                                                                                                                                        "TMF"
                                                                                                                                        {:window
                                                                                                                                         10})
                                                                                                                                       7)
                                                                                                                                      [(asset
                                                                                                                                        "TECL"
                                                                                                                                        "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(asset
                                                                                                                                          "BIL"
                                                                                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                                                                                                                      [(weight-equal
                                                                                                                        [(group
                                                                                                                          "Normal market"
                                                                                                                          [(weight-equal
                                                                                                                            [(if
                                                                                                                              (>
                                                                                                                               (max-drawdown
                                                                                                                                "QQQ"
                                                                                                                                {:window
                                                                                                                                 10})
                                                                                                                               6)
                                                                                                                              [(weight-equal
                                                                                                                                [(asset
                                                                                                                                  "BIL"
                                                                                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (>
                                                                                                                                   (max-drawdown
                                                                                                                                    "TMF"
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   7)
                                                                                                                                  [(weight-equal
                                                                                                                                    [(asset
                                                                                                                                      "BIL"
                                                                                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
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
                                                                                                                                        [(asset
                                                                                                                                          "TECL"
                                                                                                                                          "Direxion Daily Technology Bull 3x Shares")])]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(if
                                                                                                                                          (>
                                                                                                                                           (rsi
                                                                                                                                            "SPY"
                                                                                                                                            {:window
                                                                                                                                             60})
                                                                                                                                           50)
                                                                                                                                          [(group
                                                                                                                                            "Bond > Stock"
                                                                                                                                            [(weight-equal
                                                                                                                                              [(if
                                                                                                                                                (>
                                                                                                                                                 (rsi
                                                                                                                                                  "BND"
                                                                                                                                                  {:window
                                                                                                                                                   45})
                                                                                                                                                 (rsi
                                                                                                                                                  "SPY"
                                                                                                                                                  {:window
                                                                                                                                                   45}))
                                                                                                                                                [(asset
                                                                                                                                                  "TECL"
                                                                                                                                                  "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(asset
                                                                                                                                                    "BIL"
                                                                                                                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                                                                                                                                          [(group
                                                                                                                                            "Bond Mid-term < Long-term"
                                                                                                                                            [(weight-equal
                                                                                                                                              [(if
                                                                                                                                                (<
                                                                                                                                                 (rsi
                                                                                                                                                  "IEF"
                                                                                                                                                  {:window
                                                                                                                                                   200})
                                                                                                                                                 (rsi
                                                                                                                                                  "TLT"
                                                                                                                                                  {:window
                                                                                                                                                   200}))
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(if
                                                                                                                                                    (>
                                                                                                                                                     (rsi
                                                                                                                                                      "BND"
                                                                                                                                                      {:window
                                                                                                                                                       45})
                                                                                                                                                     (rsi
                                                                                                                                                      "SPY"
                                                                                                                                                      {:window
                                                                                                                                                       45}))
                                                                                                                                                    [(asset
                                                                                                                                                      "TECL"
                                                                                                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(asset
                                                                                                                                                        "BIL"
                                                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(asset
                                                                                                                                                    "BIL"
                                                                                                                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])]
                                                                                                [(group
                                                                                                  "2nd Block"
                                                                                                  [(weight-equal
                                                                                                    [(if
                                                                                                      (>
                                                                                                       (cumulative-return
                                                                                                        "TQQQ"
                                                                                                        {:window
                                                                                                         1})
                                                                                                       5.5)
                                                                                                      [(weight-equal
                                                                                                        [(filter
                                                                                                          (exponential-moving-average-price
                                                                                                           {:window
                                                                                                            5})
                                                                                                          (select-bottom
                                                                                                           1)
                                                                                                          [(asset
                                                                                                            "SOXS"
                                                                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                                           (asset
                                                                                                            "TECS"
                                                                                                            "Direxion Daily Technology Bear 3X Shares")])])]
                                                                                                      [(weight-equal
                                                                                                        [(group
                                                                                                          "TECL or Not"
                                                                                                          [(weight-equal
                                                                                                            [(if
                                                                                                              (>
                                                                                                               (rsi
                                                                                                                "TQQQ"
                                                                                                                {:window
                                                                                                                 10})
                                                                                                               79)
                                                                                                              [(asset
                                                                                                                "SOXS"
                                                                                                                "Direxion Daily Semiconductor Bear 3x Shares")]
                                                                                                              [(weight-equal
                                                                                                                [(group
                                                                                                                  "Huge volatility"
                                                                                                                  [(weight-equal
                                                                                                                    [(if
                                                                                                                      (<
                                                                                                                       (cumulative-return
                                                                                                                        "TQQQ"
                                                                                                                        {:window
                                                                                                                         6})
                                                                                                                       -13)
                                                                                                                      [(weight-equal
                                                                                                                        [(if
                                                                                                                          (>
                                                                                                                           (cumulative-return
                                                                                                                            "TQQQ"
                                                                                                                            {:window
                                                                                                                             1})
                                                                                                                           6)
                                                                                                                          [(weight-equal
                                                                                                                            [(asset
                                                                                                                              "SOXS"
                                                                                                                              "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                                          [(weight-equal
                                                                                                                            [(group
                                                                                                                              "Mean Rev"
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (<
                                                                                                                                   (rsi
                                                                                                                                    "TQQQ"
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   32)
                                                                                                                                  [(asset
                                                                                                                                    "TECL"
                                                                                                                                    "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (<
                                                                                                                                       (max-drawdown
                                                                                                                                        "TMF"
                                                                                                                                        {:window
                                                                                                                                         10})
                                                                                                                                       7)
                                                                                                                                      [(asset
                                                                                                                                        "TECL"
                                                                                                                                        "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(asset
                                                                                                                                          "BIL"
                                                                                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                                                                                                                      [(weight-equal
                                                                                                                        [(group
                                                                                                                          "Normal market"
                                                                                                                          [(weight-equal
                                                                                                                            [(if
                                                                                                                              (>
                                                                                                                               (max-drawdown
                                                                                                                                "QQQ"
                                                                                                                                {:window
                                                                                                                                 10})
                                                                                                                               6)
                                                                                                                              [(weight-equal
                                                                                                                                [(asset
                                                                                                                                  "BIL"
                                                                                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (>
                                                                                                                                   (max-drawdown
                                                                                                                                    "TMF"
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   7)
                                                                                                                                  [(weight-equal
                                                                                                                                    [(asset
                                                                                                                                      "BIL"
                                                                                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
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
                                                                                                                                        [(asset
                                                                                                                                          "TECL"
                                                                                                                                          "Direxion Daily Technology Bull 3x Shares")])]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(if
                                                                                                                                          (>
                                                                                                                                           (rsi
                                                                                                                                            "SPY"
                                                                                                                                            {:window
                                                                                                                                             60})
                                                                                                                                           50)
                                                                                                                                          [(group
                                                                                                                                            "Bond > Stock"
                                                                                                                                            [(weight-equal
                                                                                                                                              [(if
                                                                                                                                                (>
                                                                                                                                                 (rsi
                                                                                                                                                  "BND"
                                                                                                                                                  {:window
                                                                                                                                                   45})
                                                                                                                                                 (rsi
                                                                                                                                                  "SPY"
                                                                                                                                                  {:window
                                                                                                                                                   45}))
                                                                                                                                                [(asset
                                                                                                                                                  "TECL"
                                                                                                                                                  "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(asset
                                                                                                                                                    "BIL"
                                                                                                                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                                                                                                                                          [(group
                                                                                                                                            "Bond Mid-term < Long-term"
                                                                                                                                            [(weight-equal
                                                                                                                                              [(if
                                                                                                                                                (<
                                                                                                                                                 (rsi
                                                                                                                                                  "IEF"
                                                                                                                                                  {:window
                                                                                                                                                   200})
                                                                                                                                                 (rsi
                                                                                                                                                  "TLT"
                                                                                                                                                  {:window
                                                                                                                                                   200}))
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(if
                                                                                                                                                    (>
                                                                                                                                                     (rsi
                                                                                                                                                      "BND"
                                                                                                                                                      {:window
                                                                                                                                                       45})
                                                                                                                                                     (rsi
                                                                                                                                                      "SPY"
                                                                                                                                                      {:window
                                                                                                                                                       45}))
                                                                                                                                                    [(asset
                                                                                                                                                      "TECL"
                                                                                                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(asset
                                                                                                                                                        "BIL"
                                                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(asset
                                                                                                                                                    "BIL"
                                                                                                                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])]
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (<
                                                                                                 (moving-average-return
                                                                                                  "VIXY"
                                                                                                  {:window
                                                                                                   5})
                                                                                                 0)
                                                                                                [(group
                                                                                                  "3rd Block"
                                                                                                  [(weight-equal
                                                                                                    [(if
                                                                                                      (>
                                                                                                       (cumulative-return
                                                                                                        "TQQQ"
                                                                                                        {:window
                                                                                                         1})
                                                                                                       5.5)
                                                                                                      [(weight-equal
                                                                                                        [(filter
                                                                                                          (exponential-moving-average-price
                                                                                                           {:window
                                                                                                            5})
                                                                                                          (select-bottom
                                                                                                           1)
                                                                                                          [(asset
                                                                                                            "SOXS"
                                                                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                                           (asset
                                                                                                            "TECS"
                                                                                                            "Direxion Daily Technology Bear 3X Shares")])])]
                                                                                                      [(weight-equal
                                                                                                        [(group
                                                                                                          "TECL or Not"
                                                                                                          [(weight-equal
                                                                                                            [(if
                                                                                                              (>
                                                                                                               (rsi
                                                                                                                "TQQQ"
                                                                                                                {:window
                                                                                                                 10})
                                                                                                               79)
                                                                                                              [(asset
                                                                                                                "SOXS"
                                                                                                                "Direxion Daily Semiconductor Bear 3x Shares")]
                                                                                                              [(weight-equal
                                                                                                                [(group
                                                                                                                  "Huge volatility"
                                                                                                                  [(weight-equal
                                                                                                                    [(if
                                                                                                                      (<
                                                                                                                       (cumulative-return
                                                                                                                        "TQQQ"
                                                                                                                        {:window
                                                                                                                         6})
                                                                                                                       -13)
                                                                                                                      [(weight-equal
                                                                                                                        [(if
                                                                                                                          (>
                                                                                                                           (cumulative-return
                                                                                                                            "TQQQ"
                                                                                                                            {:window
                                                                                                                             1})
                                                                                                                           6)
                                                                                                                          [(weight-equal
                                                                                                                            [(asset
                                                                                                                              "SOXS"
                                                                                                                              "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                                          [(weight-equal
                                                                                                                            [(group
                                                                                                                              "Mean Rev"
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (<
                                                                                                                                   (rsi
                                                                                                                                    "TQQQ"
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   32)
                                                                                                                                  [(asset
                                                                                                                                    "TECL"
                                                                                                                                    "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (<
                                                                                                                                       (max-drawdown
                                                                                                                                        "TMF"
                                                                                                                                        {:window
                                                                                                                                         10})
                                                                                                                                       7)
                                                                                                                                      [(asset
                                                                                                                                        "TECL"
                                                                                                                                        "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(asset
                                                                                                                                          "BIL"
                                                                                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                                                                                                                      [(weight-equal
                                                                                                                        [(group
                                                                                                                          "Normal market"
                                                                                                                          [(weight-equal
                                                                                                                            [(if
                                                                                                                              (>
                                                                                                                               (max-drawdown
                                                                                                                                "QQQ"
                                                                                                                                {:window
                                                                                                                                 10})
                                                                                                                               6)
                                                                                                                              [(weight-equal
                                                                                                                                [(asset
                                                                                                                                  "BIL"
                                                                                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (>
                                                                                                                                   (max-drawdown
                                                                                                                                    "TMF"
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   7)
                                                                                                                                  [(weight-equal
                                                                                                                                    [(asset
                                                                                                                                      "BIL"
                                                                                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
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
                                                                                                                                        [(asset
                                                                                                                                          "TECL"
                                                                                                                                          "Direxion Daily Technology Bull 3x Shares")])]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(if
                                                                                                                                          (>
                                                                                                                                           (rsi
                                                                                                                                            "SPY"
                                                                                                                                            {:window
                                                                                                                                             60})
                                                                                                                                           50)
                                                                                                                                          [(group
                                                                                                                                            "Bond > Stock"
                                                                                                                                            [(weight-equal
                                                                                                                                              [(if
                                                                                                                                                (>
                                                                                                                                                 (rsi
                                                                                                                                                  "BND"
                                                                                                                                                  {:window
                                                                                                                                                   45})
                                                                                                                                                 (rsi
                                                                                                                                                  "SPY"
                                                                                                                                                  {:window
                                                                                                                                                   45}))
                                                                                                                                                [(asset
                                                                                                                                                  "TECL"
                                                                                                                                                  "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(asset
                                                                                                                                                    "BIL"
                                                                                                                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                                                                                                                                          [(group
                                                                                                                                            "Bond Mid-term < Long-term"
                                                                                                                                            [(weight-equal
                                                                                                                                              [(if
                                                                                                                                                (<
                                                                                                                                                 (rsi
                                                                                                                                                  "IEF"
                                                                                                                                                  {:window
                                                                                                                                                   200})
                                                                                                                                                 (rsi
                                                                                                                                                  "TLT"
                                                                                                                                                  {:window
                                                                                                                                                   200}))
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(if
                                                                                                                                                    (>
                                                                                                                                                     (rsi
                                                                                                                                                      "BND"
                                                                                                                                                      {:window
                                                                                                                                                       45})
                                                                                                                                                     (rsi
                                                                                                                                                      "SPY"
                                                                                                                                                      {:window
                                                                                                                                                       45}))
                                                                                                                                                    [(asset
                                                                                                                                                      "TECL"
                                                                                                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(asset
                                                                                                                                                        "BIL"
                                                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(asset
                                                                                                                                                    "BIL"
                                                                                                                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])]
                                                                                                [(group
                                                                                                  "4th Block"
                                                                                                  [(weight-equal
                                                                                                    [(if
                                                                                                      (>
                                                                                                       (cumulative-return
                                                                                                        "TQQQ"
                                                                                                        {:window
                                                                                                         1})
                                                                                                       5.5)
                                                                                                      [(weight-equal
                                                                                                        [(filter
                                                                                                          (exponential-moving-average-price
                                                                                                           {:window
                                                                                                            5})
                                                                                                          (select-top
                                                                                                           1)
                                                                                                          [(asset
                                                                                                            "SOXS"
                                                                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                                           (asset
                                                                                                            "TECS"
                                                                                                            "Direxion Daily Technology Bear 3X Shares")])])]
                                                                                                      [(weight-equal
                                                                                                        [(group
                                                                                                          "TECL or Not"
                                                                                                          [(weight-equal
                                                                                                            [(if
                                                                                                              (>
                                                                                                               (rsi
                                                                                                                "TQQQ"
                                                                                                                {:window
                                                                                                                 10})
                                                                                                               79)
                                                                                                              [(asset
                                                                                                                "SOXS"
                                                                                                                "Direxion Daily Semiconductor Bear 3x Shares")]
                                                                                                              [(weight-equal
                                                                                                                [(group
                                                                                                                  "Huge volatility"
                                                                                                                  [(weight-equal
                                                                                                                    [(if
                                                                                                                      (<
                                                                                                                       (cumulative-return
                                                                                                                        "TQQQ"
                                                                                                                        {:window
                                                                                                                         6})
                                                                                                                       -13)
                                                                                                                      [(weight-equal
                                                                                                                        [(if
                                                                                                                          (>
                                                                                                                           (cumulative-return
                                                                                                                            "TQQQ"
                                                                                                                            {:window
                                                                                                                             1})
                                                                                                                           6)
                                                                                                                          [(weight-equal
                                                                                                                            [(asset
                                                                                                                              "SOXS"
                                                                                                                              "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                                          [(weight-equal
                                                                                                                            [(group
                                                                                                                              "Mean Rev"
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (<
                                                                                                                                   (rsi
                                                                                                                                    "TQQQ"
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   32)
                                                                                                                                  [(asset
                                                                                                                                    "TECL"
                                                                                                                                    "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (<
                                                                                                                                       (max-drawdown
                                                                                                                                        "TMF"
                                                                                                                                        {:window
                                                                                                                                         10})
                                                                                                                                       7)
                                                                                                                                      [(asset
                                                                                                                                        "TECL"
                                                                                                                                        "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(asset
                                                                                                                                          "BIL"
                                                                                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                                                                                                                      [(weight-equal
                                                                                                                        [(group
                                                                                                                          "Normal market"
                                                                                                                          [(weight-equal
                                                                                                                            [(if
                                                                                                                              (>
                                                                                                                               (max-drawdown
                                                                                                                                "QQQ"
                                                                                                                                {:window
                                                                                                                                 10})
                                                                                                                               6)
                                                                                                                              [(weight-equal
                                                                                                                                [(asset
                                                                                                                                  "BIL"
                                                                                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (>
                                                                                                                                   (max-drawdown
                                                                                                                                    "TMF"
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   7)
                                                                                                                                  [(weight-equal
                                                                                                                                    [(asset
                                                                                                                                      "BIL"
                                                                                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
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
                                                                                                                                        [(asset
                                                                                                                                          "TECL"
                                                                                                                                          "Direxion Daily Technology Bull 3x Shares")])]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(if
                                                                                                                                          (>
                                                                                                                                           (rsi
                                                                                                                                            "SPY"
                                                                                                                                            {:window
                                                                                                                                             60})
                                                                                                                                           50)
                                                                                                                                          [(group
                                                                                                                                            "Bond > Stock"
                                                                                                                                            [(weight-equal
                                                                                                                                              [(if
                                                                                                                                                (>
                                                                                                                                                 (rsi
                                                                                                                                                  "BND"
                                                                                                                                                  {:window
                                                                                                                                                   45})
                                                                                                                                                 (rsi
                                                                                                                                                  "SPY"
                                                                                                                                                  {:window
                                                                                                                                                   45}))
                                                                                                                                                [(asset
                                                                                                                                                  "TECL"
                                                                                                                                                  "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(asset
                                                                                                                                                    "BIL"
                                                                                                                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                                                                                                                                          [(group
                                                                                                                                            "Bond Mid-term < Long-term"
                                                                                                                                            [(weight-equal
                                                                                                                                              [(if
                                                                                                                                                (<
                                                                                                                                                 (rsi
                                                                                                                                                  "IEF"
                                                                                                                                                  {:window
                                                                                                                                                   200})
                                                                                                                                                 (rsi
                                                                                                                                                  "TLT"
                                                                                                                                                  {:window
                                                                                                                                                   200}))
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(if
                                                                                                                                                    (>
                                                                                                                                                     (rsi
                                                                                                                                                      "BND"
                                                                                                                                                      {:window
                                                                                                                                                       45})
                                                                                                                                                     (rsi
                                                                                                                                                      "SPY"
                                                                                                                                                      {:window
                                                                                                                                                       45}))
                                                                                                                                                    [(asset
                                                                                                                                                      "TECL"
                                                                                                                                                      "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(asset
                                                                                                                                                        "BIL"
                                                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(asset
                                                                                                                                                    "BIL"
                                                                                                                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]
                                                                            [(weight-equal
                                                                              [(group
                                                                                "Danger Market Conditions"
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (>
                                                                                     (rsi
                                                                                      "TQQQ"
                                                                                      {:window
                                                                                       10})
                                                                                     80)
                                                                                    [(weight-equal
                                                                                      [(filter
                                                                                        (cumulative-return
                                                                                         {:window
                                                                                          5})
                                                                                        (select-bottom
                                                                                         1)
                                                                                        [(asset
                                                                                          "TMV"
                                                                                          "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                                         (asset
                                                                                          "BIL"
                                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (rsi
                                                                                          "VIXY"
                                                                                          {:window
                                                                                           10})
                                                                                         50)
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (<
                                                                                             (rsi
                                                                                              "TQQQ"
                                                                                              {:window
                                                                                               10})
                                                                                             31)
                                                                                            [(weight-equal
                                                                                              [(filter
                                                                                                (stdev-price
                                                                                                 {:window
                                                                                                  5})
                                                                                                (select-bottom
                                                                                                 1)
                                                                                                [(asset
                                                                                                  "SOXL"
                                                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                                 (asset
                                                                                                  "ERX"
                                                                                                  "Direxion Daily Energy Bull 2x Shares")
                                                                                                 (asset
                                                                                                  "TMV"
                                                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])]
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (<
                                                                                                 (moving-average-return
                                                                                                  "VIXY"
                                                                                                  {:window
                                                                                                   5})
                                                                                                 0)
                                                                                                [(weight-equal
                                                                                                  [(asset
                                                                                                    "SOXL"
                                                                                                    "Direxion Daily Semiconductor Bull 3x Shares")])]
                                                                                                [(weight-equal
                                                                                                  [(group
                                                                                                    "TECL or Not"
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (>
                                                                                                         (rsi
                                                                                                          "TQQQ"
                                                                                                          {:window
                                                                                                           10})
                                                                                                         79)
                                                                                                        [(asset
                                                                                                          "SOXS"
                                                                                                          "Direxion Daily Semiconductor Bear 3x Shares")]
                                                                                                        [(weight-equal
                                                                                                          [(group
                                                                                                            "Huge volatility"
                                                                                                            [(weight-equal
                                                                                                              [(if
                                                                                                                (<
                                                                                                                 (cumulative-return
                                                                                                                  "TQQQ"
                                                                                                                  {:window
                                                                                                                   6})
                                                                                                                 -13)
                                                                                                                [(weight-equal
                                                                                                                  [(if
                                                                                                                    (>
                                                                                                                     (cumulative-return
                                                                                                                      "TQQQ"
                                                                                                                      {:window
                                                                                                                       1})
                                                                                                                     6)
                                                                                                                    [(weight-equal
                                                                                                                      [(asset
                                                                                                                        "SOXS"
                                                                                                                        "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                                    [(weight-equal
                                                                                                                      [(group
                                                                                                                        "Mean Rev"
                                                                                                                        [(weight-equal
                                                                                                                          [(if
                                                                                                                            (<
                                                                                                                             (rsi
                                                                                                                              "TQQQ"
                                                                                                                              {:window
                                                                                                                               10})
                                                                                                                             32)
                                                                                                                            [(asset
                                                                                                                              "TECL"
                                                                                                                              "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                            [(weight-equal
                                                                                                                              [(if
                                                                                                                                (<
                                                                                                                                 (max-drawdown
                                                                                                                                  "TMF"
                                                                                                                                  {:window
                                                                                                                                   10})
                                                                                                                                 7)
                                                                                                                                [(asset
                                                                                                                                  "TECL"
                                                                                                                                  "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                [(weight-equal
                                                                                                                                  [(asset
                                                                                                                                    "BIL"
                                                                                                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                                                                                                                [(weight-equal
                                                                                                                  [(group
                                                                                                                    "Normal market"
                                                                                                                    [(weight-equal
                                                                                                                      [(if
                                                                                                                        (>
                                                                                                                         (max-drawdown
                                                                                                                          "QQQ"
                                                                                                                          {:window
                                                                                                                           10})
                                                                                                                         6)
                                                                                                                        [(weight-equal
                                                                                                                          [(asset
                                                                                                                            "BIL"
                                                                                                                            "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                                                                                                                        [(weight-equal
                                                                                                                          [(if
                                                                                                                            (>
                                                                                                                             (max-drawdown
                                                                                                                              "TMF"
                                                                                                                              {:window
                                                                                                                               10})
                                                                                                                             7)
                                                                                                                            [(weight-equal
                                                                                                                              [(asset
                                                                                                                                "BIL"
                                                                                                                                "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
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
                                                                                                                                  [(asset
                                                                                                                                    "TECL"
                                                                                                                                    "Direxion Daily Technology Bull 3x Shares")])]
                                                                                                                                [(weight-equal
                                                                                                                                  [(if
                                                                                                                                    (>
                                                                                                                                     (rsi
                                                                                                                                      "SPY"
                                                                                                                                      {:window
                                                                                                                                       60})
                                                                                                                                     50)
                                                                                                                                    [(group
                                                                                                                                      "Bond > Stock"
                                                                                                                                      [(weight-equal
                                                                                                                                        [(if
                                                                                                                                          (>
                                                                                                                                           (rsi
                                                                                                                                            "BND"
                                                                                                                                            {:window
                                                                                                                                             45})
                                                                                                                                           (rsi
                                                                                                                                            "SPY"
                                                                                                                                            {:window
                                                                                                                                             45}))
                                                                                                                                          [(asset
                                                                                                                                            "TECL"
                                                                                                                                            "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                          [(weight-equal
                                                                                                                                            [(asset
                                                                                                                                              "BIL"
                                                                                                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                                                                                                                                    [(group
                                                                                                                                      "Bond Mid-term < Long-term"
                                                                                                                                      [(weight-equal
                                                                                                                                        [(if
                                                                                                                                          (<
                                                                                                                                           (rsi
                                                                                                                                            "IEF"
                                                                                                                                            {:window
                                                                                                                                             200})
                                                                                                                                           (rsi
                                                                                                                                            "TLT"
                                                                                                                                            {:window
                                                                                                                                             200}))
                                                                                                                                          [(weight-equal
                                                                                                                                            [(if
                                                                                                                                              (>
                                                                                                                                               (rsi
                                                                                                                                                "BND"
                                                                                                                                                {:window
                                                                                                                                                 45})
                                                                                                                                               (rsi
                                                                                                                                                "SPY"
                                                                                                                                                {:window
                                                                                                                                                 45}))
                                                                                                                                              [(asset
                                                                                                                                                "TECL"
                                                                                                                                                "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                              [(weight-equal
                                                                                                                                                [(asset
                                                                                                                                                  "BIL"
                                                                                                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                                                                                                                          [(weight-equal
                                                                                                                                            [(asset
                                                                                                                                              "BIL"
                                                                                                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])]
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (<
                                                                                             (rsi
                                                                                              "TQQQ"
                                                                                              {:window
                                                                                               10})
                                                                                             31)
                                                                                            [(weight-equal
                                                                                              [(asset
                                                                                                "SOXL"
                                                                                                "Direxion Daily Semiconductor Bull 3x Shares")])]
                                                                                            [(weight-equal
                                                                                              [(group
                                                                                                "TECL or Not"
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (>
                                                                                                     (rsi
                                                                                                      "TQQQ"
                                                                                                      {:window
                                                                                                       10})
                                                                                                     79)
                                                                                                    [(asset
                                                                                                      "SOXS"
                                                                                                      "Direxion Daily Semiconductor Bear 3x Shares")]
                                                                                                    [(weight-equal
                                                                                                      [(group
                                                                                                        "Huge volatility"
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (<
                                                                                                             (cumulative-return
                                                                                                              "TQQQ"
                                                                                                              {:window
                                                                                                               6})
                                                                                                             -13)
                                                                                                            [(weight-equal
                                                                                                              [(if
                                                                                                                (>
                                                                                                                 (cumulative-return
                                                                                                                  "TQQQ"
                                                                                                                  {:window
                                                                                                                   1})
                                                                                                                 6)
                                                                                                                [(weight-equal
                                                                                                                  [(asset
                                                                                                                    "SOXS"
                                                                                                                    "Direxion Daily Semiconductor Bear 3x Shares")])]
                                                                                                                [(weight-equal
                                                                                                                  [(group
                                                                                                                    "Mean Rev"
                                                                                                                    [(weight-equal
                                                                                                                      [(if
                                                                                                                        (<
                                                                                                                         (rsi
                                                                                                                          "TQQQ"
                                                                                                                          {:window
                                                                                                                           10})
                                                                                                                         32)
                                                                                                                        [(asset
                                                                                                                          "TECL"
                                                                                                                          "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                        [(weight-equal
                                                                                                                          [(if
                                                                                                                            (<
                                                                                                                             (max-drawdown
                                                                                                                              "TMF"
                                                                                                                              {:window
                                                                                                                               10})
                                                                                                                             7)
                                                                                                                            [(asset
                                                                                                                              "TECL"
                                                                                                                              "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                            [(weight-equal
                                                                                                                              [(asset
                                                                                                                                "BIL"
                                                                                                                                "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])]
                                                                                                            [(weight-equal
                                                                                                              [(group
                                                                                                                "Normal market"
                                                                                                                [(weight-equal
                                                                                                                  [(if
                                                                                                                    (>
                                                                                                                     (max-drawdown
                                                                                                                      "QQQ"
                                                                                                                      {:window
                                                                                                                       10})
                                                                                                                     6)
                                                                                                                    [(weight-equal
                                                                                                                      [(asset
                                                                                                                        "BIL"
                                                                                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                                                                                                                    [(weight-equal
                                                                                                                      [(if
                                                                                                                        (>
                                                                                                                         (max-drawdown
                                                                                                                          "TMF"
                                                                                                                          {:window
                                                                                                                           10})
                                                                                                                         7)
                                                                                                                        [(weight-equal
                                                                                                                          [(asset
                                                                                                                            "BIL"
                                                                                                                            "SPDR Bloomberg 1-3 Month T-Bill ETF")])]
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
                                                                                                                              [(asset
                                                                                                                                "TECL"
                                                                                                                                "Direxion Daily Technology Bull 3x Shares")])]
                                                                                                                            [(weight-equal
                                                                                                                              [(if
                                                                                                                                (>
                                                                                                                                 (rsi
                                                                                                                                  "SPY"
                                                                                                                                  {:window
                                                                                                                                   60})
                                                                                                                                 50)
                                                                                                                                [(group
                                                                                                                                  "Bond > Stock"
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (>
                                                                                                                                       (rsi
                                                                                                                                        "BND"
                                                                                                                                        {:window
                                                                                                                                         45})
                                                                                                                                       (rsi
                                                                                                                                        "SPY"
                                                                                                                                        {:window
                                                                                                                                         45}))
                                                                                                                                      [(asset
                                                                                                                                        "TECL"
                                                                                                                                        "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(asset
                                                                                                                                          "BIL"
                                                                                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                                                                                                                                [(group
                                                                                                                                  "Bond Mid-term < Long-term"
                                                                                                                                  [(weight-equal
                                                                                                                                    [(if
                                                                                                                                      (<
                                                                                                                                       (rsi
                                                                                                                                        "IEF"
                                                                                                                                        {:window
                                                                                                                                         200})
                                                                                                                                       (rsi
                                                                                                                                        "TLT"
                                                                                                                                        {:window
                                                                                                                                         200}))
                                                                                                                                      [(weight-equal
                                                                                                                                        [(if
                                                                                                                                          (>
                                                                                                                                           (rsi
                                                                                                                                            "BND"
                                                                                                                                            {:window
                                                                                                                                             45})
                                                                                                                                           (rsi
                                                                                                                                            "SPY"
                                                                                                                                            {:window
                                                                                                                                             45}))
                                                                                                                                          [(asset
                                                                                                                                            "TECL"
                                                                                                                                            "Direxion Daily Technology Bull 3x Shares")]
                                                                                                                                          [(weight-equal
                                                                                                                                            [(asset
                                                                                                                                              "BIL"
                                                                                                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
                                                                                                                                      [(weight-equal
                                                                                                                                        [(asset
                                                                                                                                          "BIL"
                                                                                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]))
