(defsymphony
 "(B) 3x Beefier V4.1.1xxx | A Better \"LETF minimum drawdown\" | DJKeyhole 🧙‍♂️ | No UGE UUP QLD DBC (60/20%MDD) 2021"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-specified
  0.4
  (group
   "V3| S&P risk on/off | DJKeyhole ???? | Changed to V2 Advance Volatility Hedge & V1.1 A Better LETF Basket"
   [(weight-equal
     [(if
       (< (max-drawdown "SPY" {:window 10}) 5)
       [(group
         "Risk ON"
         [(weight-equal
           [(if
             (<= (max-drawdown "SPY" {:window 4}) 3)
             [(asset "SSO" "ProShares Ultra S&P 500")]
             [(weight-equal
               [(group
                 "V2 | Advanced Volatility Hedge | DJKeyhole | Modified from Garen Mod"
                 [(weight-equal
                   [(if
                     (> (cumulative-return "UVXY" {:window 5}) -0.5)
                     [(weight-inverse-volatility
                       5
                       [(asset
                         "VIXM"
                         "ProShares VIX Mid-Term Futures ETF")
                        (asset
                         "USDU"
                         "WisdomTree Bloomberg US Dollar Bullish Fund")
                        (asset
                         "UVXY"
                         "ProShares Ultra VIX Short-Term Futures ETF")])]
                     [(group
                       "Safer 20 Year Treasury Bonds with Leverage"
                       [(weight-equal
                         [(if
                           (>
                            (current-price "TLT")
                            (moving-average-price "TLT" {:window 200}))
                           [(weight-equal
                             [(group
                               "If long term TLT is trending up"
                               [(weight-equal
                                 [(if
                                   (< (rsi "TLT" {:window 14}) 50)
                                   [(weight-equal
                                     [(group
                                       "If medium term TLT is not overbought"
                                       [(weight-equal
                                         [(if
                                           (>
                                            (current-price "TLT")
                                            (moving-average-price
                                             "TLT"
                                             {:window 5}))
                                           [(weight-equal
                                             [(group
                                               "Short term TLT is trending up, buy 3x leveraged bull treasury bonds (TMF)"
                                               [(weight-equal
                                                 [(asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])]
                                           [(weight-equal
                                             [(group
                                               "If short term TLT is trending down"
                                               [(weight-equal
                                                 [(if
                                                   (<
                                                    (rsi
                                                     "TLT"
                                                     {:window 14})
                                                    20)
                                                   [(weight-equal
                                                     [(group
                                                       "Medium term TLT is underbought, buy 3x leveraged bull treasury bonds (TMF)"
                                                       [(weight-equal
                                                         [(asset
                                                           "TMF"
                                                           "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])]
                                                   [(weight-specified
                                                     1
                                                     (group
                                                      "Leveraged Safety"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (moving-average-return
                                                            "TLT"
                                                            {:window
                                                             20})
                                                           0)
                                                          [(group
                                                            "Risk Off, Rising Rates"
                                                            [(weight-equal
                                                              [(asset
                                                                "USDU"
                                                                "WisdomTree Bloomberg US Dollar Bullish Fund")
                                                               (filter
                                                                (rsi
                                                                 {:window
                                                                  20})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "PSQ"
                                                                  "ProShares Short QQQ")
                                                                 (asset
                                                                  "SH"
                                                                  "ProShares Short S&P500")
                                                                 (asset
                                                                  "USDU"
                                                                  "WisdomTree Bloomberg US Dollar Bullish Fund")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])]
                                                          [(group
                                                            "Risk Off, Falling Rates"
                                                            [(weight-equal
                                                              [(asset
                                                                "UGL"
                                                                "ProShares Ultra Gold")
                                                               (asset
                                                                "TMF"
                                                                "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                               (asset
                                                                "BTAL"
                                                                "AGFiQ US Market Neutral Anti-Beta Fund")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])]))])])])])])])])])]
                                   [(weight-equal
                                     [(group
                                       "Medium term TLT may be overbought"
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 14})
                                            80)
                                           [(weight-equal
                                             [(group
                                               "Medium term TLT is overbought, buy 3x leveraged bear treasury bonds (TMV)"
                                               [(weight-equal
                                                 [(asset
                                                   "TMV"
                                                   "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])]
                                           [(weight-specified
                                             1
                                             (group
                                              "Leveraged Safety"
                                              [(weight-specified
                                                1
                                                (if
                                                 (<
                                                  (moving-average-return
                                                   "TLT"
                                                   {:window 20})
                                                  0)
                                                 [(group
                                                   "Risk Off, Rising Rates"
                                                   [(weight-equal
                                                     [(asset
                                                       "USDU"
                                                       "WisdomTree Bloomberg US Dollar Bullish Fund")
                                                      (filter
                                                       (rsi
                                                        {:window 20})
                                                       (select-bottom
                                                        1)
                                                       [(asset
                                                         "PSQ"
                                                         "ProShares Short QQQ")
                                                        (asset
                                                         "SH"
                                                         "ProShares Short S&P500")
                                                        (asset
                                                         "USDU"
                                                         "WisdomTree Bloomberg US Dollar Bullish Fund")
                                                        (asset
                                                         "TMV"
                                                         "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])]
                                                 [(group
                                                   "Risk Off, Falling Rates"
                                                   [(weight-equal
                                                     [(asset
                                                       "UGL"
                                                       "ProShares Ultra Gold")
                                                      (asset
                                                       "TMF"
                                                       "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                      (asset
                                                       "BTAL"
                                                       "AGFiQ US Market Neutral Anti-Beta Fund")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])]))]))])])])])])])])])]
                           [(group
                             "Safety: Long Term, 2 Least Volatile"
                             [(weight-equal
                               [(group
                                 "Leveraged Safety"
                                 [(weight-specified
                                   1
                                   (if
                                    (<
                                     (moving-average-return
                                      "TLT"
                                      {:window 20})
                                     0)
                                    [(group
                                      "Risk Off, Rising Rates"
                                      [(weight-equal
                                        [(asset
                                          "USDU"
                                          "WisdomTree Bloomberg US Dollar Bullish Fund")
                                         (filter
                                          (rsi {:window 20})
                                          (select-bottom 1)
                                          [(asset
                                            "PSQ"
                                            "ProShares Short QQQ")
                                           (asset
                                            "SH"
                                            "ProShares Short S&P500")
                                           (asset
                                            "USDU"
                                            "WisdomTree Bloomberg US Dollar Bullish Fund")
                                           (asset
                                            "TMV"
                                            "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])]
                                    [(group
                                      "Risk Off, Falling Rates"
                                      [(weight-equal
                                        [(asset
                                          "UGL"
                                          "ProShares Ultra Gold")
                                         (asset
                                          "TMF"
                                          "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                         (asset
                                          "BTAL"
                                          "AGFiQ US Market Neutral Anti-Beta Fund")
                                         (asset
                                          "XLP"
                                          "Consumer Staples Select Sector SPDR Fund")])])]))])])])])])])])])])
                (group
                 "V2.0.1 | A Better LETF Basket | DJKeyhole ???? | No UGE"
                 [(weight-equal
                   [(if
                     (>
                      (current-price "TLT")
                      (moving-average-price "TLT" {:window 200}))
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
                                                      {:window 7})
                                                     (select-bottom 1)
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
                                                      {:window 7})
                                                     (select-bottom 1)
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
                                              (rsi "TLT" {:window 14})
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
                                                       {:window 20})
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
                                                                     "UVXY"
                                                                     "ProShares Ultra VIX Short-Term Futures ETF")]
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
                                                                     "UVXY"
                                                                     "ProShares Ultra VIX Short-Term Futures ETF")]
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
                                                                                 "EWZ"
                                                                                 "iShares MSCI Brazil ETF")
                                                                                (asset
                                                                                 "MVV"
                                                                                 "ProShares Ultra MidCap400")
                                                                                (asset
                                                                                 "PUI"
                                                                                 "Invesco DWA Utilities Momentum ETF")
                                                                                (asset
                                                                                 "IYK"
                                                                                 "iShares U.S. Consumer Staples ETF")
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
                                                                                 "UCO"
                                                                                 "ProShares Ultra Bloomberg Crude Oil")
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
                                     (> (rsi "TLT" {:window 14}) 80)
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
                                                       {:window 1})
                                                      5.5)
                                                     [(weight-equal
                                                       [(asset
                                                         "UVXY"
                                                         "ProShares Ultra VIX Short-Term Futures ETF")])]
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
                                                           "UPRO"
                                                           "ProShares UltraPro S&P500")])])])])]
                                                 [(weight-equal
                                                   [(filter
                                                     (rsi {:window 5})
                                                     (select-top 1)
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
                                                                 "ProShares UltraPro Short QQQ")
                                                                (asset
                                                                 "EUO"
                                                                 "ProShares UltraShort Euro")
                                                                (asset
                                                                 "YCS"
                                                                 "ProShares UltraShort Yen")])])]
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
                                                         {:window 11})
                                                        77)
                                                       [(asset
                                                         "UVXY"
                                                         "ProShares Ultra VIX Short-Term Futures ETF")]
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
                                                                     "EUO"
                                                                     "ProShares UltraShort Euro")
                                                                    (asset
                                                                     "YCS"
                                                                     "ProShares UltraShort Yen")])])]
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
                                                                     "ProShares Ultra Semiconductors")])])])])])])])])]
                                                   [(weight-equal
                                                     [(if
                                                       (>
                                                        (moving-average-return
                                                         "SPY"
                                                         {:window 210})
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
                                                             "UVXY"
                                                             "ProShares Ultra VIX Short-Term Futures ETF")]
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
                                                                             "USDU"
                                                                             "WisdomTree Bloomberg US Dollar Bullish Fund")
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
                                                                         "USDU"
                                                                         "WisdomTree Bloomberg US Dollar Bullish Fund")
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
                                                                       "UCO"
                                                                       "ProShares Ultra Bloomberg Crude Oil")
                                                                      (asset
                                                                       "YCS"
                                                                       "ProShares UltraShort Yen")])])])])])])])])])])])])])])])])])])])])])])])])]
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
                                                     (select-bottom 1)
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
                                              (rsi "TQQQ" {:window 11})
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
                                                          {:window 5})
                                                         (select-bottom
                                                          1)
                                                         [(asset
                                                           "SOXL"
                                                           "Direxion Daily Semiconductor Bull 3x Shares")
                                                          (asset
                                                           "IYK"
                                                           "iShares U.S. Consumer Staples ETF")
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
                                                           "ProShares UltraPro S&P500")
                                                          (asset
                                                           "TMV"
                                                           "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                          (asset
                                                           "IYK"
                                                           "iShares U.S. Consumer Staples ETF")
                                                          (asset
                                                           "TECL"
                                                           "Direxion Daily Technology Bull 3x Shares")])])]
                                                     [(weight-equal
                                                       [(filter
                                                         (moving-average-return
                                                          {:window 22})
                                                         (select-bottom
                                                          1)
                                                         [(asset
                                                           "SOXL"
                                                           "Direxion Daily Semiconductor Bull 3x Shares")
                                                          (asset
                                                           "UPRO"
                                                           "ProShares UltraPro S&P500")
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
                                                         {:window 5})
                                                        (stdev-return
                                                         "DBC"
                                                         {:window 5}))
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
                                                         "ProShares UltraPro S&P500")
                                                        (asset
                                                         "IYK"
                                                         "iShares U.S. Consumer Staples ETF")])])]
                                                   [(weight-equal
                                                     [(filter
                                                       (cumulative-return
                                                        {:window 5})
                                                       (select-top 1)
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
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
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
                                                               "EWZ"
                                                               "iShares MSCI Brazil ETF")
                                                              (asset
                                                               "MVV"
                                                               "ProShares Ultra MidCap400")
                                                              (asset
                                                               "PUI"
                                                               "Invesco DWA Utilities Momentum ETF")
                                                              (asset
                                                               "IYK"
                                                               "iShares U.S. Consumer Staples ETF")
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
                                                           {:window 7})
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
                                                               "ProShares Ultra MidCap400")
                                                              (asset
                                                               "UGE"
                                                               "ProShares Ultra Consumer Goods")])])]
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
                                                     "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])])])])])])])])])])])])])])])]
       [(group
         "Risk Off"
         [(weight-equal
           [(if
             (>
              (current-price "SPY")
              (moving-average-price "SPY" {:window 20}))
             [(weight-equal
               [(if
                 (< (rsi "SH" {:window 10}) 31)
                 [(asset "SH" "ProShares Short S&P500")]
                 [(asset "UPRO" "ProShares UltraPro S&P500")])])]
             [(weight-equal
               [(filter
                 (rsi {:window 10})
                 (select-top 1)
                 [(asset "SH" "ProShares Short S&P500")
                  (asset "BSV" "Vanguard Short-Term Bond ETF")])
                (group
                 "Advanced Volatility Hedge | DJKeyhole V2 (Modified from Garen Mod)"
                 [(weight-equal
                   [(if
                     (> (cumulative-return "UVXY" {:window 5}) -0.5)
                     [(weight-inverse-volatility
                       5
                       [(asset
                         "VIXM"
                         "ProShares VIX Mid-Term Futures ETF")
                        (asset
                         "USDU"
                         "WisdomTree Bloomberg US Dollar Bullish Fund")
                        (asset
                         "UVXY"
                         "ProShares Ultra VIX Short-Term Futures ETF")])]
                     [(group
                       "Safer 20 Year Treasury Bonds with Leverage"
                       [(weight-equal
                         [(if
                           (>
                            (current-price "TLT")
                            (moving-average-price "TLT" {:window 200}))
                           [(weight-equal
                             [(group
                               "If long term TLT is trending up"
                               [(weight-equal
                                 [(if
                                   (< (rsi "TLT" {:window 14}) 50)
                                   [(weight-equal
                                     [(group
                                       "If medium term TLT is not overbought"
                                       [(weight-equal
                                         [(if
                                           (>
                                            (current-price "TLT")
                                            (moving-average-price
                                             "TLT"
                                             {:window 5}))
                                           [(weight-equal
                                             [(group
                                               "Short term TLT is trending up, buy 3x leveraged bull treasury bonds (TMF)"
                                               [(weight-equal
                                                 [(asset
                                                   "TMF"
                                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])]
                                           [(weight-equal
                                             [(group
                                               "If short term TLT is trending down"
                                               [(weight-equal
                                                 [(if
                                                   (<
                                                    (rsi
                                                     "TLT"
                                                     {:window 14})
                                                    20)
                                                   [(weight-equal
                                                     [(group
                                                       "Medium term TLT is underbought, buy 3x leveraged bull treasury bonds (TMF)"
                                                       [(weight-equal
                                                         [(asset
                                                           "TMF"
                                                           "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])]
                                                   [(weight-specified
                                                     1
                                                     (group
                                                      "Leveraged Safety"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (moving-average-return
                                                            "TLT"
                                                            {:window
                                                             20})
                                                           0)
                                                          [(group
                                                            "Risk Off, Rising Rates"
                                                            [(weight-equal
                                                              [(asset
                                                                "USDU"
                                                                "WisdomTree Bloomberg US Dollar Bullish Fund")
                                                               (filter
                                                                (rsi
                                                                 {:window
                                                                  20})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "PSQ"
                                                                  "ProShares Short QQQ")
                                                                 (asset
                                                                  "SH"
                                                                  "ProShares Short S&P500")
                                                                 (asset
                                                                  "USDU"
                                                                  "WisdomTree Bloomberg US Dollar Bullish Fund")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])]
                                                          [(group
                                                            "Risk Off, Falling Rates"
                                                            [(weight-equal
                                                              [(asset
                                                                "UGL"
                                                                "ProShares Ultra Gold")
                                                               (asset
                                                                "TMF"
                                                                "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                               (asset
                                                                "BTAL"
                                                                "AGFiQ US Market Neutral Anti-Beta Fund")
                                                               (asset
                                                                "XLP"
                                                                "Consumer Staples Select Sector SPDR Fund")])])])])]))])])])])])])])])]
                                   [(weight-equal
                                     [(group
                                       "Medium term TLT may be overbought"
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 14})
                                            80)
                                           [(weight-equal
                                             [(group
                                               "Medium term TLT is overbought, buy 3x leveraged bear treasury bonds (TMV)"
                                               [(weight-equal
                                                 [(asset
                                                   "TMV"
                                                   "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])]
                                           [(weight-specified
                                             1
                                             (group
                                              "Leveraged Safety"
                                              [(weight-specified
                                                1
                                                (if
                                                 (<
                                                  (moving-average-return
                                                   "TLT"
                                                   {:window 20})
                                                  0)
                                                 [(group
                                                   "Risk Off, Rising Rates"
                                                   [(weight-equal
                                                     [(asset
                                                       "USDU"
                                                       "WisdomTree Bloomberg US Dollar Bullish Fund")
                                                      (filter
                                                       (rsi
                                                        {:window 20})
                                                       (select-bottom
                                                        1)
                                                       [(asset
                                                         "PSQ"
                                                         "ProShares Short QQQ")
                                                        (asset
                                                         "SH"
                                                         "ProShares Short S&P500")
                                                        (asset
                                                         "USDU"
                                                         "WisdomTree Bloomberg US Dollar Bullish Fund")
                                                        (asset
                                                         "TMV"
                                                         "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])]
                                                 [(group
                                                   "Risk Off, Falling Rates"
                                                   [(weight-equal
                                                     [(asset
                                                       "UGL"
                                                       "ProShares Ultra Gold")
                                                      (asset
                                                       "TMF"
                                                       "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                      (asset
                                                       "BTAL"
                                                       "AGFiQ US Market Neutral Anti-Beta Fund")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])]))]))])])])])])])])])]
                           [(group
                             "Safety: Long Term, 2 Least Volatile"
                             [(weight-equal
                               [(group
                                 "Leveraged Safety"
                                 [(weight-specified
                                   1
                                   (if
                                    (<
                                     (moving-average-return
                                      "TLT"
                                      {:window 20})
                                     0)
                                    [(group
                                      "Risk Off, Rising Rates"
                                      [(weight-equal
                                        [(asset
                                          "USDU"
                                          "WisdomTree Bloomberg US Dollar Bullish Fund")
                                         (filter
                                          (rsi {:window 20})
                                          (select-bottom 1)
                                          [(asset
                                            "PSQ"
                                            "ProShares Short QQQ")
                                           (asset
                                            "SH"
                                            "ProShares Short S&P500")
                                           (asset
                                            "USDU"
                                            "WisdomTree Bloomberg US Dollar Bullish Fund")
                                           (asset
                                            "TMV"
                                            "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])]
                                    [(group
                                      "Risk Off, Falling Rates"
                                      [(weight-equal
                                        [(asset
                                          "UGL"
                                          "ProShares Ultra Gold")
                                         (asset
                                          "TMF"
                                          "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                         (asset
                                          "BTAL"
                                          "AGFiQ US Market Neutral Anti-Beta Fund")
                                         (asset
                                          "XLP"
                                          "Consumer Staples Select Sector SPDR Fund")])])]))])])])])])])])])])])])])])])])])
  0.6
  (group
   "V3.1.1 | A Better \"Buy the Dips LETFs\" | DJKeyhole ???? | No UGE"
   [(weight-equal
     [(if
       (< (cumulative-return "QQQ" {:window 5}) -6)
       [(weight-equal
         [(if
           (> (cumulative-return "TQQQ" {:window 1}) 5)
           [(weight-equal
             [(filter
               (cumulative-return {:window 5})
               (select-top 1)
               [(asset
                 "SOXS"
                 "Direxion Daily Semiconductor Bear 3x Shares")
                (asset "SQQQ" "ProShares UltraPro Short QQQ")])])]
           [(weight-equal
             [(if
               (> (rsi "TQQQ" {:window 10}) 31)
               [(weight-equal
                 [(filter
                   (cumulative-return {:window 5})
                   (select-bottom 1)
                   [(asset
                     "SOXS"
                     "Direxion Daily Semiconductor Bear 3x Shares")
                    (asset "SQQQ" "ProShares UltraPro Short QQQ")])])]
               [(weight-equal
                 [(filter
                   (cumulative-return {:window 5})
                   (select-bottom 1)
                   [(asset
                     "SOXL"
                     "Direxion Daily Semiconductor Bull 3x Shares")
                    (asset
                     "TQQQ"
                     "ProShares UltraPro QQQ")])])])])])])]
       [(group
         "V2.0.1 | A Better LETF Basket | DJKeyhole ???? | No UGE"
         [(weight-equal
           [(if
             (>
              (current-price "TLT")
              (moving-average-price "TLT" {:window 200}))
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
                              (moving-average-price "TLT" {:window 5}))
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
                                          (rsi "TQQQ" {:window 10})
                                          30)
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
                                              {:window 7})
                                             (select-bottom 1)
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
                                              {:window 7})
                                             (select-bottom 1)
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
                                     (< (rsi "TLT" {:window 14}) 20)
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
                                               {:window 20})
                                              0)
                                             [(group
                                               "A.A.B.B.A: Risk Off, Rising Rates (TMV)*"
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
                                                         {:window 210})
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
                                                             "UVXY"
                                                             "ProShares Ultra VIX Short-Term Futures ETF")]
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
                                                     {:window 210})
                                                    (moving-average-price
                                                     "SPY"
                                                     {:window 360}))
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
                                                         {:window 210})
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
                                                             "UVXY"
                                                             "ProShares Ultra VIX Short-Term Futures ETF")]
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
                                                                         "EWZ"
                                                                         "iShares MSCI Brazil ETF")
                                                                        (asset
                                                                         "MVV"
                                                                         "ProShares Ultra MidCap400")
                                                                        (asset
                                                                         "PUI"
                                                                         "Invesco DWA Utilities Momentum ETF")
                                                                        (asset
                                                                         "IYK"
                                                                         "iShares U.S. Consumer Staples ETF")
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
                                                                         "UCO"
                                                                         "ProShares Ultra Bloomberg Crude Oil")
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
                             (> (rsi "TLT" {:window 14}) 80)
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
                                               {:window 1})
                                              5.5)
                                             [(weight-equal
                                               [(asset
                                                 "UVXY"
                                                 "ProShares Ultra VIX Short-Term Futures ETF")])]
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
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")])])])])]
                                         [(weight-equal
                                           [(filter
                                             (rsi {:window 5})
                                             (select-top 1)
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
                                                     "UPRO"
                                                     "ProShares UltraPro S&P500")])])]
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
                                                         "SQQQ"
                                                         "ProShares UltraPro Short QQQ")
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
                                                 {:window 11})
                                                77)
                                               [(asset
                                                 "UVXY"
                                                 "ProShares Ultra VIX Short-Term Futures ETF")]
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
                                                   (select-bottom 1)
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
                                                            {:window
                                                             5})
                                                           (select-top
                                                            1)
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
                                                             {:window
                                                              1})
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
                                                                     "USDU"
                                                                     "WisdomTree Bloomberg US Dollar Bullish Fund")
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
                                                                 "USDU"
                                                                 "WisdomTree Bloomberg US Dollar Bullish Fund")
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
                                                         (rsi
                                                          {:window 5})
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
                                                               "UCO"
                                                               "ProShares Ultra Bloomberg Crude Oil")
                                                              (asset
                                                               "YCS"
                                                               "ProShares UltraShort Yen")])])])])])])])])])])])])])])])])])])])])])])])])]
             [(group
               "B: If long term TLT is trending down, safety: Long Term, 2 Least Volatile*"
               [(weight-equal
                 [(group
                   "B.A: Leveraged Safety*"
                   [(weight-equal
                     [(if
                       (< (moving-average-return "TLT" {:window 20}) 0)
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
                                 (< (rsi "TQQQ" {:window 10}) 30)
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
                                             (select-bottom 1)
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
                                     (> (rsi "TQQQ" {:window 11}) 77)
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
                                                  {:window 5})
                                                 (select-bottom 1)
                                                 [(asset
                                                   "SOXL"
                                                   "Direxion Daily Semiconductor Bull 3x Shares")
                                                  (asset
                                                   "IYK"
                                                   "iShares U.S. Consumer Staples ETF")
                                                  (asset
                                                   "TMV"
                                                   "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                                         [(weight-equal
                                           [(if
                                             (<
                                              (rsi "BIL" {:window 7})
                                              (rsi "IEF" {:window 7}))
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
                                                   "ProShares UltraPro S&P500")
                                                  (asset
                                                   "TMV"
                                                   "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                  (asset
                                                   "IYK"
                                                   "iShares U.S. Consumer Staples ETF")
                                                  (asset
                                                   "TECL"
                                                   "Direxion Daily Technology Bull 3x Shares")])])]
                                             [(weight-equal
                                               [(filter
                                                 (moving-average-return
                                                  {:window 22})
                                                 (select-bottom 1)
                                                 [(asset
                                                   "SOXL"
                                                   "Direxion Daily Semiconductor Bull 3x Shares")
                                                  (asset
                                                   "UPRO"
                                                   "ProShares UltraPro S&P500")
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
                                                 {:window 5})
                                                (stdev-return
                                                 "DBC"
                                                 {:window 5}))
                                               [(asset
                                                 "TMV"
                                                 "Direxion Daily 20+ Year Treasury Bear 3x Shares")]
                                               [(asset
                                                 "PDBC"
                                                 "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi "BIL" {:window 7})
                                                (rsi
                                                 "IEF"
                                                 {:window 7}))
                                               [(weight-equal
                                                 [(filter
                                                   (moving-average-return
                                                    {:window 5})
                                                   (select-top 1)
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
                                                    {:window 5})
                                                   (select-bottom 1)
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
                                            (rsi "BIL" {:window 7})
                                            (rsi "IEF" {:window 7}))
                                           [(weight-equal
                                             [(filter
                                               (moving-average-return
                                                {:window 5})
                                               (select-bottom 1)
                                               [(asset
                                                 "EPI"
                                                 "WisdomTree India Earnings Fund")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")
                                                (asset
                                                 "UPRO"
                                                 "ProShares UltraPro S&P500")
                                                (asset
                                                 "IYK"
                                                 "iShares U.S. Consumer Staples ETF")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 5})
                                               (select-top 1)
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
                                  (cumulative-return "SPY" {:window 2})
                                  -2)
                                 [(weight-equal
                                   [(filter
                                     (cumulative-return {:window 5})
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
                                           "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
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
                                          (rsi "TQQQ" {:window 11})
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
                                                      {:window 7})
                                                     (select-bottom 1)
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
                                                       "EWZ"
                                                       "iShares MSCI Brazil ETF")
                                                      (asset
                                                       "MVV"
                                                       "ProShares Ultra MidCap400")
                                                      (asset
                                                       "PUI"
                                                       "Invesco DWA Utilities Momentum ETF")
                                                      (asset
                                                       "IYK"
                                                       "iShares U.S. Consumer Staples ETF")
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
                                                   {:window 7})
                                                  (rsi
                                                   "IEF"
                                                   {:window 7}))
                                                 [(weight-equal
                                                   [(filter
                                                     (moving-average-return
                                                      {:window 7})
                                                     (select-bottom 1)
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
                                                       "ProShares Ultra MidCap400")
                                                      (asset
                                                       "UGE"
                                                       "ProShares Ultra Consumer Goods")])])]
                                                 [(weight-equal
                                                   [(filter
                                                     (cumulative-return
                                                      {:window 5})
                                                     (select-top 1)
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
                                             "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])])])])])])])])])])])])])])))
