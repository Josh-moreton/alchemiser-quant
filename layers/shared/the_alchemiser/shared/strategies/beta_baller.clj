(defsymphony
 "V3.0.2a | ☢️ Beta Baller + TCCC 💊 | Deez, BrianE, HinnomTX, DereckN, Garen, DJKeyhole 🧙‍♂️, comrade | AR: 10490.6%, DD 29.4% - BT date 1DEC19"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "V3.0.2a | ☢️ Beta Baller + TCCC 💊 | Deez, BrianE, HinnomTX, DereckN, Garen, DJKeyhole 🧙‍♂️ | AR: 10490.6%, DD 29.4% - BT date 1DEC19"
    [(weight-equal
      [(if
        (< (rsi "BIL" {:window 7}) (rsi "IEF" {:window 7}))
        [(weight-equal
          [(if
            (> (rsi "SPY" {:window 6}) 75)
            [(group
              "Overbought S&P. Sell the rip. Buy volatility."
              [(weight-equal
                [(filter
                  (rsi {:window 13})
                  (select-bottom 1)
                  [(asset
                    "UVXY"
                    "ProShares Ultra VIX Short-Term Futures ETF")
                   (asset
                    "VIXY"
                    "ProShares VIX Short-Term Futures ETF")])])])]
            [(asset
              "SOXL"
              "Direxion Daily Semiconductor Bull 3x Shares")])])]
        [(weight-equal
          [(if
            (< (rsi "SPY" {:window 6}) 27)
            [(group
              "Extremely oversold S&P (low RSI). Double check with bond mkt before going long"
              [(weight-equal
                [(if
                  (<
                   (rsi "SHY" {:window 10})
                   (rsi "HIBL" {:window 10}))
                  [(weight-equal
                    [(filter
                      (rsi {:window 5})
                      (select-bottom 1)
                      [(asset
                        "SOXS"
                        "Direxion Daily Semiconductor Bear 3x Shares")
                       (asset
                        "SPXS"
                        "Direxion Daily S&P 500 Bear 3x Shares")
                       (asset
                        "SQQQ"
                        "ProShares UltraPro Short QQQ")])])]
                  [(asset
                    "TECL"
                    "Direxion Daily Technology Bull 3x Shares")])])])]
            [(group
              "V0.1 | TCCC Stop the Bleed 💊 | DJKeyhole 🧙‍♂️ | 1/2 of Momentum Mean Reversion"
              [(weight-equal
                [(if
                  (< (rsi "SPY" {:window 10}) 30)
                  [(asset
                    "SOXL"
                    "Direxion Daily Semiconductor Bull 3x Shares")]
                  [(weight-equal
                    [(if
                      (> (rsi "UVXY" {:window 10}) 74)
                      [(weight-equal
                        [(if
                          (> (rsi "UVXY" {:window 10}) 84)
                          [(asset
                            "SOXL"
                            "Direxion Daily Semiconductor Bull 3x Shares")]
                          [(asset
                            "UVXY"
                            "ProShares Ultra VIX Short-Term Futures ETF")])])]
                      [(group
                        "Bear Stock Market - High Inflation - [STRIPPED] V2.0.1 | A Better LETF Basket | DJKeyhole 🧙‍♂️ | No UGE"
                        [(weight-equal
                          [(if
                            (>
                             (current-price "TLT")
                             (moving-average-price
                              "TLT"
                              {:window 200}))
                            [(group
                              "A.B: Medium term TLT may be overbought*"
                              [(weight-equal
                                [(if
                                  (<
                                   (moving-average-return
                                    "TLT"
                                    {:window 20})
                                   0)
                                  [(group
                                    "A.B.B.A: Risk Off, Rising Rates (TMV)*"
                                    [(weight-equal
                                      [(if
                                        (<=
                                         (exponential-moving-average-price
                                          "SPY"
                                          {:window 210})
                                         (moving-average-price
                                          "SPY"
                                          {:window 360}))
                                        [(asset
                                          "SOXL"
                                          "Direxion Daily Semiconductor Bull 3x Shares")]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "TQQQ" {:window 11})
                                             77)
                                            [(asset
                                              "UVXY"
                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "BIL"
                                                  {:window 5})
                                                 (rsi
                                                  "IEF"
                                                  {:window 5}))
                                                [(asset
                                                  "SOXS"
                                                  "Direxion Daily Semiconductor Bear 3x Shares")]
                                                [(weight-equal
                                                  [(filter
                                                    (moving-average-return
                                                     {:window 5})
                                                    (select-bottom 1)
                                                    [(asset
                                                      "TECL"
                                                      "Direxion Daily Technology Bull 3x Shares")
                                                     (asset
                                                      "SOXL"
                                                      "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])]
                                  [(group
                                    "A.B.B.B: Risk Off, Falling Rates (TMF)*"
                                    [(weight-equal
                                      [(if
                                        (<=
                                         (exponential-moving-average-price
                                          "SPY"
                                          {:window 210})
                                         (moving-average-price
                                          "SPY"
                                          {:window 360}))
                                        [(weight-equal
                                          [(if
                                            (<
                                             (rsi "TQQQ" {:window 10})
                                             30)
                                            [(weight-equal
                                              [(filter
                                                (moving-average-return
                                                 {:window 5})
                                                (select-bottom 1)
                                                [(asset
                                                  "TECL"
                                                  "Direxion Daily Technology Bull 3x Shares")
                                                 (asset
                                                  "SOXL"
                                                  "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                            [(weight-equal
                                              [(if
                                                (<=
                                                 (cumulative-return
                                                  "SPY"
                                                  {:window 2})
                                                 -2)
                                                [(weight-equal
                                                  [(filter
                                                    (cumulative-return
                                                     {:window 5})
                                                    (select-top 1)
                                                    [(asset
                                                      "TECS"
                                                      "Direxion Daily Technology Bear 3X Shares")
                                                     (asset
                                                      "SOXS"
                                                      "Direxion Daily Semiconductor Bear 3x Shares")
                                                     (asset
                                                      "SQQQ"
                                                      "ProShares UltraPro Short QQQ")])])]
                                                [(weight-equal
                                                  [(if
                                                    (>=
                                                     (cumulative-return
                                                      "SPXU"
                                                      {:window 6})
                                                     (cumulative-return
                                                      "UPRO"
                                                      {:window 3}))
                                                    [(weight-equal
                                                      [(filter
                                                        (cumulative-return
                                                         {:window 5})
                                                        (select-top 1)
                                                        [(asset
                                                          "ERX"
                                                          "Direxion Daily Energy Bull 2x Shares")
                                                         (asset
                                                          "EUO"
                                                          "ProShares UltraShort Euro")
                                                         (asset
                                                          "YCS"
                                                          "ProShares UltraShort Yen")])])]
                                                    [(weight-equal
                                                      [(filter
                                                        (moving-average-return
                                                         {:window 5})
                                                        (select-bottom
                                                         1)
                                                        [(asset
                                                          "SOXL"
                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                         (asset
                                                          "EWZ"
                                                          "iShares MSCI Brazil ETF")
                                                         (asset
                                                          "MVV"
                                                          "ProShares Ultra MidCap400")
                                                         (asset
                                                          "USD"
                                                          "ProShares Ultra Semiconductors")])])])])])])])])]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (moving-average-return
                                              "SPY"
                                              {:window 210})
                                             (moving-average-return
                                              "DBC"
                                              {:window 360}))
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "TQQQ"
                                                  {:window 11})
                                                 77)
                                                [(asset
                                                  "UVXY"
                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                [(weight-equal
                                                  [(if
                                                    (<
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 6})
                                                     -10)
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (cumulative-return
                                                          "TQQQ"
                                                          {:window 1})
                                                         5.5)
                                                        [(weight-equal
                                                          [(asset
                                                            "UVXY"
                                                            "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "BIL"
                                                              {:window
                                                               7})
                                                             (rsi
                                                              "IEF"
                                                              {:window
                                                               7}))
                                                            [(asset
                                                              "SOXL"
                                                              "Direxion Daily Semiconductor Bull 3x Shares")]
                                                            [(weight-equal
                                                              [(filter
                                                                (cumulative-return
                                                                 {:window
                                                                  5})
                                                                (select-top
                                                                 1)
                                                                [(asset
                                                                  "EWZ"
                                                                  "iShares MSCI Brazil ETF")
                                                                 (asset
                                                                  "UUP"
                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                 (asset
                                                                  "UCO"
                                                                  "ProShares Ultra Bloomberg Crude Oil")])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "BIL"
                                                          {:window 7})
                                                         (rsi
                                                          "IEF"
                                                          {:window 7}))
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
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")
                                                             (asset
                                                              "SPXL"
                                                              "Direxion Daily S&P 500 Bull 3x Shares")
                                                             (asset
                                                              "QLD"
                                                              "ProShares Ultra QQQ")
                                                             (asset
                                                              "USD"
                                                              "ProShares Ultra Semiconductors")])])]
                                                        [(weight-equal
                                                          [(filter
                                                            (cumulative-return
                                                             {:window
                                                              5})
                                                            (select-top
                                                             1)
                                                            [(asset
                                                              "EWZ"
                                                              "iShares MSCI Brazil ETF")
                                                             (asset
                                                              "UUP"
                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                             (asset
                                                              "TMF"
                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])]
                                            [(group
                                              "Defense | Modified"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (stdev-return
                                                    "DBC"
                                                    {:window 20})
                                                   (stdev-return
                                                    "SPY"
                                                    {:window 20}))
                                                  [(weight-equal
                                                    [(filter
                                                      (rsi {:window 5})
                                                      (select-bottom 1)
                                                      [(asset
                                                        "SHY"
                                                        "iShares 1-3 Year Treasury Bond ETF")
                                                       (asset
                                                        "EWZ"
                                                        "iShares MSCI Brazil ETF")
                                                       (asset
                                                        "GLD"
                                                        "SPDR Gold Shares")
                                                       (asset
                                                        "SPXS"
                                                        "Direxion Daily S&P 500 Bear 3x Shares")
                                                       (asset
                                                        "TECS"
                                                        "Direxion Daily Technology Bear 3X Shares")
                                                       (asset
                                                        "SOXS"
                                                        "Direxion Daily Semiconductor Bear 3x Shares")
                                                       (asset
                                                        "UCO"
                                                        "ProShares Ultra Bloomberg Crude Oil")
                                                       (asset
                                                        "YCS"
                                                        "ProShares UltraShort Yen")])])]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (rsi
                                                        "BIL"
                                                        {:window 7})
                                                       (rsi
                                                        "IEF"
                                                        {:window 7}))
                                                      [(weight-equal
                                                        [(filter
                                                          (moving-average-return
                                                           {:window 5})
                                                          (select-bottom
                                                           1)
                                                          [(asset
                                                            "SOXL"
                                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                                           (asset
                                                            "USD"
                                                            "ProShares Ultra Semiconductors")
                                                           (asset
                                                            "TMF"
                                                            "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                                                      [(weight-equal
                                                        [(filter
                                                          (cumulative-return
                                                           {:window 5})
                                                          (select-top
                                                           1)
                                                          [(asset
                                                            "EWZ"
                                                            "iShares MSCI Brazil ETF")
                                                           (asset
                                                            "SPXS"
                                                            "Direxion Daily S&P 500 Bear 3x Shares")
                                                           (asset
                                                            "SOXS"
                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                           (asset
                                                            "UCO"
                                                            "ProShares Ultra Bloomberg Crude Oil")
                                                           (asset
                                                            "YCS"
                                                            "ProShares UltraShort Yen")])])])])])])])])])])])])])])])]
                            [(group
                              "B: If long term TLT is trending down, safety: Long Term, 2 Least Volatile*"
                              [(weight-equal
                                [(if
                                  (<
                                   (moving-average-return
                                    "TLT"
                                    {:window 20})
                                   0)
                                  [(group
                                    "B.A.A: Risk Off, Rising Rates (TMV)* - LETF Basket"
                                    [(weight-equal
                                      [(if
                                        (<=
                                         (exponential-moving-average-price
                                          "SPY"
                                          {:window 210})
                                         (moving-average-price
                                          "SPY"
                                          {:window 360}))
                                        [(weight-equal
                                          [(if
                                            (<
                                             (rsi "TQQQ" {:window 10})
                                             30)
                                            [(weight-equal
                                              [(filter
                                                (moving-average-return
                                                 {:window 5})
                                                (select-top 1)
                                                [(asset
                                                  "TQQQ"
                                                  "ProShares UltraPro QQQ")
                                                 (asset
                                                  "SOXL"
                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                 (asset
                                                  "UPRO"
                                                  "ProShares UltraPro S&P500")])])]
                                            [(weight-equal
                                              [(if
                                                (<=
                                                 (cumulative-return
                                                  "SPY"
                                                  {:window 2})
                                                 -2)
                                                [(weight-equal
                                                  [(filter
                                                    (cumulative-return
                                                     {:window 5})
                                                    (select-bottom 1)
                                                    [(asset
                                                      "SPXS"
                                                      "Direxion Daily S&P 500 Bear 3x Shares")
                                                     (asset
                                                      "TECS"
                                                      "Direxion Daily Technology Bear 3X Shares")
                                                     (asset
                                                      "SOXS"
                                                      "Direxion Daily Semiconductor Bear 3x Shares")
                                                     (asset
                                                      "SQQQ"
                                                      "ProShares UltraPro Short QQQ")
                                                     (asset
                                                      "ERX"
                                                      "Direxion Daily Energy Bull 2x Shares")])])]
                                                [(weight-equal
                                                  [(if
                                                    (>=
                                                     (cumulative-return
                                                      "SPXU"
                                                      {:window 6})
                                                     (cumulative-return
                                                      "UPRO"
                                                      {:window 3}))
                                                    [(weight-equal
                                                      [(filter
                                                        (cumulative-return
                                                         {:window 5})
                                                        (select-top 1)
                                                        [(asset
                                                          "SOXS"
                                                          "Direxion Daily Semiconductor Bear 3x Shares")
                                                         (asset
                                                          "SQQQ"
                                                          "ProShares UltraPro Short QQQ")
                                                         (asset
                                                          "EPI"
                                                          "WisdomTree India Earnings Fund")])])]
                                                    [(weight-equal
                                                      [(filter
                                                        (moving-average-return
                                                         {:window 5})
                                                        (select-bottom
                                                         1)
                                                        [(asset
                                                          "TECL"
                                                          "Direxion Daily Technology Bull 3x Shares")
                                                         (asset
                                                          "SOXL"
                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                         (asset
                                                          "TMV"
                                                          "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (moving-average-return
                                              "SPY"
                                              {:window 210})
                                             (moving-average-return
                                              "DBC"
                                              {:window 360}))
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "TQQQ"
                                                  {:window 11})
                                                 77)
                                                [(asset
                                                  "UVXY"
                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                [(weight-equal
                                                  [(if
                                                    (<
                                                     (cumulative-return
                                                      "TQQQ"
                                                      {:window 6})
                                                     -10)
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (cumulative-return
                                                          "TQQQ"
                                                          {:window 1})
                                                         5.5)
                                                        [(weight-equal
                                                          [(asset
                                                            "UVXY"
                                                            "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              5})
                                                            (select-bottom
                                                             1)
                                                            [(asset
                                                              "SOXL"
                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "BIL"
                                                          {:window 7})
                                                         (rsi
                                                          "IEF"
                                                          {:window 7}))
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              5})
                                                            (select-top
                                                             1)
                                                            [(asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")
                                                             (asset
                                                              "SOXL"
                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                             (asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                             (asset
                                                              "TECL"
                                                              "Direxion Daily Technology Bull 3x Shares")])])]
                                                        [(weight-specified
                                                          0.8
                                                          (filter
                                                           (moving-average-return
                                                            {:window
                                                             22})
                                                           (select-bottom
                                                            1)
                                                           [(asset
                                                             "SOXL"
                                                             "Direxion Daily Semiconductor Bull 3x Shares")
                                                            (asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])
                                                          0.2
                                                          (filter
                                                           (cumulative-return
                                                            {:window
                                                             150})
                                                           (select-top
                                                            5)
                                                           [(asset
                                                             "DBC"
                                                             "Invesco DB Commodity Index Tracking Fund")
                                                            (asset
                                                             "DBA"
                                                             "Invesco DB Agriculture Fund")
                                                            (asset
                                                             "SHY"
                                                             "iShares 1-3 Year Treasury Bond ETF")
                                                            (asset
                                                             "TLT"
                                                             "iShares 20+ Year Treasury Bond ETF")
                                                            (asset
                                                             "XLE"
                                                             "Energy Select Sector SPDR Fund")
                                                            (asset
                                                             "IEF"
                                                             "iShares 7-10 Year Treasury Bond ETF")
                                                            (asset
                                                             "TBF"
                                                             "Proshares Short 20+ Year Treasury")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")]))])])])])])])]
                                            [(group
                                              "Defense | Modified"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (stdev-return
                                                    "DBC"
                                                    {:window 20})
                                                   (stdev-return
                                                    "SPY"
                                                    {:window 20}))
                                                  [(weight-equal
                                                    [(if
                                                      (>=
                                                       (stdev-return
                                                        "DBC"
                                                        {:window 10})
                                                       3)
                                                      [(weight-equal
                                                        [(if
                                                          (<=
                                                           (stdev-return
                                                            "TMV"
                                                            {:window
                                                             5})
                                                           (stdev-return
                                                            "DBC"
                                                            {:window
                                                             5}))
                                                          [(asset
                                                            "TMV"
                                                            "Direxion Daily 20+ Year Treasury Bear 3x Shares")]
                                                          [(asset
                                                            "DBC"
                                                            "Invesco DB Commodity Index Tracking Fund")])])]
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (rsi
                                                            "BIL"
                                                            {:window
                                                             7})
                                                           (rsi
                                                            "IEF"
                                                            {:window
                                                             7}))
                                                          [(weight-equal
                                                            [(filter
                                                              (moving-average-return
                                                               {:window
                                                                5})
                                                              (select-top
                                                               1)
                                                              [(asset
                                                                "TMV"
                                                                "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                               (asset
                                                                "SOXS"
                                                                "Direxion Daily Semiconductor Bear 3x Shares")
                                                               (asset
                                                                "SPXU"
                                                                "ProShares UltraPro Short S&P500")])])]
                                                          [(weight-equal
                                                            [(filter
                                                              (cumulative-return
                                                               {:window
                                                                5})
                                                              (select-bottom
                                                               1)
                                                              [(asset
                                                                "EFA"
                                                                "iShares MSCI EAFE ETF")
                                                               (asset
                                                                "EEM"
                                                                "iShares MSCI Emerging Markets ETF")
                                                               (asset
                                                                "SPXS"
                                                                "Direxion Daily S&P 500 Bear 3x Shares")
                                                               (asset
                                                                "SOXS"
                                                                "Direxion Daily Semiconductor Bear 3x Shares")
                                                               (asset
                                                                "UCO"
                                                                "ProShares Ultra Bloomberg Crude Oil")
                                                               (asset
                                                                "TMV"
                                                                "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (rsi
                                                        "BIL"
                                                        {:window 7})
                                                       (rsi
                                                        "IEF"
                                                        {:window 7}))
                                                      [(weight-equal
                                                        [(filter
                                                          (moving-average-return
                                                           {:window 5})
                                                          (select-bottom
                                                           1)
                                                          [(asset
                                                            "EPI"
                                                            "WisdomTree India Earnings Fund")
                                                           (asset
                                                            "SOXL"
                                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                                           (asset
                                                            "UPRO"
                                                            "ProShares UltraPro S&P500")])])]
                                                      [(weight-equal
                                                        [(filter
                                                          (cumulative-return
                                                           {:window 5})
                                                          (select-top
                                                           1)
                                                          [(asset
                                                            "EWZ"
                                                            "iShares MSCI Brazil ETF")
                                                           (asset
                                                            "TECS"
                                                            "Direxion Daily Technology Bear 3X Shares")
                                                           (asset
                                                            "SOXS"
                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                           (asset
                                                            "EUO"
                                                            "ProShares UltraShort Euro")
                                                           (asset
                                                            "YCS"
                                                            "ProShares UltraShort Yen")
                                                           (asset
                                                            "TMV"
                                                            "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])])])]
                                  [(group
                                    "B.A.B: Risk Off, Falling Rates (TMF)* - LETF Basket"
                                    [(weight-equal
                                      [(if
                                        (<=
                                         (exponential-moving-average-price
                                          "SPY"
                                          {:window 210})
                                         (moving-average-price
                                          "SPY"
                                          {:window 360}))
                                        [(weight-equal
                                          [(if
                                            (<=
                                             (cumulative-return
                                              "SPY"
                                              {:window 2})
                                             -2)
                                            [(weight-equal
                                              [(filter
                                                (cumulative-return
                                                 {:window 5})
                                                (select-top 1)
                                                [(asset
                                                  "SPXS"
                                                  "Direxion Daily S&P 500 Bear 3x Shares")
                                                 (asset
                                                  "TECS"
                                                  "Direxion Daily Technology Bear 3X Shares")
                                                 (asset
                                                  "SOXS"
                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                 (asset
                                                  "SQQQ"
                                                  "ProShares UltraPro Short QQQ")])])]
                                            [(weight-equal
                                              [(if
                                                (>=
                                                 (cumulative-return
                                                  "SPXU"
                                                  {:window 6})
                                                 (cumulative-return
                                                  "UPRO"
                                                  {:window 3}))
                                                [(weight-equal
                                                  [(filter
                                                    (cumulative-return
                                                     {:window 5})
                                                    (select-bottom 1)
                                                    [(asset
                                                      "BIL"
                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                     (asset
                                                      "AGG"
                                                      "iShares Core U.S. Aggregate Bond ETF")
                                                     (asset
                                                      "TMF"
                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")])
                                                   (filter
                                                    (cumulative-return
                                                     {:window 150})
                                                    (select-top 5)
                                                    [(asset
                                                      "DBC"
                                                      "Invesco DB Commodity Index Tracking Fund")
                                                     (asset
                                                      "DBA"
                                                      "Invesco DB Agriculture Fund")
                                                     (asset
                                                      "SHY"
                                                      "iShares 1-3 Year Treasury Bond ETF")
                                                     (asset
                                                      "TLT"
                                                      "iShares 20+ Year Treasury Bond ETF")
                                                     (asset
                                                      "XLE"
                                                      "Energy Select Sector SPDR Fund")
                                                     (asset
                                                      "IEF"
                                                      "iShares 7-10 Year Treasury Bond ETF")
                                                     (asset
                                                      "TBF"
                                                      "Proshares Short 20+ Year Treasury")
                                                     (asset
                                                      "XLP"
                                                      "Consumer Staples Select Sector SPDR Fund")])])]
                                                [(weight-equal
                                                  [(filter
                                                    (moving-average-return
                                                     {:window 5})
                                                    (select-bottom 1)
                                                    [(asset
                                                      "TECL"
                                                      "Direxion Daily Technology Bull 3x Shares")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")
                                                     (asset
                                                      "SOXL"
                                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                                     (asset
                                                      "EWZ"
                                                      "iShares MSCI Brazil ETF")
                                                     (asset
                                                      "TMF"
                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (moving-average-return
                                              "SPY"
                                              {:window 210})
                                             (moving-average-return
                                              "DBC"
                                              {:window 360}))
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (exponential-moving-average-price
                                                  "SPY"
                                                  {:window 210})
                                                 (exponential-moving-average-price
                                                  "SPY"
                                                  {:window 360}))
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "TQQQ"
                                                      {:window 11})
                                                     77)
                                                    [(asset
                                                      "UVXY"
                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "TQQQ"
                                                          {:window 6})
                                                         -10)
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
                                                                "UVXY"
                                                                "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  7})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "TECL"
                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                 (asset
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")
                                                                 (asset
                                                                  "SPXL"
                                                                  "Direxion Daily S&P 500 Bull 3x Shares")
                                                                 (asset
                                                                  "EPI"
                                                                  "WisdomTree India Earnings Fund")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")
                                                                 (asset
                                                                  "QLD"
                                                                  "ProShares Ultra QQQ")
                                                                 (asset
                                                                  "EWZ"
                                                                  "iShares MSCI Brazil ETF")
                                                                 (asset
                                                                  "MVV"
                                                                  "ProShares Ultra MidCap400")
                                                                 (asset
                                                                  "PUI"
                                                                  "Invesco DWA Utilities Momentum ETF")
                                                                 (asset
                                                                  "USD"
                                                                  "ProShares Ultra Semiconductors")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])]
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "BIL"
                                                              {:window
                                                               7})
                                                             (rsi
                                                              "IEF"
                                                              {:window
                                                               7}))
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  7})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "TECL"
                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                 (asset
                                                                  "SPXL"
                                                                  "Direxion Daily S&P 500 Bull 3x Shares")
                                                                 (asset
                                                                  "EPI"
                                                                  "WisdomTree India Earnings Fund")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")
                                                                 (asset
                                                                  "MVV"
                                                                  "ProShares Ultra MidCap400")])])]
                                                            [(weight-equal
                                                              [(filter
                                                                (cumulative-return
                                                                 {:window
                                                                  5})
                                                                (select-top
                                                                 1)
                                                                [(asset
                                                                  "SOXS"
                                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])]
                                                [(weight-equal
                                                  [(filter
                                                    (rsi {:window 5})
                                                    (select-bottom 1)
                                                    [(asset
                                                      "SPXS"
                                                      "Direxion Daily S&P 500 Bear 3x Shares")
                                                     (asset
                                                      "SQQQ"
                                                      "ProShares UltraPro Short QQQ")
                                                     (asset
                                                      "TECS"
                                                      "Direxion Daily Technology Bear 3X Shares")
                                                     (asset
                                                      "SOXS"
                                                      "Direxion Daily Semiconductor Bear 3x Shares")])])])])]
                                            [(group
                                              "Defense | Modified"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (stdev-return
                                                    "DBC"
                                                    {:window 20})
                                                   (stdev-return
                                                    "SPY"
                                                    {:window 20}))
                                                  [(weight-equal
                                                    [(filter
                                                      (rsi {:window 5})
                                                      (select-bottom 1)
                                                      [(asset
                                                        "SPXS"
                                                        "Direxion Daily S&P 500 Bear 3x Shares")
                                                       (asset
                                                        "EPI"
                                                        "WisdomTree India Earnings Fund")
                                                       (asset
                                                        "TECS"
                                                        "Direxion Daily Technology Bear 3X Shares")
                                                       (asset
                                                        "SOXS"
                                                        "Direxion Daily Semiconductor Bear 3x Shares")
                                                       (asset
                                                        "SQQQ"
                                                        "ProShares UltraPro Short QQQ")])])]
                                                  [(weight-equal
                                                    [(filter
                                                      (moving-average-return
                                                       {:window 5})
                                                      (select-top 1)
                                                      [(asset
                                                        "TECL"
                                                        "Direxion Daily Technology Bull 3x Shares")
                                                       (asset
                                                        "TQQQ"
                                                        "ProShares UltraPro QQQ")
                                                       (asset
                                                        "SOXL"
                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                       (asset
                                                        "TMF"
                                                        "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])])])])])])])])])])])])])])])])])])])]))
