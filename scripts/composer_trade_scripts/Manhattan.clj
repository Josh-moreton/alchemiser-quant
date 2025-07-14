(defsymphony
 "E$[NO K-1 50/50] ☢️ Mod of V1.11 The Manhattan Project | 50% TQQQ Minimal | 50% Beta Baller + TCCC"
 {:asset-class "EQUITIES", :rebalance-threshold 0.09}
 (weight-equal
  [(group
    "[NO K-1] V 3.0.1 | ☢️ Beta Baller + TCCC 💊 | Deez, BrianE, HinnomTX, DereckN, Garen, DJKeyhole 🧙‍♂️ | AR: 9335.3%, DD 32.3% - BT date 1DEC19"
    [(weight-equal
      [(if
        (< (rsi "BIL" {:window 10}) (rsi "IEF" {:window 10}))
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
                    "VXX"
                    "iPath Series B S&P 500 VIX Short-Term Futures ETN")
                   (asset "SQQQ" "ProShares UltraPro Short QQQ")])])])]
            [(weight-equal
              [(asset
                "SOXL"
                "Direxion Daily Semiconductor Bull 3x Shares")])])])]
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
            [(group
              "V0.1 | TCCC Stop the Bleed 💊 | DJKeyhole 🧙‍♂️ | 1/2 of Momentum Mean Reversion"
              [(weight-equal
                [(if
                  (< (rsi "SPY" {:window 10}) 30)
                  [(group
                    "V1.2 | Five and Below | DJKeyhole | No Low Volume LETFs"
                    [(weight-equal
                      [(filter
                        (moving-average-return {:window 5})
                        (select-bottom 1)
                        [(asset
                          "TECL"
                          "Direxion Daily Technology Bull 3x Shares")
                         (asset "TQQQ" "ProShares UltraPro QQQ")
                         (asset
                          "SPXL"
                          "Direxion Daily S&P 500 Bull 3x Shares")
                         (asset
                          "SOXL"
                          "Direxion Daily Semiconductor Bull 3x Shares")
                         (asset "UPRO" "ProShares UltraPro S&P500")
                         (asset "QLD" "ProShares Ultra QQQ")])])])]
                  [(weight-equal
                    [(if
                      (> (rsi "UVXY" {:window 10}) 74)
                      [(weight-equal
                        [(if
                          (> (rsi "UVXY" {:window 10}) 84)
                          [(group
                            "V2.0 | A Better LETF Basket | DJKeyhole 🧙‍♂️ | Lean and Green 💸^"
                            [(weight-equal
                              [(if
                                (>
                                 (current-price "TLT")
                                 (moving-average-price
                                  "TLT"
                                  {:window 200}))
                                [(weight-equal
                                  [(group
                                    "A: If long term TLT is trending up^"
                                    [(weight-equal
                                      [(if
                                        (< (rsi "TLT" {:window 14}) 50)
                                        [(weight-equal
                                          [(group
                                            "A.A: If medium term TLT is not overbought^"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (current-price "TLT")
                                                 (moving-average-price
                                                  "TLT"
                                                  {:window 5}))
                                                [(weight-equal
                                                  [(group
                                                    "A.A.A: Short term TLT is trending up, buy 3x leveraged bull treasury bonds (TMF)*"
                                                    [(weight-equal
                                                      [(if
                                                        (<=
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
                                                            (<
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               10})
                                                             30)
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  5})
                                                                (select-top
                                                                 1)
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
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")
                                                                 (asset
                                                                  "SPXL"
                                                                  "Direxion Daily S&P 500 Bull 3x Shares")])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>=
                                                                 (cumulative-return
                                                                  "SPXU"
                                                                  {:window
                                                                   6})
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   3}))
                                                                [(weight-equal
                                                                  [(filter
                                                                    (cumulative-return
                                                                     {:window
                                                                      5})
                                                                    (select-top
                                                                     1)
                                                                    [(asset
                                                                      "TECS"
                                                                      "Direxion Daily Technology Bear 3X Shares")
                                                                     (asset
                                                                      "SOXS"
                                                                      "Direxion Daily Semiconductor Bear 3x Shares")
                                                                     (asset
                                                                      "SQQQ"
                                                                      "ProShares UltraPro Short QQQ")
                                                                     (asset
                                                                      "TMF"
                                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                     (asset
                                                                      "SHY"
                                                                      "iShares 1-3 Year Treasury Bond ETF")])])]
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
                                                                      "SOXL"
                                                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                                                     (asset
                                                                      "UPRO"
                                                                      "ProShares UltraPro S&P500")
                                                                     (asset
                                                                      "EWZ"
                                                                      "iShares MSCI Brazil ETF")
                                                                     (asset
                                                                      "TMF"
                                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])]
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "TQQQ"
                                                              {:window
                                                               6})
                                                             -10)
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
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  7})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])]
                                                [(weight-equal
                                                  [(group
                                                    "A.A.B: If short term TLT is trending down^"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "TLT"
                                                          {:window 14})
                                                         20)
                                                        [(weight-equal
                                                          [(group
                                                            "A.A.B.A: Medium term TLT is underbought, buy 3x leveraged bull treasury bonds (TMF) - Can't Test - Use SHY for Safety *"
                                                            [(weight-equal
                                                              [(asset
                                                                "SHY"
                                                                "iShares 1-3 Year Treasury Bond ETF")])])])]
                                                        [(weight-equal
                                                          [(group
                                                            "A.A.B.B: Leveraged Safety^"
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (moving-average-return
                                                                  "TLT"
                                                                  {:window
                                                                   20})
                                                                 0)
                                                                [(group
                                                                  "A.A.B.B.A: Risk Off, Rising Rates (TMV)*"
                                                                  [(weight-equal
                                                                    [(if
                                                                      (<=
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
                                                                          (>=
                                                                           (cumulative-return
                                                                            "SPXU"
                                                                            {:window
                                                                             6})
                                                                           (cumulative-return
                                                                            "UPRO"
                                                                            {:window
                                                                             3}))
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
                                                                                "ERX"
                                                                                "Direxion Daily Energy Bull 2x Shares")
                                                                               (asset
                                                                                "SHY"
                                                                                "iShares 1-3 Year Treasury Bond ETF")])])]
                                                                          [(weight-equal
                                                                            [(filter
                                                                              (moving-average-return
                                                                               {:window
                                                                                5})
                                                                              (select-bottom
                                                                               1)
                                                                              [(asset
                                                                                "TQQQ"
                                                                                "ProShares UltraPro QQQ")
                                                                               (asset
                                                                                "SOXL"
                                                                                "Direxion Daily Semiconductor Bull 3x Shares")
                                                                               (asset
                                                                                "CURE"
                                                                                "Direxion Daily Healthcare Bull 3x Shares")
                                                                               (asset
                                                                                "EWZ"
                                                                                "iShares MSCI Brazil ETF")
                                                                               (asset
                                                                                "SHY"
                                                                                "iShares 1-3 Year Treasury Bond ETF")])])])])]
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
                                                                              (>
                                                                               (rsi
                                                                                "TQQQ"
                                                                                {:window
                                                                                 11})
                                                                               77)
                                                                              [(asset
                                                                                "VXX"
                                                                                "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                                                                              [(weight-equal
                                                                                [(if
                                                                                  (<
                                                                                   (cumulative-return
                                                                                    "TQQQ"
                                                                                    {:window
                                                                                     6})
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
                                                                                          "VXX"
                                                                                          "iPath Series B S&P 500 VIX Short-Term Futures ETN")])]
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
                                                                                            "SOXL"
                                                                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                           (asset
                                                                                            "UPRO"
                                                                                            "ProShares UltraPro S&P500")
                                                                                           (asset
                                                                                            "TMV"
                                                                                            "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                                           (asset
                                                                                            "SHY"
                                                                                            "iShares 1-3 Year Treasury Bond ETF")])])])])]
                                                                                  [(weight-equal
                                                                                    [(filter
                                                                                      (moving-average-return
                                                                                       {:window
                                                                                        5})
                                                                                      (select-top
                                                                                       1)
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
                                                                                        "UPRO"
                                                                                        "ProShares UltraPro S&P500")
                                                                                       (asset
                                                                                        "TMV"
                                                                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                                       (asset
                                                                                        "SHY"
                                                                                        "iShares 1-3 Year Treasury Bond ETF")])])])])])])]
                                                                          [(group
                                                                            "Defense | Modified"
                                                                            [(weight-equal
                                                                              [(if
                                                                                (>
                                                                                 (stdev-return
                                                                                  "DBC"
                                                                                  {:window
                                                                                   20})
                                                                                 (stdev-return
                                                                                  "SPY"
                                                                                  {:window
                                                                                   20}))
                                                                                [(weight-equal
                                                                                  [(filter
                                                                                    (rsi
                                                                                     {:window
                                                                                      5})
                                                                                    (select-bottom
                                                                                     1)
                                                                                    [(asset
                                                                                      "EEM"
                                                                                      "iShares MSCI Emerging Markets ETF")
                                                                                     (asset
                                                                                      "TECS"
                                                                                      "Direxion Daily Technology Bear 3X Shares")
                                                                                     (asset
                                                                                      "SQQQ"
                                                                                      "ProShares UltraPro Short QQQ")
                                                                                     (asset
                                                                                      "TMV"
                                                                                      "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])]
                                                                                [(weight-equal
                                                                                  [(filter
                                                                                    (rsi
                                                                                     {:window
                                                                                      10})
                                                                                    (select-bottom
                                                                                     1)
                                                                                    [(asset
                                                                                      "EEM"
                                                                                      "iShares MSCI Emerging Markets ETF")
                                                                                     (asset
                                                                                      "TECS"
                                                                                      "Direxion Daily Technology Bear 3X Shares")
                                                                                     (asset
                                                                                      "SOXS"
                                                                                      "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                     (asset
                                                                                      "TMV"
                                                                                      "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])]
                                                                [(group
                                                                  "A.A.B.B.B: Risk Off, Falling Rates (TMF)^"
                                                                  [(weight-equal
                                                                    [(if
                                                                      (<=
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
                                                                          (>=
                                                                           (cumulative-return
                                                                            "SPXU"
                                                                            {:window
                                                                             6})
                                                                           (cumulative-return
                                                                            "UPRO"
                                                                            {:window
                                                                             3}))
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
                                                                                "TECL"
                                                                                "Direxion Daily Technology Bull 3x Shares")
                                                                               (asset
                                                                                "TMF"
                                                                                "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
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
                                                                                "SOXL"
                                                                                "Direxion Daily Semiconductor Bull 3x Shares")
                                                                               (asset
                                                                                "TMF"
                                                                                "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])]
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
                                                                              (>
                                                                               (rsi
                                                                                "TQQQ"
                                                                                {:window
                                                                                 11})
                                                                               77)
                                                                              [(asset
                                                                                "VXX"
                                                                                "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                                                                              [(weight-equal
                                                                                [(if
                                                                                  (<
                                                                                   (cumulative-return
                                                                                    "TQQQ"
                                                                                    {:window
                                                                                     6})
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
                                                                                          "VXX"
                                                                                          "iPath Series B S&P 500 VIX Short-Term Futures ETN")])]
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
                                                                                            "SOXL"
                                                                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                           (asset
                                                                                            "PUI"
                                                                                            "Invesco DWA Utilities Momentum ETF")])])]
                                                                                      [(weight-equal
                                                                                        [(filter
                                                                                          (cumulative-return
                                                                                           {:window
                                                                                            5})
                                                                                          (select-bottom
                                                                                           1)
                                                                                          [(asset
                                                                                            "SOXS"
                                                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                           (asset
                                                                                            "SQQQ"
                                                                                            "ProShares UltraPro Short QQQ")
                                                                                           (asset
                                                                                            "ERX"
                                                                                            "Direxion Daily Energy Bull 2x Shares")
                                                                                           (asset
                                                                                            "DIG"
                                                                                            "ProShares Ultra Oil & Gas")])])])])])])])])]
                                                                          [(weight-equal
                                                                            [(filter
                                                                              (moving-average-return
                                                                               {:window
                                                                                5})
                                                                              (select-top
                                                                               1)
                                                                              [(asset
                                                                                "EPI"
                                                                                "WisdomTree India Earnings Fund")
                                                                               (asset
                                                                                "UPRO"
                                                                                "ProShares UltraPro S&P500")
                                                                               (asset
                                                                                "SOXL"
                                                                                "Direxion Daily Semiconductor Bull 3x Shares")
                                                                               (asset
                                                                                "TQQQ"
                                                                                "ProShares UltraPro QQQ")])])])])])])])])])])])])])])])])])])])]
                                        [(weight-equal
                                          [(group
                                            "A.B: Medium term TLT may be overbought*"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "TLT"
                                                  {:window 14})
                                                 80)
                                                [(weight-equal
                                                  [(group
                                                    "A.B.A: Medium term TLT is overbought, buy 3x leveraged bear treasury bonds (TMV)*"
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
                                                                    "VXX"
                                                                    "iPath Series B S&P 500 VIX Short-Term Futures ETN")])]
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
                                                                      "SOXL"
                                                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                                                     (asset
                                                                      "UPRO"
                                                                      "ProShares UltraPro S&P500")])])])])]
                                                            [(weight-equal
                                                              [(filter
                                                                (rsi
                                                                 {:window
                                                                  5})
                                                                (select-top
                                                                 1)
                                                                [(asset
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ")
                                                                 (asset
                                                                  "TECS"
                                                                  "Direxion Daily Technology Bear 3X Shares")
                                                                 (asset
                                                                  "SOXS"
                                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              5})
                                                            (select-top
                                                             1)
                                                            [(asset
                                                              "EPI"
                                                              "WisdomTree India Earnings Fund")
                                                             (asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")
                                                             (asset
                                                              "SOXL"
                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                             (asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])]
                                                [(weight-equal
                                                  [(group
                                                    "A.B.B: Leveraged Safety*"
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
                                                                {:window
                                                                 210})
                                                               (moving-average-price
                                                                "SPY"
                                                                {:window
                                                                 360}))
                                                              [(weight-equal
                                                                [(if
                                                                  (<
                                                                   (rsi
                                                                    "TQQQ"
                                                                    {:window
                                                                     10})
                                                                   30)
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
                                                                        "SOXL"
                                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                                       (asset
                                                                        "UPRO"
                                                                        "ProShares UltraPro S&P500")])])]
                                                                  [(weight-equal
                                                                    [(if
                                                                      (>=
                                                                       (cumulative-return
                                                                        "SPXU"
                                                                        {:window
                                                                         6})
                                                                       (cumulative-return
                                                                        "UPRO"
                                                                        {:window
                                                                         3}))
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (cumulative-return
                                                                           {:window
                                                                            5})
                                                                          (select-top
                                                                           1)
                                                                          [(asset
                                                                            "SQQQ"
                                                                            "ProShares UltraPro Short QQQ")])])]
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
                                                                            "SOXL"
                                                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                                                           (asset
                                                                            "CURE"
                                                                            "Direxion Daily Healthcare Bull 3x Shares")])])])])])])]
                                                              [(weight-equal
                                                                [(if
                                                                  (>
                                                                   (rsi
                                                                    "TQQQ"
                                                                    {:window
                                                                     11})
                                                                   77)
                                                                  [(asset
                                                                    "VXX"
                                                                    "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
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
                                                                        "SOXL"
                                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                                       (asset
                                                                        "UPRO"
                                                                        "ProShares UltraPro S&P500")
                                                                       (asset
                                                                        "TMV"
                                                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])]
                                                        [(group
                                                          "A.B.B.B: Risk Off, Falling Rates (TMF)*"
                                                          [(weight-equal
                                                            [(if
                                                              (<=
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
                                                                  (<
                                                                   (rsi
                                                                    "TQQQ"
                                                                    {:window
                                                                     10})
                                                                   30)
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
                                                                        "SOXL"
                                                                        "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                                                  [(weight-equal
                                                                    [(if
                                                                      (<=
                                                                       (cumulative-return
                                                                        "SPY"
                                                                        {:window
                                                                         2})
                                                                       -2)
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (cumulative-return
                                                                           {:window
                                                                            5})
                                                                          (select-top
                                                                           1)
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
                                                                            {:window
                                                                             6})
                                                                           (cumulative-return
                                                                            "UPRO"
                                                                            {:window
                                                                             3}))
                                                                          [(weight-equal
                                                                            [(filter
                                                                              (cumulative-return
                                                                               {:window
                                                                                5})
                                                                              (select-top
                                                                               1)
                                                                              [(asset
                                                                                "ERX"
                                                                                "Direxion Daily Energy Bull 2x Shares")
                                                                               (asset
                                                                                "IYK"
                                                                                "iShares U.S. Consumer Staples ETF")])])]
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
                                                                                "EWZ"
                                                                                "iShares MSCI Brazil ETF")
                                                                               (asset
                                                                                "MVV"
                                                                                "ProShares Ultra MidCap400")
                                                                               (asset
                                                                                "USD"
                                                                                "ProShares Ultra Semiconductors")
                                                                               (asset
                                                                                "IYK"
                                                                                "iShares U.S. Consumer Staples ETF")])])])])])])])])]
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
                                                                      (>
                                                                       (rsi
                                                                        "TQQQ"
                                                                        {:window
                                                                         11})
                                                                       77)
                                                                      [(asset
                                                                        "VXX"
                                                                        "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                                                                      [(weight-equal
                                                                        [(if
                                                                          (<
                                                                           (cumulative-return
                                                                            "TQQQ"
                                                                            {:window
                                                                             6})
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
                                                                                  "VXX"
                                                                                  "iPath Series B S&P 500 VIX Short-Term Futures ETN")])]
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
                                                                                      (select-bottom
                                                                                       1)
                                                                                      [(asset
                                                                                        "SOXL"
                                                                                        "Direxion Daily Semiconductor Bull 3x Shares")])])]
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
                                                                                        "ERX"
                                                                                        "Direxion Daily Energy Bull 2x Shares")])])])])])])]
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
                                                                                    "ProShares Ultra Semiconductors")
                                                                                   (asset
                                                                                    "IYK"
                                                                                    "iShares U.S. Consumer Staples ETF")])])]
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
                                                                                    "IYK"
                                                                                    "iShares U.S. Consumer Staples ETF")])])])])])])])])]
                                                                  [(group
                                                                    "Defense | Modified"
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (stdev-return
                                                                          "DBC"
                                                                          {:window
                                                                           20})
                                                                         (stdev-return
                                                                          "SPY"
                                                                          {:window
                                                                           20}))
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (rsi
                                                                             {:window
                                                                              5})
                                                                            (select-bottom
                                                                             1)
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
                                                                              "Direxion Daily Semiconductor Bear 3x Shares")])])]
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
                                                                                 {:window
                                                                                  5})
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
                                                                                  "ERX"
                                                                                  "Direxion Daily Energy Bull 2x Shares")])])])])])])])])])])])])])])])])])])])])])])])])]
                                [(group
                                  "B: If long term TLT is trending down, safety: Long Term, 2 Least Volatile*"
                                  [(weight-equal
                                    [(group
                                      "B.A: Leveraged Safety*"
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
                                                     (rsi
                                                      "TQQQ"
                                                      {:window 10})
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
                                                             {:window
                                                              5})
                                                            (select-bottom
                                                             1)
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
                                                              {:window
                                                               6})
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               3}))
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
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ")
                                                                 (asset
                                                                  "EPI"
                                                                  "WisdomTree India Earnings Fund")])])]
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
                                                          "VXX"
                                                          "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "TQQQ"
                                                              {:window
                                                               6})
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
                                                                    "VXX"
                                                                    "iPath Series B S&P 500 VIX Short-Term Futures ETN")])]
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
                                                                [(weight-equal
                                                                  [(filter
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
                                                                      "ProShares UltraPro S&P500")])])])])])])])])]
                                                    [(group
                                                      "Defense | Modified"
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (stdev-return
                                                            "DBC"
                                                            {:window
                                                             20})
                                                           (stdev-return
                                                            "SPY"
                                                            {:window
                                                             20}))
                                                          [(weight-equal
                                                            [(if
                                                              (>=
                                                               (stdev-return
                                                                "DBC"
                                                                {:window
                                                                 10})
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
                                                                    "PDBC"
                                                                    "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")])])]
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
                                                                        "ERX"
                                                                        "Direxion Daily Energy Bull 2x Shares")
                                                                       (asset
                                                                        "TMV"
                                                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])]
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
                                                                   {:window
                                                                    5})
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
                                                             {:window
                                                              5})
                                                            (select-bottom
                                                             1)
                                                            [(asset
                                                              "BIL"
                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                             (asset
                                                              "AGG"
                                                              "iShares Core U.S. Aggregate Bond ETF")
                                                             (asset
                                                              "TMF"
                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
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
                                                          {:window
                                                           210})
                                                         (exponential-moving-average-price
                                                          "SPY"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               11})
                                                             77)
                                                            [(asset
                                                              "VXX"
                                                              "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (cumulative-return
                                                                  "TQQQ"
                                                                  {:window
                                                                   6})
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
                                                                        "VXX"
                                                                        "iPath Series B S&P 500 VIX Short-Term Futures ETN")])]
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
                                                            (rsi
                                                             {:window
                                                              5})
                                                            (select-bottom
                                                             1)
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
                                                            {:window
                                                             20})
                                                           (stdev-return
                                                            "SPY"
                                                            {:window
                                                             20}))
                                                          [(weight-equal
                                                            [(filter
                                                              (rsi
                                                               {:window
                                                                5})
                                                              (select-bottom
                                                               1)
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
                                                               {:window
                                                                5})
                                                              (select-top
                                                               1)
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
                                                                "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])])])])])])])])])])])]
                          [(asset
                            "VXX"
                            "iPath Series B S&P 500 VIX Short-Term Futures ETN")])])]
                      [(group
                        "V2.0 | A Better LETF Basket | DJKeyhole 🧙‍♂️ | Lean and Green 💸^"
                        [(weight-equal
                          [(if
                            (>
                             (current-price "TLT")
                             (moving-average-price
                              "TLT"
                              {:window 200}))
                            [(weight-equal
                              [(group
                                "A: If long term TLT is trending up^"
                                [(weight-equal
                                  [(if
                                    (< (rsi "TLT" {:window 14}) 50)
                                    [(weight-equal
                                      [(group
                                        "A.A: If medium term TLT is not overbought^"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (current-price "TLT")
                                             (moving-average-price
                                              "TLT"
                                              {:window 5}))
                                            [(weight-equal
                                              [(group
                                                "A.A.A: Short term TLT is trending up, buy 3x leveraged bull treasury bonds (TMF)*"
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
                                                         (rsi
                                                          "TQQQ"
                                                          {:window 10})
                                                         30)
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              5})
                                                            (select-top
                                                             1)
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
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")
                                                             (asset
                                                              "SPXL"
                                                              "Direxion Daily S&P 500 Bull 3x Shares")])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>=
                                                             (cumulative-return
                                                              "SPXU"
                                                              {:window
                                                               6})
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               3}))
                                                            [(weight-equal
                                                              [(filter
                                                                (cumulative-return
                                                                 {:window
                                                                  5})
                                                                (select-top
                                                                 1)
                                                                [(asset
                                                                  "TECS"
                                                                  "Direxion Daily Technology Bear 3X Shares")
                                                                 (asset
                                                                  "SOXS"
                                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                                 (asset
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                 (asset
                                                                  "SHY"
                                                                  "iShares 1-3 Year Treasury Bond ETF")])])]
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
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")
                                                                 (asset
                                                                  "EWZ"
                                                                  "iShares MSCI Brazil ETF")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (cumulative-return
                                                          "TQQQ"
                                                          {:window 6})
                                                         -10)
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
                                                              "TMF"
                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              7})
                                                            (select-bottom
                                                             1)
                                                            [(asset
                                                              "SOXL"
                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                             (asset
                                                              "TMF"
                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "A.A.B: If short term TLT is trending down^"
                                                [(weight-equal
                                                  [(if
                                                    (<
                                                     (rsi
                                                      "TLT"
                                                      {:window 14})
                                                     20)
                                                    [(weight-equal
                                                      [(group
                                                        "A.A.B.A: Medium term TLT is underbought, buy 3x leveraged bull treasury bonds (TMF) - Can't Test - Use SHY for Safety *"
                                                        [(weight-equal
                                                          [(asset
                                                            "SHY"
                                                            "iShares 1-3 Year Treasury Bond ETF")])])])]
                                                    [(weight-equal
                                                      [(group
                                                        "A.A.B.B: Leveraged Safety^"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (moving-average-return
                                                              "TLT"
                                                              {:window
                                                               20})
                                                             0)
                                                            [(group
                                                              "A.A.B.B.A: Risk Off, Rising Rates (TMV)*"
                                                              [(weight-equal
                                                                [(if
                                                                  (<=
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
                                                                      (>=
                                                                       (cumulative-return
                                                                        "SPXU"
                                                                        {:window
                                                                         6})
                                                                       (cumulative-return
                                                                        "UPRO"
                                                                        {:window
                                                                         3}))
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
                                                                            "ERX"
                                                                            "Direxion Daily Energy Bull 2x Shares")
                                                                           (asset
                                                                            "SHY"
                                                                            "iShares 1-3 Year Treasury Bond ETF")])])]
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (moving-average-return
                                                                           {:window
                                                                            5})
                                                                          (select-bottom
                                                                           1)
                                                                          [(asset
                                                                            "TQQQ"
                                                                            "ProShares UltraPro QQQ")
                                                                           (asset
                                                                            "SOXL"
                                                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                                                           (asset
                                                                            "CURE"
                                                                            "Direxion Daily Healthcare Bull 3x Shares")
                                                                           (asset
                                                                            "EWZ"
                                                                            "iShares MSCI Brazil ETF")
                                                                           (asset
                                                                            "SHY"
                                                                            "iShares 1-3 Year Treasury Bond ETF")])])])])]
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
                                                                          (>
                                                                           (rsi
                                                                            "TQQQ"
                                                                            {:window
                                                                             11})
                                                                           77)
                                                                          [(asset
                                                                            "VXX"
                                                                            "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                                                                          [(weight-equal
                                                                            [(if
                                                                              (<
                                                                               (cumulative-return
                                                                                "TQQQ"
                                                                                {:window
                                                                                 6})
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
                                                                                      "VXX"
                                                                                      "iPath Series B S&P 500 VIX Short-Term Futures ETN")])]
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
                                                                                        "SOXL"
                                                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                       (asset
                                                                                        "UPRO"
                                                                                        "ProShares UltraPro S&P500")
                                                                                       (asset
                                                                                        "TMV"
                                                                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                                       (asset
                                                                                        "SHY"
                                                                                        "iShares 1-3 Year Treasury Bond ETF")])])])])]
                                                                              [(weight-equal
                                                                                [(filter
                                                                                  (moving-average-return
                                                                                   {:window
                                                                                    5})
                                                                                  (select-top
                                                                                   1)
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
                                                                                    "UPRO"
                                                                                    "ProShares UltraPro S&P500")
                                                                                   (asset
                                                                                    "TMV"
                                                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                                   (asset
                                                                                    "SHY"
                                                                                    "iShares 1-3 Year Treasury Bond ETF")])])])])])])]
                                                                      [(group
                                                                        "Defense | Modified"
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (stdev-return
                                                                              "DBC"
                                                                              {:window
                                                                               20})
                                                                             (stdev-return
                                                                              "SPY"
                                                                              {:window
                                                                               20}))
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (rsi
                                                                                 {:window
                                                                                  5})
                                                                                (select-bottom
                                                                                 1)
                                                                                [(asset
                                                                                  "EEM"
                                                                                  "iShares MSCI Emerging Markets ETF")
                                                                                 (asset
                                                                                  "TECS"
                                                                                  "Direxion Daily Technology Bear 3X Shares")
                                                                                 (asset
                                                                                  "SOXS"
                                                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                 (asset
                                                                                  "TMV"
                                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])]
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (rsi
                                                                                 {:window
                                                                                  10})
                                                                                (select-bottom
                                                                                 1)
                                                                                [(asset
                                                                                  "EEM"
                                                                                  "iShares MSCI Emerging Markets ETF")
                                                                                 (asset
                                                                                  "TECS"
                                                                                  "Direxion Daily Technology Bear 3X Shares")
                                                                                 (asset
                                                                                  "SOXS"
                                                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                 (asset
                                                                                  "TMV"
                                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])]
                                                            [(group
                                                              "A.A.B.B.B: Risk Off, Falling Rates (TMF)^"
                                                              [(weight-equal
                                                                [(if
                                                                  (<=
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
                                                                      (>=
                                                                       (cumulative-return
                                                                        "SPXU"
                                                                        {:window
                                                                         6})
                                                                       (cumulative-return
                                                                        "UPRO"
                                                                        {:window
                                                                         3}))
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
                                                                            "TECL"
                                                                            "Direxion Daily Technology Bull 3x Shares")
                                                                           (asset
                                                                            "TMF"
                                                                            "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
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
                                                                            "SOXL"
                                                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                                                           (asset
                                                                            "TMF"
                                                                            "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])]
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
                                                                          (>
                                                                           (rsi
                                                                            "TQQQ"
                                                                            {:window
                                                                             11})
                                                                           77)
                                                                          [(asset
                                                                            "VXX"
                                                                            "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                                                                          [(weight-equal
                                                                            [(if
                                                                              (<
                                                                               (cumulative-return
                                                                                "TQQQ"
                                                                                {:window
                                                                                 6})
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
                                                                                      "VXX"
                                                                                      "iPath Series B S&P 500 VIX Short-Term Futures ETN")])]
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
                                                                                        "SOXL"
                                                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                       (asset
                                                                                        "PUI"
                                                                                        "Invesco DWA Utilities Momentum ETF")])])]
                                                                                  [(weight-equal
                                                                                    [(filter
                                                                                      (cumulative-return
                                                                                       {:window
                                                                                        5})
                                                                                      (select-bottom
                                                                                       1)
                                                                                      [(asset
                                                                                        "SOXS"
                                                                                        "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                       (asset
                                                                                        "SQQQ"
                                                                                        "ProShares UltraPro Short QQQ")
                                                                                       (asset
                                                                                        "ERX"
                                                                                        "Direxion Daily Energy Bull 2x Shares")
                                                                                       (asset
                                                                                        "DIG"
                                                                                        "ProShares Ultra Oil & Gas")])])])])])])])])]
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (moving-average-return
                                                                           {:window
                                                                            5})
                                                                          (select-top
                                                                           1)
                                                                          [(asset
                                                                            "EPI"
                                                                            "WisdomTree India Earnings Fund")
                                                                           (asset
                                                                            "UPRO"
                                                                            "ProShares UltraPro S&P500")
                                                                           (asset
                                                                            "SOXL"
                                                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                                                           (asset
                                                                            "TQQQ"
                                                                            "ProShares UltraPro QQQ")])])])])])])])])])])])])])])])])])])])]
                                    [(weight-equal
                                      [(group
                                        "A.B: Medium term TLT may be overbought*"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "TLT" {:window 14})
                                             80)
                                            [(weight-equal
                                              [(group
                                                "A.B.A: Medium term TLT is overbought, buy 3x leveraged bear treasury bonds (TMV)*"
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
                                                                "VXX"
                                                                "iPath Series B S&P 500 VIX Short-Term Futures ETN")])]
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
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])])])]
                                                        [(weight-equal
                                                          [(filter
                                                            (rsi
                                                             {:window
                                                              5})
                                                            (select-top
                                                             1)
                                                            [(asset
                                                              "SQQQ"
                                                              "ProShares UltraPro Short QQQ")
                                                             (asset
                                                              "TECS"
                                                              "Direxion Daily Technology Bear 3X Shares")
                                                             (asset
                                                              "SOXS"
                                                              "Direxion Daily Semiconductor Bear 3x Shares")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                                                    [(weight-equal
                                                      [(filter
                                                        (moving-average-return
                                                         {:window 5})
                                                        (select-top 1)
                                                        [(asset
                                                          "EPI"
                                                          "WisdomTree India Earnings Fund")
                                                         (asset
                                                          "UPRO"
                                                          "ProShares UltraPro S&P500")
                                                         (asset
                                                          "SOXL"
                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                         (asset
                                                          "TQQQ"
                                                          "ProShares UltraPro QQQ")
                                                         (asset
                                                          "TMV"
                                                          "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])]
                                            [(weight-equal
                                              [(group
                                                "A.B.B: Leveraged Safety*"
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
                                                            {:window
                                                             210})
                                                           (moving-average-price
                                                            "SPY"
                                                            {:window
                                                             360}))
                                                          [(weight-equal
                                                            [(if
                                                              (<
                                                               (rsi
                                                                "TQQQ"
                                                                {:window
                                                                 10})
                                                               30)
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
                                                                    "SOXL"
                                                                    "Direxion Daily Semiconductor Bull 3x Shares")
                                                                   (asset
                                                                    "UPRO"
                                                                    "ProShares UltraPro S&P500")])])]
                                                              [(weight-equal
                                                                [(if
                                                                  (>=
                                                                   (cumulative-return
                                                                    "SPXU"
                                                                    {:window
                                                                     6})
                                                                   (cumulative-return
                                                                    "UPRO"
                                                                    {:window
                                                                     3}))
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (cumulative-return
                                                                       {:window
                                                                        5})
                                                                      (select-top
                                                                       1)
                                                                      [(asset
                                                                        "SQQQ"
                                                                        "ProShares UltraPro Short QQQ")])])]
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
                                                                        "SOXL"
                                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                                       (asset
                                                                        "CURE"
                                                                        "Direxion Daily Healthcare Bull 3x Shares")])])])])])])]
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (rsi
                                                                "TQQQ"
                                                                {:window
                                                                 11})
                                                               77)
                                                              [(asset
                                                                "VXX"
                                                                "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
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
                                                                    "SOXL"
                                                                    "Direxion Daily Semiconductor Bull 3x Shares")
                                                                   (asset
                                                                    "UPRO"
                                                                    "ProShares UltraPro S&P500")
                                                                   (asset
                                                                    "TMV"
                                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])]
                                                    [(group
                                                      "A.B.B.B: Risk Off, Falling Rates (TMF)*"
                                                      [(weight-equal
                                                        [(if
                                                          (<=
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
                                                              (<
                                                               (rsi
                                                                "TQQQ"
                                                                {:window
                                                                 10})
                                                               30)
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
                                                                    "SOXL"
                                                                    "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                                              [(weight-equal
                                                                [(if
                                                                  (<=
                                                                   (cumulative-return
                                                                    "SPY"
                                                                    {:window
                                                                     2})
                                                                   -2)
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (cumulative-return
                                                                       {:window
                                                                        5})
                                                                      (select-top
                                                                       1)
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
                                                                        {:window
                                                                         6})
                                                                       (cumulative-return
                                                                        "UPRO"
                                                                        {:window
                                                                         3}))
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (cumulative-return
                                                                           {:window
                                                                            5})
                                                                          (select-top
                                                                           1)
                                                                          [(asset
                                                                            "ERX"
                                                                            "Direxion Daily Energy Bull 2x Shares")
                                                                           (asset
                                                                            "IYK"
                                                                            "iShares U.S. Consumer Staples ETF")])])]
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
                                                                            "EWZ"
                                                                            "iShares MSCI Brazil ETF")
                                                                           (asset
                                                                            "MVV"
                                                                            "ProShares Ultra MidCap400")
                                                                           (asset
                                                                            "USD"
                                                                            "ProShares Ultra Semiconductors")
                                                                           (asset
                                                                            "IYK"
                                                                            "iShares U.S. Consumer Staples ETF")])])])])])])])])]
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
                                                                  (>
                                                                   (rsi
                                                                    "TQQQ"
                                                                    {:window
                                                                     11})
                                                                   77)
                                                                  [(asset
                                                                    "VXX"
                                                                    "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                                                                  [(weight-equal
                                                                    [(if
                                                                      (<
                                                                       (cumulative-return
                                                                        "TQQQ"
                                                                        {:window
                                                                         6})
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
                                                                              "VXX"
                                                                              "iPath Series B S&P 500 VIX Short-Term Futures ETN")])]
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
                                                                                  (select-bottom
                                                                                   1)
                                                                                  [(asset
                                                                                    "SOXL"
                                                                                    "Direxion Daily Semiconductor Bull 3x Shares")])])]
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
                                                                                    "ERX"
                                                                                    "Direxion Daily Energy Bull 2x Shares")])])])])])])]
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
                                                                                "ProShares Ultra Semiconductors")
                                                                               (asset
                                                                                "IYK"
                                                                                "iShares U.S. Consumer Staples ETF")])])]
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
                                                                                "IYK"
                                                                                "iShares U.S. Consumer Staples ETF")])])])])])])])])]
                                                              [(group
                                                                "Defense | Modified"
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (stdev-return
                                                                      "DBC"
                                                                      {:window
                                                                       20})
                                                                     (stdev-return
                                                                      "SPY"
                                                                      {:window
                                                                       20}))
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (rsi
                                                                         {:window
                                                                          5})
                                                                        (select-bottom
                                                                         1)
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
                                                                          "Direxion Daily Semiconductor Bear 3x Shares")])])]
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
                                                                             {:window
                                                                              5})
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
                                                                              "ERX"
                                                                              "Direxion Daily Energy Bull 2x Shares")])])])])])])])])])])])])])])])])])])])])])])])])]
                            [(group
                              "B: If long term TLT is trending down, safety: Long Term, 2 Least Volatile*"
                              [(weight-equal
                                [(group
                                  "B.A: Leveraged Safety*"
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
                                                 (rsi
                                                  "TQQQ"
                                                  {:window 10})
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
                                                        (select-bottom
                                                         1)
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
                                                             {:window
                                                              5})
                                                            (select-top
                                                             1)
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
                                                      "VXX"
                                                      "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
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
                                                                "VXX"
                                                                "iPath Series B S&P 500 VIX Short-Term Futures ETN")])]
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
                                                            [(weight-equal
                                                              [(filter
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
                                                                  "ProShares UltraPro S&P500")])])])])])])])])]
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
                                                            {:window
                                                             10})
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
                                                                "PDBC"
                                                                "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")])])]
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
                                                                    "ERX"
                                                                    "Direxion Daily Energy Bull 2x Shares")
                                                                   (asset
                                                                    "TMV"
                                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])]
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
                                                               {:window
                                                                5})
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
                                                        (select-bottom
                                                         1)
                                                        [(asset
                                                          "BIL"
                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                         (asset
                                                          "AGG"
                                                          "iShares Core U.S. Aggregate Bond ETF")
                                                         (asset
                                                          "TMF"
                                                          "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
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
                                                          "VXX"
                                                          "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (cumulative-return
                                                              "TQQQ"
                                                              {:window
                                                               6})
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
                                                                    "VXX"
                                                                    "iPath Series B S&P 500 VIX Short-Term Futures ETN")])]
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
                                                        (rsi
                                                         {:window 5})
                                                        (select-bottom
                                                         1)
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
                                                          (rsi
                                                           {:window 5})
                                                          (select-bottom
                                                           1)
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
                                                          (select-top
                                                           1)
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
                                                            "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])])])])])])])])])])])])])])])])])])])])])
   (group
    "$ TQQQ For The Long Term Minimal | Dereck Nielsen, Pietros Maneos & Raekon v1.4 | 258.9%/42.2%DD from 28 Oct 2011 | NO K-1 mod"
    [(weight-equal
      [(if
        (>
         (current-price "SPY")
         (moving-average-price "SPY" {:window 200}))
        [(weight-equal
          [(if
            (> (rsi "TQQQ" {:window 10}) 79)
            [(asset
              "VXX"
              "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
            [(weight-equal
              [(if
                (> (rsi "SPXL" {:window 10}) 80)
                [(asset
                  "VXX"
                  "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                [(group
                  "A Better \"Buy the Dips Nasdaq\" by Garen Phillips | Raekon mod"
                  [(weight-equal
                    [(if
                      (< (cumulative-return "QQQ" {:window 5}) -6)
                      [(weight-equal
                        [(if
                          (> (cumulative-return "TQQQ" {:window 1}) 5)
                          [(asset
                            "SQQQ"
                            "ProShares UltraPro Short QQQ")]
                          [(weight-equal
                            [(if
                              (> (rsi "TQQQ" {:window 10}) 31)
                              [(asset
                                "SQQQ"
                                "ProShares UltraPro Short QQQ")]
                              [(asset
                                "TQQQ"
                                "ProShares UltraPro QQQ")])])])])]
                      [(weight-equal
                        [(if
                          (> (rsi "QQQ" {:window 10}) 80)
                          [(asset
                            "SQQQ"
                            "ProShares UltraPro Short QQQ")]
                          [(weight-equal
                            [(if
                              (> (stdev-return "TQQQ" {:window 10}) 5)
                              [(asset
                                "TLT"
                                "iShares 20+ Year Treasury Bond ETF")]
                              [(asset
                                "TQQQ"
                                "ProShares UltraPro QQQ")])])])])])])])])])])])]
        [(weight-equal
          [(if
            (< (rsi "TQQQ" {:window 10}) 31)
            [(asset "TQQQ" "ProShares UltraPro QQQ")]
            [(weight-equal
              [(if
                (< (rsi "SPY" {:window 10}) 30)
                [(asset "TQQQ" "ProShares UltraPro QQQ")]
                [(weight-equal
                  [(if
                    (> (rsi "UVXY" {:window 10}) 74)
                    [(weight-equal
                      [(if
                        (> (rsi "UVXY" {:window 10}) 84)
                        [(weight-equal
                          [(filter
                            (rsi {:window 10})
                            (select-top 1)
                            [(asset
                              "SQQQ"
                              "ProShares UltraPro Short QQQ")
                             (asset
                              "TLT"
                              "iShares 20+ Year Treasury Bond ETF")])])]
                        [(asset
                          "VXX"
                          "iPath Series B S&P 500 VIX Short-Term Futures ETN")])])]
                    [(weight-equal
                      [(if
                        (>
                         (current-price "TQQQ")
                         (moving-average-price "TQQQ" {:window 20}))
                        [(weight-equal
                          [(if
                            (< (rsi "SQQQ" {:window 10}) 31)
                            [(asset
                              "SQQQ"
                              "ProShares UltraPro Short QQQ")]
                            [(asset
                              "TQQQ"
                              "ProShares UltraPro QQQ")])])]
                        [(weight-equal
                          [(filter
                            (rsi {:window 10})
                            (select-top 1)
                            [(asset
                              "SQQQ"
                              "ProShares UltraPro Short QQQ")
                             (asset
                              "TLT"
                              "iShares 20+ Year Treasury Bond ETF")])])])])])])])])])])])])])]))
