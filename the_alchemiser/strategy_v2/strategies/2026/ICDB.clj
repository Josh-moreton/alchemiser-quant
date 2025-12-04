(defsymphony
 "ICDB: TQQQ FP + EMs + Phoenix Jorgmundr + Vol Catcher"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-specified
  0.5
  (if
   (> (rsi "XLK" {:window 10}) (rsi "KMLM" {:window 10}))
   [(group
     "TQQQ FTLT | Full Package | Diceroll Group | Shorter Backtest v2 [FTL]"
     [(weight-equal
       [(filter
         (cumulative-return {:window 20})
         (select-top 2)
         [(group
           "TQQQ FTLT | Full Package | 20d max DD | Bottom 1 | Shorter Backtest"
           [(weight-equal
             [(filter
               (max-drawdown {:window 20})
               (select-bottom 1)
               [(group
                 "TQQQ For The Long Term 'Original' (longer backtest)"
                 [(weight-equal
                   [(if
                     (>
                      (current-price "SPY")
                      (moving-average-price "SPY" {:window 200}))
                     [(weight-equal
                       [(group
                         "Bull Market"
                         [(weight-equal
                           [(if
                             (> (rsi "QQQ" {:window 10}) 80)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(weight-equal
                               [(if
                                 (> (rsi "SPY" {:window 10}) 80)
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")]
                                 [(weight-equal
                                   [(if
                                     (> (rsi "SPY" {:window 60}) 60)
                                     [(weight-equal
                                       [(filter
                                         (moving-average-return
                                          {:window 15})
                                         (select-top 1)
                                         [(asset
                                           "TMF"
                                           "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                          (asset
                                           "UUP"
                                           "Invesco DB US Dollar Index Bullish Fund")
                                          (asset
                                           "VIXY"
                                           "ProShares VIX Short-Term Futures ETF")
                                          (asset
                                           "XLP"
                                           "Consumer Staples Select Sector SPDR Fund")
                                          (asset
                                           "SPLV"
                                           "Invesco S&P 500 Low Volatility ETF")
                                          (asset
                                           "BTAL"
                                           "AGF U.S. Market Neutral Anti-Beta Fund")])])]
                                     [(weight-specified
                                       0.67
                                       (filter
                                        (moving-average-return
                                         {:window 21})
                                        (select-top 3)
                                        [(asset
                                          "TQQQ"
                                          "ProShares UltraPro QQQ")
                                         (asset
                                          "SOXL"
                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                         (asset
                                          "TECL"
                                          "Direxion Daily Technology Bull 3x Shares")
                                         (asset
                                          "UDOW"
                                          "ProShares UltraPro Dow30")
                                         (asset
                                          "UPRO"
                                          "ProShares UltraPro S&P500")
                                         (asset
                                          "ROM"
                                          "ProShares Ultra Technology")
                                         (asset
                                          "QLD"
                                          "ProShares Ultra QQQ")
                                         (asset
                                          "SSO"
                                          "ProShares Ultra S&P 500")
                                         (asset
                                          "URTY"
                                          "ProShares UltraPro Russell2000")])
                                       0.33
                                       (asset
                                        "SVXY"
                                        "ProShares Short VIX Short-Term Futures ETF"))])])])])])])])])]
                     [(weight-equal
                       [(group
                         "Modified Dip Buy Strategy"
                         [(weight-equal
                           [(if
                             (< (rsi "TECL" {:window 10}) 30)
                             [(asset
                               "TECL"
                               "Direxion Daily Technology Bull 3x Shares")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])
                            (if
                             (< (rsi "SOXL" {:window 10}) 30)
                             [(asset
                               "SOXL"
                               "Direxion Daily Semiconductor Bull 3x Shares")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])
                            (if
                             (< (rsi "TQQQ" {:window 10}) 30)
                             [(asset "TQQQ" "ProShares UltraPro QQQ")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])
                            (if
                             (< (rsi "UPRO" {:window 10}) 30)
                             [(asset
                               "UPRO"
                               "ProShares UltraPro S&P500")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])
                            (if
                             (< (rsi "URTY" {:window 10}) 30)
                             [(asset
                               "URTY"
                               "ProShares UltraPro Russell2000")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])
                (group
                 "TQQQ For The Long Term (Reddit Post Link)"
                 [(weight-equal
                   [(if
                     (>
                      (current-price "SPY")
                      (moving-average-price "SPY" {:window 200}))
                     [(weight-equal
                       [(if
                         (> (rsi "TQQQ" {:window 10}) 79)
                         [(asset
                           "UVXY"
                           "ProShares Ultra VIX Short-Term Futures ETF")]
                         [(weight-equal
                           [(if
                             (> (rsi "SPXL" {:window 10}) 80)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(weight-equal
                               [(asset
                                 "TQQQ"
                                 "ProShares UltraPro QQQ")])])])])])]
                     [(weight-equal
                       [(if
                         (< (rsi "TQQQ" {:window 10}) 31)
                         [(asset
                           "TECL"
                           "Direxion Daily Technology Bull 3x Shares")]
                         [(weight-equal
                           [(if
                             (< (rsi "SPY" {:window 10}) 30)
                             [(asset
                               "UPRO"
                               "ProShares UltraPro S&P500")]
                             [(weight-equal
                               [(if
                                 (<
                                  (current-price "TQQQ")
                                  (moving-average-price
                                   "TQQQ"
                                   {:window 20}))
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
                                 [(weight-equal
                                   [(if
                                     (< (rsi "SQQQ" {:window 10}) 31)
                                     [(asset
                                       "SQQQ"
                                       "ProShares UltraPro Short QQQ")]
                                     [(asset
                                       "TQQQ"
                                       "ProShares UltraPro QQQ")])])])])])])])])])])])
                (group
                 "TQQQ For The Long Term V2"
                 [(weight-equal
                   [(if
                     (>
                      (current-price "SPY")
                      (moving-average-price "SPY" {:window 200}))
                     [(weight-equal
                       [(if
                         (> (rsi "TQQQ" {:window 10}) 79)
                         [(asset
                           "UVXY"
                           "ProShares Ultra VIX Short-Term Futures ETF")]
                         [(weight-equal
                           [(if
                             (> (rsi "SPXL" {:window 10}) 80)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(asset
                               "TQQQ"
                               "ProShares UltraPro QQQ")])])])])]
                     [(weight-equal
                       [(if
                         (< (rsi "TQQQ" {:window 10}) 31)
                         [(asset
                           "TECL"
                           "Direxion Daily Technology Bull 3x Shares")]
                         [(weight-equal
                           [(if
                             (< (rsi "SPY" {:window 10}) 30)
                             [(asset
                               "SPXL"
                               "Direxion Daily S&P 500 Bull 3x Shares")]
                             [(weight-equal
                               [(if
                                 (> (rsi "UVXY" {:window 10}) 74)
                                 [(weight-equal
                                   [(if
                                     (> (rsi "UVXY" {:window 10}) 84)
                                     [(weight-equal
                                       [(if
                                         (>
                                          (current-price "TQQQ")
                                          (moving-average-price
                                           "TQQQ"
                                           {:window 20}))
                                         [(asset
                                           "TQQQ"
                                           "ProShares UltraPro QQQ")]
                                         [(weight-equal
                                           [(filter
                                             (rsi {:window 10})
                                             (select-top 1)
                                             [(asset
                                               "SQQQ"
                                               "ProShares UltraPro Short QQQ")
                                              (asset
                                               "BSV"
                                               "Vanguard Short-Term Bond ETF")])])])])]
                                     [(asset
                                       "UVXY"
                                       "ProShares Ultra VIX Short-Term Futures ETF")])])]
                                 [(weight-equal
                                   [(if
                                     (>
                                      (current-price "TQQQ")
                                      (moving-average-price
                                       "TQQQ"
                                       {:window 20}))
                                     [(asset
                                       "TQQQ"
                                       "ProShares UltraPro QQQ")]
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 10})
                                         (select-top 1)
                                         [(asset
                                           "SQQQ"
                                           "ProShares UltraPro Short QQQ")
                                          (asset
                                           "BSV"
                                           "Vanguard Short-Term Bond ETF")])])])])])])])])])])])])])
                (group
                 "TQQQ FTLT w/Sideways Market Mods"
                 [(weight-equal
                   [(if
                     (>
                      (current-price "SPY")
                      (moving-average-price "SPY" {:window 200}))
                     [(weight-equal
                       [(if
                         (> (rsi "TQQQ" {:window 10}) 79)
                         [(asset
                           "UVXY"
                           "ProShares Ultra VIX Short-Term Futures ETF")]
                         [(weight-equal
                           [(if
                             (> (rsi "SPXL" {:window 10}) 80)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(weight-equal
                               [(if
                                 (>
                                  (cumulative-return
                                   "TQQQ"
                                   {:window 5})
                                  20)
                                 [(weight-equal
                                   [(if
                                     (< (rsi "TQQQ" {:window 10}) 31)
                                     [(asset
                                       "TQQQ"
                                       "ProShares UltraPro QQQ")]
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 10})
                                         (select-top 1)
                                         [(asset
                                           "UVXY"
                                           "ProShares Ultra VIX Short-Term Futures ETF")
                                          (asset
                                           "SQQQ"
                                           "ProShares UltraPro Short QQQ")])])])])]
                                 [(weight-equal
                                   [(asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])])])])])])])]
                     [(weight-equal
                       [(if
                         (< (rsi "TQQQ" {:window 10}) 31)
                         [(asset
                           "TECL"
                           "Direxion Daily Technology Bull 3x Shares")]
                         [(weight-equal
                           [(if
                             (< (rsi "SMH" {:window 10}) 30)
                             [(asset
                               "SOXL"
                               "Direxion Daily Semiconductor Bull 3x Shares")]
                             [(weight-equal
                               [(if
                                 (< (rsi "DIA" {:window 10}) 27)
                                 [(asset
                                   "UDOW"
                                   "ProShares UltraPro Dow30")]
                                 [(weight-equal
                                   [(if
                                     (< (rsi "SPY" {:window 14}) 28)
                                     [(asset
                                       "UPRO"
                                       "ProShares UltraPro S&P500")]
                                     [(weight-equal
                                       [(if
                                         (<
                                          (cumulative-return
                                           "QQQ"
                                           {:window 200})
                                          -20)
                                         [(weight-equal
                                           [(group
                                             "Nasdaq In Crash Territory, Time to Deleverage"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (current-price "QQQ")
                                                  (moving-average-price
                                                   "QQQ"
                                                   {:window 20}))
                                                 [(weight-equal
                                                   [(if
                                                     (<=
                                                      (cumulative-return
                                                       "QQQ"
                                                       {:window 60})
                                                      -12)
                                                     [(group
                                                       "Sideways Market Deleverage"
                                                       [(weight-equal
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (current-price
                                                               "SPY")
                                                              (moving-average-price
                                                               "SPY"
                                                               {:window
                                                                20}))
                                                             [(asset
                                                               "SPY"
                                                               "SPDR S&P 500 ETF Trust")]
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (rsi
                                                                   "TLT"
                                                                   {:window
                                                                    10})
                                                                  (rsi
                                                                   "SQQQ"
                                                                   {:window
                                                                    10}))
                                                                 [(asset
                                                                   "QQQ"
                                                                   "Invesco QQQ Trust")]
                                                                 [(asset
                                                                   "PSQ"
                                                                   "ProShares Short QQQ")])])])
                                                            (if
                                                             (>
                                                              (rsi
                                                               "TLT"
                                                               {:window
                                                                10})
                                                              (rsi
                                                               "SQQQ"
                                                               {:window
                                                                10}))
                                                             [(asset
                                                               "QQQ"
                                                               "Invesco QQQ Trust")]
                                                             [(asset
                                                               "PSQ"
                                                               "ProShares Short QQQ")])])])])]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "TQQQ"
                                                           "ProShares UltraPro QQQ")]
                                                         [(asset
                                                           "SQQQ"
                                                           "ProShares UltraPro Short QQQ")])])])])]
                                                 [(weight-equal
                                                   [(if
                                                     (<
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10})
                                                      31)
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (cumulative-return
                                                           "QQQ"
                                                           {:window
                                                            10})
                                                          5.5)
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")]
                                                         [(weight-equal
                                                           [(filter
                                                             (rsi
                                                              {:window
                                                               10})
                                                             (select-top
                                                              1)
                                                             [(asset
                                                               "QQQ"
                                                               "Invesco QQQ Trust")
                                                              (asset
                                                               "SMH"
                                                               "VanEck Semiconductor ETF")])])])])])])])])])])]
                                         [(weight-equal
                                           [(if
                                             (<
                                              (current-price "QQQ")
                                              (moving-average-price
                                               "QQQ"
                                               {:window 20}))
                                             [(weight-equal
                                               [(if
                                                 (>
                                                  (rsi
                                                   "TLT"
                                                   {:window 10})
                                                  (rsi
                                                   "SQQQ"
                                                   {:window 10}))
                                                 [(asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")]
                                                 [(asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")])])]
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (rsi
                                                   "SQQQ"
                                                   {:window 10})
                                                  31)
                                                 [(asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")]
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "QQQ"
                                                       {:window 10})
                                                      5.5)
                                                     [(asset
                                                       "SQQQ"
                                                       "ProShares UltraPro Short QQQ")]
                                                     [(weight-equal
                                                       [(filter
                                                         (rsi
                                                          {:window 10})
                                                         (select-top 1)
                                                         [(asset
                                                           "TQQQ"
                                                           "ProShares UltraPro QQQ")
                                                          (asset
                                                           "SOXL"
                                                           "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                        (if
                                         (<
                                          (current-price "QQQ")
                                          (moving-average-price
                                           "QQQ"
                                           {:window 20}))
                                         [(weight-equal
                                           [(if
                                             (<=
                                              (cumulative-return
                                               "QQQ"
                                               {:window 60})
                                              -12)
                                             [(group
                                               "Sideways Market Deleverage"
                                               [(weight-equal
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])])]
                                             [(weight-equal
                                               [(if
                                                 (>
                                                  (rsi
                                                   "TLT"
                                                   {:window 10})
                                                  (rsi
                                                   "SQQQ"
                                                   {:window 10}))
                                                 [(asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")]
                                                 [(asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")])])])])]
                                         [(weight-equal
                                           [(if
                                             (<
                                              (rsi "SQQQ" {:window 10})
                                              31)
                                             [(asset
                                               "SQQQ"
                                               "ProShares UltraPro Short QQQ")]
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 70})
                                                  -15)
                                                 [(weight-equal
                                                   [(filter
                                                     (rsi {:window 10})
                                                     (select-top 1)
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")
                                                      (asset
                                                       "SOXL"
                                                       "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                                 [(weight-equal
                                                   [(filter
                                                     (cumulative-return
                                                      {:window 15})
                                                     (select-top 2)
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")
                                                      (asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")
                                                      (asset
                                                       "DIA"
                                                       "SPDR Dow Jones Industrial Average ETF Trust")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])])])])
                (group
                 "7e TQQQ FTLT V4.2.5a + Sideways Market Deleverage | No K-1 | BT 04/17/2019"
                 [(weight-equal
                   [(group
                     "TQQQ For The Long Term V4.2 | BT 04/17/2019"
                     [(weight-equal
                       [(if
                         (>
                          (current-price "SPY")
                          (moving-average-price "SPY" {:window 200}))
                         [(weight-equal
                           [(if
                             (> (rsi "TQQQ" {:window 14}) 75)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(weight-equal
                               [(if
                                 (> (rsi "SPXL" {:window 10}) 80)
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")]
                                 [(group
                                   "A Better \"Buy the Dips Nasdaq\" by Garen Phillips"
                                   [(weight-equal
                                     [(if
                                       (<
                                        (cumulative-return
                                         "QQQ"
                                         {:window 5})
                                        -6)
                                       [(weight-equal
                                         [(if
                                           (>
                                            (cumulative-return
                                             "TQQQ"
                                             {:window 1})
                                            5)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (rsi
                                                 "TQQQ"
                                                 {:window 10})
                                                20)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "QQQ" {:window 10})
                                            80)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "QQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")]
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust Series I")])])])])])])])])])])])]
                         [(weight-equal
                           [(if
                             (<=
                              (cumulative-return "QQQ" {:window 60})
                              -20)
                             [(group
                               "Sideways Market Deleverage"
                               [(weight-equal
                                 [(if
                                   (>=
                                    (cumulative-return
                                     "UUP"
                                     {:window 2})
                                    1)
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "TLT"
                                         {:window 1})
                                        0)
                                       [(weight-equal
                                         [(filter
                                           (rsi {:window 5})
                                           (select-bottom 3)
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")
                                            (asset
                                             "SOXL"
                                             "Direxion Daily Semiconductor Bull 3x Shares")
                                            (asset
                                             "BIL"
                                             "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                            (asset
                                             "EWZ"
                                             "iShares MSCI Brazil ETF")
                                            (asset
                                             "UPRO"
                                             "ProShares UltraPro S&P500")
                                            (asset
                                             "QQQ"
                                             "Invesco QQQ Trust")
                                            (asset
                                             "TECL"
                                             "Direxion Daily Technology Bull 3x Shares")
                                            (asset
                                             "SPY"
                                             "SPDR S&P 500 ETF Trust")
                                            (asset
                                             "TNA"
                                             "Direxion Daily Small Cap Bull 3x Shares")
                                            (asset
                                             "XOP"
                                             "SPDR Series Trust - SPDR Oil & Gas Exploration and Production ETF")])])]
                                       [(weight-equal
                                         [(filter
                                           (rsi {:window 5})
                                           (select-bottom 3)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")
                                            (asset
                                             "SOXS"
                                             "Direxion Daily Semiconductor Bear 3x Shares")
                                            (asset
                                             "BIL"
                                             "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                            (asset
                                             "SH"
                                             "ProShares Short S&P500")
                                            (asset
                                             "PSQ"
                                             "ProShares Short QQQ")
                                            (asset
                                             "TECS"
                                             "Direxion Daily Technology Bear 3X Shares")
                                            (asset
                                             "TZA"
                                             "Direxion Daily Small Cap Bear 3x Shares")
                                            (asset
                                             "DUG"
                                             "ProShares Trust - ProShares UltraShort Energy")])])])])]
                                   [(weight-equal
                                     [(if
                                       (>=
                                        (current-price "SPY")
                                        (moving-average-price
                                         "SPY"
                                         {:window 3}))
                                       [(weight-equal
                                         [(filter
                                           (rsi {:window 5})
                                           (select-bottom 3)
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")
                                            (asset
                                             "SOXL"
                                             "Direxion Daily Semiconductor Bull 3x Shares")
                                            (asset
                                             "BIL"
                                             "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                            (asset
                                             "EWZ"
                                             "iShares MSCI Brazil ETF")
                                            (asset
                                             "UPRO"
                                             "ProShares UltraPro S&P500")
                                            (asset
                                             "QQQ"
                                             "Invesco QQQ Trust")
                                            (asset
                                             "TECL"
                                             "Direxion Daily Technology Bull 3x Shares")
                                            (asset
                                             "SPY"
                                             "SPDR S&P 500 ETF Trust")
                                            (asset
                                             "TNA"
                                             "Direxion Daily Small Cap Bull 3x Shares")])])]
                                       [(asset
                                         "BSV"
                                         "Vanguard Short-Term Bond ETF")
                                        (asset
                                         "TLT"
                                         "iShares 20+ Year Treasury Bond ETF")])])])])])]
                             [(weight-equal
                               [(if
                                 (< (rsi "TQQQ" {:window 9}) 32)
                                 [(weight-equal
                                   [(if
                                     (>=
                                      (cumulative-return
                                       "TQQQ"
                                       {:window 2})
                                      (cumulative-return
                                       "TQQQ"
                                       {:window 5}))
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 10})
                                         (select-bottom 1)
                                         [(asset
                                           "TECL"
                                           "Direxion Daily Technology Bull 3x Shares")
                                          (asset
                                           "SOXL"
                                           "Direxion Daily Semiconductor Bull 3x Shares")
                                          (asset
                                           "SHY"
                                           "iShares 1-3 Year Treasury Bond ETF")])
                                        (filter
                                         (rsi {:window 5})
                                         (select-bottom 1)
                                         [(asset
                                           "SOXL"
                                           "Direxion Daily Semiconductor Bull 3x Shares")
                                          (asset
                                           "SHY"
                                           "iShares 1-3 Year Treasury Bond ETF")])])]
                                     [(weight-equal
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SPY" {:window 10})
                                            30)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-bottom 1)
                                               [(asset
                                                 "SPXL"
                                                 "Direxion Daily S&P 500 Bull 3x Shares")
                                                (asset
                                                 "SHY"
                                                 "iShares 1-3 Year Treasury Bond ETF")])])]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (rsi
                                                 "UVXY"
                                                 {:window 10})
                                                74)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "UVXY"
                                                     {:window 10})
                                                    84)
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "BSV"
                                                         "Vanguard Short-Term Bond ETF")
                                                        (asset
                                                         "SOXS"
                                                         "Direxion Daily Semiconductor Bear 3x Shares")])])]
                                                   [(asset
                                                     "UVXY"
                                                     "ProShares Ultra VIX Short-Term Futures ETF")])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (current-price
                                                     "TQQQ")
                                                    (moving-average-price
                                                     "TQQQ"
                                                     {:window 20}))
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (rsi
                                                         "SQQQ"
                                                         {:window 10})
                                                        31)
                                                       [(asset
                                                         "SQQQ"
                                                         "ProShares UltraPro Short QQQ")]
                                                       [(asset
                                                         "SOXL"
                                                         "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "BSV"
                                                         "Vanguard Short-Term Bond ETF")
                                                        (asset
                                                         "SOXS"
                                                         "Direxion Daily Semiconductor Bear 3x Shares")])])])])])])])])])])])]
                                 [(weight-equal
                                   [(if
                                     (< (rsi "SPY" {:window 10}) 30)
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 10})
                                         (select-bottom 1)
                                         [(asset
                                           "SPXL"
                                           "Direxion Daily S&P 500 Bull 3x Shares")
                                          (asset
                                           "SHY"
                                           "iShares 1-3 Year Treasury Bond ETF")])])]
                                     [(weight-equal
                                       [(if
                                         (>
                                          (rsi "UVXY" {:window 10})
                                          74)
                                         [(weight-equal
                                           [(if
                                             (>
                                              (rsi "UVXY" {:window 10})
                                              84)
                                             [(weight-equal
                                               [(filter
                                                 (rsi {:window 10})
                                                 (select-top 1)
                                                 [(asset
                                                   "BSV"
                                                   "Vanguard Short-Term Bond ETF")
                                                  (asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")])])]
                                             [(asset
                                               "UVXY"
                                               "ProShares Ultra VIX Short-Term Futures ETF")])])]
                                         [(weight-equal
                                           [(if
                                             (>
                                              (current-price "TQQQ")
                                              (moving-average-price
                                               "TQQQ"
                                               {:window 20}))
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (rsi
                                                   "SQQQ"
                                                   {:window 10})
                                                  31)
                                                 [(asset
                                                   "SOXS"
                                                   "Direxion Daily Semiconductor Bear 3x Shares")]
                                                 [(asset
                                                   "SOXL"
                                                   "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                             [(weight-equal
                                               [(filter
                                                 (rsi {:window 10})
                                                 (select-top 1)
                                                 [(asset
                                                   "BSV"
                                                   "Vanguard Short-Term Bond ETF")
                                                  (asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")])])])])])])])])])])])])])])])])])])])])
          (group
           "TQQQ FTLT | Full Package | 20d StDev | Bottom 2 | Shorter Backtest"
           [(weight-equal
             [(filter
               (stdev-return {:window 20})
               (select-top 2)
               [(group
                 "TQQQ For The Long Term 'Original' (longer backtest)"
                 [(weight-equal
                   [(if
                     (>
                      (current-price "SPY")
                      (moving-average-price "SPY" {:window 200}))
                     [(weight-equal
                       [(group
                         "Bull Market"
                         [(weight-equal
                           [(if
                             (> (rsi "QQQ" {:window 10}) 80)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(weight-equal
                               [(if
                                 (> (rsi "SPY" {:window 10}) 80)
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")]
                                 [(weight-equal
                                   [(if
                                     (> (rsi "SPY" {:window 60}) 60)
                                     [(weight-equal
                                       [(filter
                                         (moving-average-return
                                          {:window 15})
                                         (select-top 1)
                                         [(asset
                                           "TMF"
                                           "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                          (asset
                                           "UUP"
                                           "Invesco DB US Dollar Index Bullish Fund")
                                          (asset
                                           "VIXY"
                                           "ProShares VIX Short-Term Futures ETF")
                                          (asset
                                           "XLP"
                                           "Consumer Staples Select Sector SPDR Fund")
                                          (asset
                                           "SPLV"
                                           "Invesco S&P 500 Low Volatility ETF")
                                          (asset
                                           "BTAL"
                                           "AGF U.S. Market Neutral Anti-Beta Fund")])])]
                                     [(weight-specified
                                       0.67
                                       (filter
                                        (moving-average-return
                                         {:window 21})
                                        (select-top 3)
                                        [(asset
                                          "TQQQ"
                                          "ProShares UltraPro QQQ")
                                         (asset
                                          "SOXL"
                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                         (asset
                                          "TECL"
                                          "Direxion Daily Technology Bull 3x Shares")
                                         (asset
                                          "UDOW"
                                          "ProShares UltraPro Dow30")
                                         (asset
                                          "UPRO"
                                          "ProShares UltraPro S&P500")
                                         (asset
                                          "ROM"
                                          "ProShares Ultra Technology")
                                         (asset
                                          "QLD"
                                          "ProShares Ultra QQQ")
                                         (asset
                                          "SSO"
                                          "ProShares Ultra S&P 500")
                                         (asset
                                          "URTY"
                                          "ProShares UltraPro Russell2000")])
                                       0.33
                                       (asset
                                        "SVXY"
                                        "ProShares Short VIX Short-Term Futures ETF"))])])])])])])])])]
                     [(weight-equal
                       [(group
                         "Modified Dip Buy Strategy"
                         [(weight-equal
                           [(if
                             (< (rsi "TECL" {:window 10}) 30)
                             [(asset
                               "TECL"
                               "Direxion Daily Technology Bull 3x Shares")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])
                            (if
                             (< (rsi "SOXL" {:window 10}) 30)
                             [(asset
                               "SOXL"
                               "Direxion Daily Semiconductor Bull 3x Shares")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])
                            (if
                             (< (rsi "TQQQ" {:window 10}) 30)
                             [(asset "TQQQ" "ProShares UltraPro QQQ")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])
                            (if
                             (< (rsi "UPRO" {:window 10}) 30)
                             [(asset
                               "UPRO"
                               "ProShares UltraPro S&P500")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])
                            (if
                             (< (rsi "URTY" {:window 10}) 30)
                             [(asset
                               "URTY"
                               "ProShares UltraPro Russell2000")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])
                (group
                 "TQQQ For The Long Term (Reddit Post Link)"
                 [(weight-equal
                   [(if
                     (>
                      (current-price "SPY")
                      (moving-average-price "SPY" {:window 200}))
                     [(weight-equal
                       [(if
                         (> (rsi "TQQQ" {:window 10}) 79)
                         [(asset
                           "UVXY"
                           "ProShares Ultra VIX Short-Term Futures ETF")]
                         [(weight-equal
                           [(if
                             (> (rsi "SPXL" {:window 10}) 80)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(weight-equal
                               [(asset
                                 "TQQQ"
                                 "ProShares UltraPro QQQ")])])])])])]
                     [(weight-equal
                       [(if
                         (< (rsi "TQQQ" {:window 10}) 31)
                         [(asset
                           "TECL"
                           "Direxion Daily Technology Bull 3x Shares")]
                         [(weight-equal
                           [(if
                             (< (rsi "SPY" {:window 10}) 30)
                             [(asset
                               "UPRO"
                               "ProShares UltraPro S&P500")]
                             [(weight-equal
                               [(if
                                 (<
                                  (current-price "TQQQ")
                                  (moving-average-price
                                   "TQQQ"
                                   {:window 20}))
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
                                 [(weight-equal
                                   [(if
                                     (< (rsi "SQQQ" {:window 10}) 31)
                                     [(asset
                                       "SQQQ"
                                       "ProShares UltraPro Short QQQ")]
                                     [(asset
                                       "TQQQ"
                                       "ProShares UltraPro QQQ")])])])])])])])])])])])
                (group
                 "TQQQ For The Long Term V2"
                 [(weight-equal
                   [(if
                     (>
                      (current-price "SPY")
                      (moving-average-price "SPY" {:window 200}))
                     [(weight-equal
                       [(if
                         (> (rsi "TQQQ" {:window 10}) 79)
                         [(asset
                           "UVXY"
                           "ProShares Ultra VIX Short-Term Futures ETF")]
                         [(weight-equal
                           [(if
                             (> (rsi "SPXL" {:window 10}) 80)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(asset
                               "TQQQ"
                               "ProShares UltraPro QQQ")])])])])]
                     [(weight-equal
                       [(if
                         (< (rsi "TQQQ" {:window 10}) 31)
                         [(asset
                           "TECL"
                           "Direxion Daily Technology Bull 3x Shares")]
                         [(weight-equal
                           [(if
                             (< (rsi "SPY" {:window 10}) 30)
                             [(asset
                               "SPXL"
                               "Direxion Daily S&P 500 Bull 3x Shares")]
                             [(weight-equal
                               [(if
                                 (> (rsi "UVXY" {:window 10}) 74)
                                 [(weight-equal
                                   [(if
                                     (> (rsi "UVXY" {:window 10}) 84)
                                     [(weight-equal
                                       [(if
                                         (>
                                          (current-price "TQQQ")
                                          (moving-average-price
                                           "TQQQ"
                                           {:window 20}))
                                         [(asset
                                           "TQQQ"
                                           "ProShares UltraPro QQQ")]
                                         [(weight-equal
                                           [(filter
                                             (rsi {:window 10})
                                             (select-top 1)
                                             [(asset
                                               "SQQQ"
                                               "ProShares UltraPro Short QQQ")
                                              (asset
                                               "BSV"
                                               "Vanguard Short-Term Bond ETF")])])])])]
                                     [(asset
                                       "UVXY"
                                       "ProShares Ultra VIX Short-Term Futures ETF")])])]
                                 [(weight-equal
                                   [(if
                                     (>
                                      (current-price "TQQQ")
                                      (moving-average-price
                                       "TQQQ"
                                       {:window 20}))
                                     [(asset
                                       "TQQQ"
                                       "ProShares UltraPro QQQ")]
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 10})
                                         (select-top 1)
                                         [(asset
                                           "SQQQ"
                                           "ProShares UltraPro Short QQQ")
                                          (asset
                                           "BSV"
                                           "Vanguard Short-Term Bond ETF")])])])])])])])])])])])])])
                (group
                 "TQQQ FTLT w/Sideways Market Mods"
                 [(weight-equal
                   [(if
                     (>
                      (current-price "SPY")
                      (moving-average-price "SPY" {:window 200}))
                     [(weight-equal
                       [(if
                         (> (rsi "TQQQ" {:window 10}) 79)
                         [(asset
                           "UVXY"
                           "ProShares Ultra VIX Short-Term Futures ETF")]
                         [(weight-equal
                           [(if
                             (> (rsi "SPXL" {:window 10}) 80)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(weight-equal
                               [(if
                                 (>
                                  (cumulative-return
                                   "TQQQ"
                                   {:window 5})
                                  20)
                                 [(weight-equal
                                   [(if
                                     (< (rsi "TQQQ" {:window 10}) 31)
                                     [(asset
                                       "TQQQ"
                                       "ProShares UltraPro QQQ")]
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 10})
                                         (select-top 1)
                                         [(asset
                                           "UVXY"
                                           "ProShares Ultra VIX Short-Term Futures ETF")
                                          (asset
                                           "SQQQ"
                                           "ProShares UltraPro Short QQQ")])])])])]
                                 [(weight-equal
                                   [(asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])])])])])])])]
                     [(weight-equal
                       [(if
                         (< (rsi "TQQQ" {:window 10}) 31)
                         [(asset
                           "TECL"
                           "Direxion Daily Technology Bull 3x Shares")]
                         [(weight-equal
                           [(if
                             (< (rsi "SMH" {:window 10}) 30)
                             [(asset
                               "SOXL"
                               "Direxion Daily Semiconductor Bull 3x Shares")]
                             [(weight-equal
                               [(if
                                 (< (rsi "DIA" {:window 10}) 27)
                                 [(asset
                                   "UDOW"
                                   "ProShares UltraPro Dow30")]
                                 [(weight-equal
                                   [(if
                                     (< (rsi "SPY" {:window 14}) 28)
                                     [(asset
                                       "UPRO"
                                       "ProShares UltraPro S&P500")]
                                     [(weight-equal
                                       [(if
                                         (<
                                          (cumulative-return
                                           "QQQ"
                                           {:window 200})
                                          -20)
                                         [(weight-equal
                                           [(group
                                             "Nasdaq In Crash Territory, Time to Deleverage"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (current-price "QQQ")
                                                  (moving-average-price
                                                   "QQQ"
                                                   {:window 20}))
                                                 [(weight-equal
                                                   [(if
                                                     (<=
                                                      (cumulative-return
                                                       "QQQ"
                                                       {:window 60})
                                                      -12)
                                                     [(group
                                                       "Sideways Market Deleverage"
                                                       [(weight-equal
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (current-price
                                                               "SPY")
                                                              (moving-average-price
                                                               "SPY"
                                                               {:window
                                                                20}))
                                                             [(asset
                                                               "SPY"
                                                               "SPDR S&P 500 ETF Trust")]
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (rsi
                                                                   "TLT"
                                                                   {:window
                                                                    10})
                                                                  (rsi
                                                                   "SQQQ"
                                                                   {:window
                                                                    10}))
                                                                 [(asset
                                                                   "QQQ"
                                                                   "Invesco QQQ Trust")]
                                                                 [(asset
                                                                   "PSQ"
                                                                   "ProShares Short QQQ")])])])
                                                            (if
                                                             (>
                                                              (rsi
                                                               "TLT"
                                                               {:window
                                                                10})
                                                              (rsi
                                                               "SQQQ"
                                                               {:window
                                                                10}))
                                                             [(asset
                                                               "QQQ"
                                                               "Invesco QQQ Trust")]
                                                             [(asset
                                                               "PSQ"
                                                               "ProShares Short QQQ")])])])])]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "TQQQ"
                                                           "ProShares UltraPro QQQ")]
                                                         [(asset
                                                           "SQQQ"
                                                           "ProShares UltraPro Short QQQ")])])])])]
                                                 [(weight-equal
                                                   [(if
                                                     (<
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10})
                                                      31)
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (cumulative-return
                                                           "QQQ"
                                                           {:window
                                                            10})
                                                          5.5)
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")]
                                                         [(weight-equal
                                                           [(filter
                                                             (rsi
                                                              {:window
                                                               10})
                                                             (select-top
                                                              1)
                                                             [(asset
                                                               "QQQ"
                                                               "Invesco QQQ Trust")
                                                              (asset
                                                               "SMH"
                                                               "VanEck Semiconductor ETF")])])])])])])])])])])]
                                         [(weight-equal
                                           [(if
                                             (<
                                              (current-price "QQQ")
                                              (moving-average-price
                                               "QQQ"
                                               {:window 20}))
                                             [(weight-equal
                                               [(if
                                                 (>
                                                  (rsi
                                                   "TLT"
                                                   {:window 10})
                                                  (rsi
                                                   "SQQQ"
                                                   {:window 10}))
                                                 [(asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")]
                                                 [(asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")])])]
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (rsi
                                                   "SQQQ"
                                                   {:window 10})
                                                  31)
                                                 [(asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")]
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "QQQ"
                                                       {:window 10})
                                                      5.5)
                                                     [(asset
                                                       "SQQQ"
                                                       "ProShares UltraPro Short QQQ")]
                                                     [(weight-equal
                                                       [(filter
                                                         (rsi
                                                          {:window 10})
                                                         (select-top 1)
                                                         [(asset
                                                           "TQQQ"
                                                           "ProShares UltraPro QQQ")
                                                          (asset
                                                           "SOXL"
                                                           "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                        (if
                                         (<
                                          (current-price "QQQ")
                                          (moving-average-price
                                           "QQQ"
                                           {:window 20}))
                                         [(weight-equal
                                           [(if
                                             (<=
                                              (cumulative-return
                                               "QQQ"
                                               {:window 60})
                                              -12)
                                             [(group
                                               "Sideways Market Deleverage"
                                               [(weight-equal
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])])]
                                             [(weight-equal
                                               [(if
                                                 (>
                                                  (rsi
                                                   "TLT"
                                                   {:window 10})
                                                  (rsi
                                                   "SQQQ"
                                                   {:window 10}))
                                                 [(asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")]
                                                 [(asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")])])])])]
                                         [(weight-equal
                                           [(if
                                             (<
                                              (rsi "SQQQ" {:window 10})
                                              31)
                                             [(asset
                                               "SQQQ"
                                               "ProShares UltraPro Short QQQ")]
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 70})
                                                  -15)
                                                 [(weight-equal
                                                   [(filter
                                                     (rsi {:window 10})
                                                     (select-top 1)
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")
                                                      (asset
                                                       "SOXL"
                                                       "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                                 [(weight-equal
                                                   [(filter
                                                     (cumulative-return
                                                      {:window 15})
                                                     (select-top 2)
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")
                                                      (asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")
                                                      (asset
                                                       "DIA"
                                                       "SPDR Dow Jones Industrial Average ETF Trust")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])])])])
                (group
                 "7e TQQQ FTLT V4.2.5a + Sideways Market Deleverage | No K-1 | BT 04/17/2019"
                 [(weight-equal
                   [(group
                     "TQQQ For The Long Term V4.2 | BT 04/17/2019"
                     [(weight-equal
                       [(if
                         (>
                          (current-price "SPY")
                          (moving-average-price "SPY" {:window 200}))
                         [(weight-equal
                           [(if
                             (> (rsi "TQQQ" {:window 14}) 75)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(weight-equal
                               [(if
                                 (> (rsi "SPXL" {:window 10}) 80)
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")]
                                 [(group
                                   "A Better \"Buy the Dips Nasdaq\" by Garen Phillips"
                                   [(weight-equal
                                     [(if
                                       (<
                                        (cumulative-return
                                         "QQQ"
                                         {:window 5})
                                        -6)
                                       [(weight-equal
                                         [(if
                                           (>
                                            (cumulative-return
                                             "TQQQ"
                                             {:window 1})
                                            5)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (rsi
                                                 "TQQQ"
                                                 {:window 10})
                                                20)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "QQQ" {:window 10})
                                            80)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "QQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")]
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust Series I")])])])])])])])])])])])]
                         [(weight-equal
                           [(if
                             (<=
                              (cumulative-return "QQQ" {:window 60})
                              -20)
                             [(group
                               "Sideways Market Deleverage"
                               [(weight-equal
                                 [(if
                                   (>=
                                    (cumulative-return
                                     "UUP"
                                     {:window 2})
                                    1)
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "TLT"
                                         {:window 1})
                                        0)
                                       [(weight-equal
                                         [(filter
                                           (rsi {:window 5})
                                           (select-bottom 3)
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")
                                            (asset
                                             "SOXL"
                                             "Direxion Daily Semiconductor Bull 3x Shares")
                                            (asset
                                             "BIL"
                                             "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                            (asset
                                             "EWZ"
                                             "iShares MSCI Brazil ETF")
                                            (asset
                                             "UPRO"
                                             "ProShares UltraPro S&P500")
                                            (asset
                                             "QQQ"
                                             "Invesco QQQ Trust")
                                            (asset
                                             "TECL"
                                             "Direxion Daily Technology Bull 3x Shares")
                                            (asset
                                             "SPY"
                                             "SPDR S&P 500 ETF Trust")
                                            (asset
                                             "TNA"
                                             "Direxion Daily Small Cap Bull 3x Shares")
                                            (asset
                                             "XOP"
                                             "SPDR Series Trust - SPDR Oil & Gas Exploration and Production ETF")])])]
                                       [(weight-equal
                                         [(filter
                                           (rsi {:window 5})
                                           (select-bottom 3)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")
                                            (asset
                                             "SOXS"
                                             "Direxion Daily Semiconductor Bear 3x Shares")
                                            (asset
                                             "BIL"
                                             "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                            (asset
                                             "SH"
                                             "ProShares Short S&P500")
                                            (asset
                                             "PSQ"
                                             "ProShares Short QQQ")
                                            (asset
                                             "TECS"
                                             "Direxion Daily Technology Bear 3X Shares")
                                            (asset
                                             "TZA"
                                             "Direxion Daily Small Cap Bear 3x Shares")
                                            (asset
                                             "DUG"
                                             "ProShares Trust - ProShares UltraShort Energy")])])])])]
                                   [(weight-equal
                                     [(if
                                       (>=
                                        (current-price "SPY")
                                        (moving-average-price
                                         "SPY"
                                         {:window 3}))
                                       [(weight-equal
                                         [(filter
                                           (rsi {:window 5})
                                           (select-bottom 3)
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")
                                            (asset
                                             "SOXL"
                                             "Direxion Daily Semiconductor Bull 3x Shares")
                                            (asset
                                             "BIL"
                                             "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                            (asset
                                             "EWZ"
                                             "iShares MSCI Brazil ETF")
                                            (asset
                                             "UPRO"
                                             "ProShares UltraPro S&P500")
                                            (asset
                                             "QQQ"
                                             "Invesco QQQ Trust")
                                            (asset
                                             "TECL"
                                             "Direxion Daily Technology Bull 3x Shares")
                                            (asset
                                             "SPY"
                                             "SPDR S&P 500 ETF Trust")
                                            (asset
                                             "TNA"
                                             "Direxion Daily Small Cap Bull 3x Shares")])])]
                                       [(asset
                                         "BSV"
                                         "Vanguard Short-Term Bond ETF")
                                        (asset
                                         "TLT"
                                         "iShares 20+ Year Treasury Bond ETF")])])])])])]
                             [(weight-equal
                               [(if
                                 (< (rsi "TQQQ" {:window 9}) 32)
                                 [(weight-equal
                                   [(if
                                     (>=
                                      (cumulative-return
                                       "TQQQ"
                                       {:window 2})
                                      (cumulative-return
                                       "TQQQ"
                                       {:window 5}))
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 10})
                                         (select-bottom 1)
                                         [(asset
                                           "TECL"
                                           "Direxion Daily Technology Bull 3x Shares")
                                          (asset
                                           "SOXL"
                                           "Direxion Daily Semiconductor Bull 3x Shares")
                                          (asset
                                           "SHY"
                                           "iShares 1-3 Year Treasury Bond ETF")])
                                        (filter
                                         (rsi {:window 5})
                                         (select-bottom 1)
                                         [(asset
                                           "SOXL"
                                           "Direxion Daily Semiconductor Bull 3x Shares")
                                          (asset
                                           "SHY"
                                           "iShares 1-3 Year Treasury Bond ETF")])])]
                                     [(weight-equal
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SPY" {:window 10})
                                            30)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-bottom 1)
                                               [(asset
                                                 "SPXL"
                                                 "Direxion Daily S&P 500 Bull 3x Shares")
                                                (asset
                                                 "SHY"
                                                 "iShares 1-3 Year Treasury Bond ETF")])])]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (rsi
                                                 "UVXY"
                                                 {:window 10})
                                                74)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "UVXY"
                                                     {:window 10})
                                                    84)
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "BSV"
                                                         "Vanguard Short-Term Bond ETF")
                                                        (asset
                                                         "SOXS"
                                                         "Direxion Daily Semiconductor Bear 3x Shares")])])]
                                                   [(asset
                                                     "UVXY"
                                                     "ProShares Ultra VIX Short-Term Futures ETF")])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (current-price
                                                     "TQQQ")
                                                    (moving-average-price
                                                     "TQQQ"
                                                     {:window 20}))
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (rsi
                                                         "SQQQ"
                                                         {:window 10})
                                                        31)
                                                       [(asset
                                                         "SQQQ"
                                                         "ProShares UltraPro Short QQQ")]
                                                       [(asset
                                                         "SOXL"
                                                         "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "BSV"
                                                         "Vanguard Short-Term Bond ETF")
                                                        (asset
                                                         "SOXS"
                                                         "Direxion Daily Semiconductor Bear 3x Shares")])])])])])])])])])])])]
                                 [(weight-equal
                                   [(if
                                     (< (rsi "SPY" {:window 10}) 30)
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 10})
                                         (select-bottom 1)
                                         [(asset
                                           "SPXL"
                                           "Direxion Daily S&P 500 Bull 3x Shares")
                                          (asset
                                           "SHY"
                                           "iShares 1-3 Year Treasury Bond ETF")])])]
                                     [(weight-equal
                                       [(if
                                         (>
                                          (rsi "UVXY" {:window 10})
                                          74)
                                         [(weight-equal
                                           [(if
                                             (>
                                              (rsi "UVXY" {:window 10})
                                              84)
                                             [(weight-equal
                                               [(filter
                                                 (rsi {:window 10})
                                                 (select-top 1)
                                                 [(asset
                                                   "BSV"
                                                   "Vanguard Short-Term Bond ETF")
                                                  (asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")])])]
                                             [(asset
                                               "UVXY"
                                               "ProShares Ultra VIX Short-Term Futures ETF")])])]
                                         [(weight-equal
                                           [(if
                                             (>
                                              (current-price "TQQQ")
                                              (moving-average-price
                                               "TQQQ"
                                               {:window 20}))
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (rsi
                                                   "SQQQ"
                                                   {:window 10})
                                                  31)
                                                 [(asset
                                                   "SOXS"
                                                   "Direxion Daily Semiconductor Bear 3x Shares")]
                                                 [(asset
                                                   "SOXL"
                                                   "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                             [(weight-equal
                                               [(filter
                                                 (rsi {:window 10})
                                                 (select-top 1)
                                                 [(asset
                                                   "BSV"
                                                   "Vanguard Short-Term Bond ETF")
                                                  (asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")])])])])])])])])])])])])])])])])])])])])
          (group
           "TQQQ FTLT | Full Package | 20d CR | Top 3 | Shorter Backtest"
           [(weight-equal
             [(filter
               (cumulative-return {:window 10})
               (select-top 3)
               [(group
                 "TQQQ For The Long Term 'Original' (longer backtest)"
                 [(weight-equal
                   [(if
                     (>
                      (current-price "SPY")
                      (moving-average-price "SPY" {:window 200}))
                     [(weight-equal
                       [(group
                         "Bull Market"
                         [(weight-equal
                           [(if
                             (> (rsi "QQQ" {:window 10}) 80)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(weight-equal
                               [(if
                                 (> (rsi "SPY" {:window 10}) 80)
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")]
                                 [(weight-equal
                                   [(if
                                     (> (rsi "SPY" {:window 60}) 60)
                                     [(weight-equal
                                       [(filter
                                         (moving-average-return
                                          {:window 15})
                                         (select-top 1)
                                         [(asset
                                           "TMF"
                                           "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                          (asset
                                           "UUP"
                                           "Invesco DB US Dollar Index Bullish Fund")
                                          (asset
                                           "VIXY"
                                           "ProShares VIX Short-Term Futures ETF")
                                          (asset
                                           "XLP"
                                           "Consumer Staples Select Sector SPDR Fund")
                                          (asset
                                           "SPLV"
                                           "Invesco S&P 500 Low Volatility ETF")
                                          (asset
                                           "BTAL"
                                           "AGF U.S. Market Neutral Anti-Beta Fund")])])]
                                     [(weight-specified
                                       0.67
                                       (filter
                                        (moving-average-return
                                         {:window 21})
                                        (select-top 3)
                                        [(asset
                                          "TQQQ"
                                          "ProShares UltraPro QQQ")
                                         (asset
                                          "SOXL"
                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                         (asset
                                          "TECL"
                                          "Direxion Daily Technology Bull 3x Shares")
                                         (asset
                                          "UDOW"
                                          "ProShares UltraPro Dow30")
                                         (asset
                                          "UPRO"
                                          "ProShares UltraPro S&P500")
                                         (asset
                                          "ROM"
                                          "ProShares Ultra Technology")
                                         (asset
                                          "QLD"
                                          "ProShares Ultra QQQ")
                                         (asset
                                          "SSO"
                                          "ProShares Ultra S&P 500")
                                         (asset
                                          "URTY"
                                          "ProShares UltraPro Russell2000")])
                                       0.33
                                       (asset
                                        "SVXY"
                                        "ProShares Short VIX Short-Term Futures ETF"))])])])])])])])])]
                     [(weight-equal
                       [(group
                         "Modified Dip Buy Strategy"
                         [(weight-equal
                           [(if
                             (< (rsi "TECL" {:window 10}) 30)
                             [(asset
                               "TECL"
                               "Direxion Daily Technology Bull 3x Shares")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])
                            (if
                             (< (rsi "SOXL" {:window 10}) 30)
                             [(asset
                               "SOXL"
                               "Direxion Daily Semiconductor Bull 3x Shares")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])
                            (if
                             (< (rsi "TQQQ" {:window 10}) 30)
                             [(asset "TQQQ" "ProShares UltraPro QQQ")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])
                            (if
                             (< (rsi "UPRO" {:window 10}) 30)
                             [(asset
                               "UPRO"
                               "ProShares UltraPro S&P500")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])
                            (if
                             (< (rsi "URTY" {:window 10}) 30)
                             [(asset
                               "URTY"
                               "ProShares UltraPro Russell2000")]
                             [(group
                               "Bear Market Sideways Protection"
                               [(weight-equal
                                 [(if
                                   (<
                                    (cumulative-return
                                     "QQQ"
                                     {:window 252})
                                    -20)
                                   [(weight-equal
                                     [(group
                                       "Nasdaq In Crash Territory, Time to Deleverage"
                                       [(weight-equal
                                         [(if
                                           (<
                                            (current-price "QQQ")
                                            (moving-average-price
                                             "QQQ"
                                             {:window 20}))
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 60})
                                                -12)
                                               [(group
                                                 "Sideways Market Deleverage"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")]
                                                   [(asset
                                                     "SQQQ"
                                                     "ProShares UltraPro Short QQQ")])])])])]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "QQQ"
                                                     {:window 10})
                                                    5.5)
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")]
                                                   [(weight-equal
                                                     [(filter
                                                       (rsi
                                                        {:window 10})
                                                       (select-top 1)
                                                       [(asset
                                                         "QQQ"
                                                         "Invesco QQQ Trust")
                                                        (asset
                                                         "SMH"
                                                         "VanEck Semiconductor ETF")])])])])])])])])])])]
                                   [(weight-equal
                                     [(if
                                       (<
                                        (current-price "QQQ")
                                        (moving-average-price
                                         "QQQ"
                                         {:window 20}))
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "SQQQ" {:window 10})
                                            31)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 10})
                                                5.5)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(weight-equal
                                                 [(filter
                                                   (rsi {:window 10})
                                                   (select-top 1)
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                  (if
                                   (<
                                    (current-price "QQQ")
                                    (moving-average-price
                                     "QQQ"
                                     {:window 20}))
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 60})
                                        -12)
                                       [(group
                                         "Sideways Market Deleverage"
                                         [(weight-equal
                                           [(weight-equal
                                             [(if
                                               (>
                                                (current-price "SPY")
                                                (moving-average-price
                                                 "SPY"
                                                 {:window 20}))
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TLT"
                                                     {:window 10})
                                                    (rsi
                                                     "SQQQ"
                                                     {:window 10}))
                                                   [(asset
                                                     "QQQ"
                                                     "Invesco QQQ Trust")]
                                                   [(asset
                                                     "PSQ"
                                                     "ProShares Short QQQ")])])])
                                              (if
                                               (>
                                                (rsi
                                                 "TLT"
                                                 {:window 10})
                                                (rsi
                                                 "SQQQ"
                                                 {:window 10}))
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")]
                                               [(asset
                                                 "PSQ"
                                                 "ProShares Short QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "TLT" {:window 10})
                                            (rsi "SQQQ" {:window 10}))
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")]
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")])])])])]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "SQQQ" {:window 10}) 31)
                                       [(asset
                                         "SQQQ"
                                         "ProShares UltraPro Short QQQ")]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (cumulative-return
                                             "QQQ"
                                             {:window 70})
                                            -15)
                                           [(weight-equal
                                             [(filter
                                               (rsi {:window 10})
                                               (select-top 1)
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 15})
                                               (select-top 2)
                                               [(asset
                                                 "SPY"
                                                 "SPDR S&P 500 ETF Trust")
                                                (asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust")
                                                (asset
                                                 "DIA"
                                                 "SPDR Dow Jones Industrial Average ETF Trust")
                                                (asset
                                                 "XLP"
                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])
                (group
                 "TQQQ For The Long Term (Reddit Post Link)"
                 [(weight-equal
                   [(if
                     (>
                      (current-price "SPY")
                      (moving-average-price "SPY" {:window 200}))
                     [(weight-equal
                       [(if
                         (> (rsi "TQQQ" {:window 10}) 79)
                         [(asset
                           "UVXY"
                           "ProShares Ultra VIX Short-Term Futures ETF")]
                         [(weight-equal
                           [(if
                             (> (rsi "SPXL" {:window 10}) 80)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(weight-equal
                               [(asset
                                 "TQQQ"
                                 "ProShares UltraPro QQQ")])])])])])]
                     [(weight-equal
                       [(if
                         (< (rsi "TQQQ" {:window 10}) 31)
                         [(asset
                           "TECL"
                           "Direxion Daily Technology Bull 3x Shares")]
                         [(weight-equal
                           [(if
                             (< (rsi "SPY" {:window 10}) 30)
                             [(asset
                               "UPRO"
                               "ProShares UltraPro S&P500")]
                             [(weight-equal
                               [(if
                                 (<
                                  (current-price "TQQQ")
                                  (moving-average-price
                                   "TQQQ"
                                   {:window 20}))
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
                                 [(weight-equal
                                   [(if
                                     (< (rsi "SQQQ" {:window 10}) 31)
                                     [(asset
                                       "SQQQ"
                                       "ProShares UltraPro Short QQQ")]
                                     [(asset
                                       "TQQQ"
                                       "ProShares UltraPro QQQ")])])])])])])])])])])])
                (group
                 "TQQQ For The Long Term V2"
                 [(weight-equal
                   [(if
                     (>
                      (current-price "SPY")
                      (moving-average-price "SPY" {:window 200}))
                     [(weight-equal
                       [(if
                         (> (rsi "TQQQ" {:window 10}) 79)
                         [(asset
                           "UVXY"
                           "ProShares Ultra VIX Short-Term Futures ETF")]
                         [(weight-equal
                           [(if
                             (> (rsi "SPXL" {:window 10}) 80)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(asset
                               "TQQQ"
                               "ProShares UltraPro QQQ")])])])])]
                     [(weight-equal
                       [(if
                         (< (rsi "TQQQ" {:window 10}) 31)
                         [(asset
                           "TECL"
                           "Direxion Daily Technology Bull 3x Shares")]
                         [(weight-equal
                           [(if
                             (< (rsi "SPY" {:window 10}) 30)
                             [(asset
                               "SPXL"
                               "Direxion Daily S&P 500 Bull 3x Shares")]
                             [(weight-equal
                               [(if
                                 (> (rsi "UVXY" {:window 10}) 74)
                                 [(weight-equal
                                   [(if
                                     (> (rsi "UVXY" {:window 10}) 84)
                                     [(weight-equal
                                       [(if
                                         (>
                                          (current-price "TQQQ")
                                          (moving-average-price
                                           "TQQQ"
                                           {:window 20}))
                                         [(asset
                                           "TQQQ"
                                           "ProShares UltraPro QQQ")]
                                         [(weight-equal
                                           [(filter
                                             (rsi {:window 10})
                                             (select-top 1)
                                             [(asset
                                               "SQQQ"
                                               "ProShares UltraPro Short QQQ")
                                              (asset
                                               "BSV"
                                               "Vanguard Short-Term Bond ETF")])])])])]
                                     [(asset
                                       "UVXY"
                                       "ProShares Ultra VIX Short-Term Futures ETF")])])]
                                 [(weight-equal
                                   [(if
                                     (>
                                      (current-price "TQQQ")
                                      (moving-average-price
                                       "TQQQ"
                                       {:window 20}))
                                     [(asset
                                       "TQQQ"
                                       "ProShares UltraPro QQQ")]
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 10})
                                         (select-top 1)
                                         [(asset
                                           "SQQQ"
                                           "ProShares UltraPro Short QQQ")
                                          (asset
                                           "BSV"
                                           "Vanguard Short-Term Bond ETF")])])])])])])])])])])])])])
                (group
                 "TQQQ FTLT w/Sideways Market Mods"
                 [(weight-equal
                   [(if
                     (>
                      (current-price "SPY")
                      (moving-average-price "SPY" {:window 200}))
                     [(weight-equal
                       [(if
                         (> (rsi "TQQQ" {:window 10}) 79)
                         [(asset
                           "UVXY"
                           "ProShares Ultra VIX Short-Term Futures ETF")]
                         [(weight-equal
                           [(if
                             (> (rsi "SPXL" {:window 10}) 80)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(weight-equal
                               [(if
                                 (>
                                  (cumulative-return
                                   "TQQQ"
                                   {:window 5})
                                  20)
                                 [(weight-equal
                                   [(if
                                     (< (rsi "TQQQ" {:window 10}) 31)
                                     [(asset
                                       "TQQQ"
                                       "ProShares UltraPro QQQ")]
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 10})
                                         (select-top 1)
                                         [(asset
                                           "UVXY"
                                           "ProShares Ultra VIX Short-Term Futures ETF")
                                          (asset
                                           "SQQQ"
                                           "ProShares UltraPro Short QQQ")])])])])]
                                 [(weight-equal
                                   [(asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])])])])])])])]
                     [(weight-equal
                       [(if
                         (< (rsi "TQQQ" {:window 10}) 31)
                         [(asset
                           "TECL"
                           "Direxion Daily Technology Bull 3x Shares")]
                         [(weight-equal
                           [(if
                             (< (rsi "SMH" {:window 10}) 30)
                             [(asset
                               "SOXL"
                               "Direxion Daily Semiconductor Bull 3x Shares")]
                             [(weight-equal
                               [(if
                                 (< (rsi "DIA" {:window 10}) 27)
                                 [(asset
                                   "UDOW"
                                   "ProShares UltraPro Dow30")]
                                 [(weight-equal
                                   [(if
                                     (< (rsi "SPY" {:window 14}) 28)
                                     [(asset
                                       "UPRO"
                                       "ProShares UltraPro S&P500")]
                                     [(weight-equal
                                       [(if
                                         (<
                                          (cumulative-return
                                           "QQQ"
                                           {:window 200})
                                          -20)
                                         [(weight-equal
                                           [(group
                                             "Nasdaq In Crash Territory, Time to Deleverage"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (current-price "QQQ")
                                                  (moving-average-price
                                                   "QQQ"
                                                   {:window 20}))
                                                 [(weight-equal
                                                   [(if
                                                     (<=
                                                      (cumulative-return
                                                       "QQQ"
                                                       {:window 60})
                                                      -12)
                                                     [(group
                                                       "Sideways Market Deleverage"
                                                       [(weight-equal
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (current-price
                                                               "SPY")
                                                              (moving-average-price
                                                               "SPY"
                                                               {:window
                                                                20}))
                                                             [(asset
                                                               "SPY"
                                                               "SPDR S&P 500 ETF Trust")]
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (rsi
                                                                   "TLT"
                                                                   {:window
                                                                    10})
                                                                  (rsi
                                                                   "SQQQ"
                                                                   {:window
                                                                    10}))
                                                                 [(asset
                                                                   "QQQ"
                                                                   "Invesco QQQ Trust")]
                                                                 [(asset
                                                                   "PSQ"
                                                                   "ProShares Short QQQ")])])])
                                                            (if
                                                             (>
                                                              (rsi
                                                               "TLT"
                                                               {:window
                                                                10})
                                                              (rsi
                                                               "SQQQ"
                                                               {:window
                                                                10}))
                                                             [(asset
                                                               "QQQ"
                                                               "Invesco QQQ Trust")]
                                                             [(asset
                                                               "PSQ"
                                                               "ProShares Short QQQ")])])])])]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "TQQQ"
                                                           "ProShares UltraPro QQQ")]
                                                         [(asset
                                                           "SQQQ"
                                                           "ProShares UltraPro Short QQQ")])])])])]
                                                 [(weight-equal
                                                   [(if
                                                     (<
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10})
                                                      31)
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (cumulative-return
                                                           "QQQ"
                                                           {:window
                                                            10})
                                                          5.5)
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")]
                                                         [(weight-equal
                                                           [(filter
                                                             (rsi
                                                              {:window
                                                               10})
                                                             (select-top
                                                              1)
                                                             [(asset
                                                               "QQQ"
                                                               "Invesco QQQ Trust")
                                                              (asset
                                                               "SMH"
                                                               "VanEck Semiconductor ETF")])])])])])])])])])])]
                                         [(weight-equal
                                           [(if
                                             (<
                                              (current-price "QQQ")
                                              (moving-average-price
                                               "QQQ"
                                               {:window 20}))
                                             [(weight-equal
                                               [(if
                                                 (>
                                                  (rsi
                                                   "TLT"
                                                   {:window 10})
                                                  (rsi
                                                   "SQQQ"
                                                   {:window 10}))
                                                 [(asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")]
                                                 [(asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")])])]
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (rsi
                                                   "SQQQ"
                                                   {:window 10})
                                                  31)
                                                 [(asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")]
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "QQQ"
                                                       {:window 10})
                                                      5.5)
                                                     [(asset
                                                       "SQQQ"
                                                       "ProShares UltraPro Short QQQ")]
                                                     [(weight-equal
                                                       [(filter
                                                         (rsi
                                                          {:window 10})
                                                         (select-top 1)
                                                         [(asset
                                                           "TQQQ"
                                                           "ProShares UltraPro QQQ")
                                                          (asset
                                                           "SOXL"
                                                           "Direxion Daily Semiconductor Bull 3x Shares")])])])])])])])])])
                                        (if
                                         (<
                                          (current-price "QQQ")
                                          (moving-average-price
                                           "QQQ"
                                           {:window 20}))
                                         [(weight-equal
                                           [(if
                                             (<=
                                              (cumulative-return
                                               "QQQ"
                                               {:window 60})
                                              -12)
                                             [(group
                                               "Sideways Market Deleverage"
                                               [(weight-equal
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (current-price
                                                       "SPY")
                                                      (moving-average-price
                                                       "SPY"
                                                       {:window 20}))
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")]
                                                     [(weight-equal
                                                       [(if
                                                         (>
                                                          (rsi
                                                           "TLT"
                                                           {:window
                                                            10})
                                                          (rsi
                                                           "SQQQ"
                                                           {:window
                                                            10}))
                                                         [(asset
                                                           "QQQ"
                                                           "Invesco QQQ Trust")]
                                                         [(asset
                                                           "PSQ"
                                                           "ProShares Short QQQ")])])])
                                                    (if
                                                     (>
                                                      (rsi
                                                       "TLT"
                                                       {:window 10})
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10}))
                                                     [(asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")]
                                                     [(asset
                                                       "PSQ"
                                                       "ProShares Short QQQ")])])])])]
                                             [(weight-equal
                                               [(if
                                                 (>
                                                  (rsi
                                                   "TLT"
                                                   {:window 10})
                                                  (rsi
                                                   "SQQQ"
                                                   {:window 10}))
                                                 [(asset
                                                   "TQQQ"
                                                   "ProShares UltraPro QQQ")]
                                                 [(asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")])])])])]
                                         [(weight-equal
                                           [(if
                                             (<
                                              (rsi "SQQQ" {:window 10})
                                              31)
                                             [(asset
                                               "SQQQ"
                                               "ProShares UltraPro Short QQQ")]
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 70})
                                                  -15)
                                                 [(weight-equal
                                                   [(filter
                                                     (rsi {:window 10})
                                                     (select-top 1)
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")
                                                      (asset
                                                       "SOXL"
                                                       "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                                 [(weight-equal
                                                   [(filter
                                                     (cumulative-return
                                                      {:window 15})
                                                     (select-top 2)
                                                     [(asset
                                                       "SPY"
                                                       "SPDR S&P 500 ETF Trust")
                                                      (asset
                                                       "QQQ"
                                                       "Invesco QQQ Trust")
                                                      (asset
                                                       "DIA"
                                                       "SPDR Dow Jones Industrial Average ETF Trust")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])])])])
                (group
                 "7e TQQQ FTLT V4.2.5a + Sideways Market Deleverage | No K-1 | BT 04/17/2019"
                 [(weight-equal
                   [(group
                     "TQQQ For The Long Term V4.2 | BT 04/17/2019"
                     [(weight-equal
                       [(if
                         (>
                          (current-price "SPY")
                          (moving-average-price "SPY" {:window 200}))
                         [(weight-equal
                           [(if
                             (> (rsi "TQQQ" {:window 14}) 75)
                             [(asset
                               "UVXY"
                               "ProShares Ultra VIX Short-Term Futures ETF")]
                             [(weight-equal
                               [(if
                                 (> (rsi "SPXL" {:window 10}) 80)
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")]
                                 [(group
                                   "A Better \"Buy the Dips Nasdaq\" by Garen Phillips"
                                   [(weight-equal
                                     [(if
                                       (<
                                        (cumulative-return
                                         "QQQ"
                                         {:window 5})
                                        -6)
                                       [(weight-equal
                                         [(if
                                           (>
                                            (cumulative-return
                                             "TQQQ"
                                             {:window 1})
                                            5)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (>
                                                (rsi
                                                 "TQQQ"
                                                 {:window 10})
                                                20)
                                               [(asset
                                                 "SQQQ"
                                                 "ProShares UltraPro Short QQQ")]
                                               [(asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")])])])])]
                                       [(weight-equal
                                         [(if
                                           (>
                                            (rsi "QQQ" {:window 10})
                                            80)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "QQQ"
                                                 {:window 10})
                                                31)
                                               [(asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")]
                                               [(asset
                                                 "QQQ"
                                                 "Invesco QQQ Trust Series I")])])])])])])])])])])])]
                         [(weight-equal
                           [(if
                             (<=
                              (cumulative-return "QQQ" {:window 60})
                              -20)
                             [(group
                               "Sideways Market Deleverage"
                               [(weight-equal
                                 [(if
                                   (>=
                                    (cumulative-return
                                     "UUP"
                                     {:window 2})
                                    1)
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "TLT"
                                         {:window 1})
                                        0)
                                       [(weight-equal
                                         [(filter
                                           (rsi {:window 5})
                                           (select-bottom 3)
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")
                                            (asset
                                             "SOXL"
                                             "Direxion Daily Semiconductor Bull 3x Shares")
                                            (asset
                                             "BIL"
                                             "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                            (asset
                                             "EWZ"
                                             "iShares MSCI Brazil ETF")
                                            (asset
                                             "UPRO"
                                             "ProShares UltraPro S&P500")
                                            (asset
                                             "QQQ"
                                             "Invesco QQQ Trust")
                                            (asset
                                             "TECL"
                                             "Direxion Daily Technology Bull 3x Shares")
                                            (asset
                                             "SPY"
                                             "SPDR S&P 500 ETF Trust")
                                            (asset
                                             "TNA"
                                             "Direxion Daily Small Cap Bull 3x Shares")
                                            (asset
                                             "XOP"
                                             "SPDR Series Trust - SPDR Oil & Gas Exploration and Production ETF")])])]
                                       [(weight-equal
                                         [(filter
                                           (rsi {:window 5})
                                           (select-bottom 3)
                                           [(asset
                                             "SQQQ"
                                             "ProShares UltraPro Short QQQ")
                                            (asset
                                             "SOXS"
                                             "Direxion Daily Semiconductor Bear 3x Shares")
                                            (asset
                                             "BIL"
                                             "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                            (asset
                                             "SH"
                                             "ProShares Short S&P500")
                                            (asset
                                             "PSQ"
                                             "ProShares Short QQQ")
                                            (asset
                                             "TECS"
                                             "Direxion Daily Technology Bear 3X Shares")
                                            (asset
                                             "TZA"
                                             "Direxion Daily Small Cap Bear 3x Shares")
                                            (asset
                                             "DUG"
                                             "ProShares Trust - ProShares UltraShort Energy")])])])])]
                                   [(weight-equal
                                     [(if
                                       (>=
                                        (current-price "SPY")
                                        (moving-average-price
                                         "SPY"
                                         {:window 3}))
                                       [(weight-equal
                                         [(filter
                                           (rsi {:window 5})
                                           (select-bottom 3)
                                           [(asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")
                                            (asset
                                             "SOXL"
                                             "Direxion Daily Semiconductor Bull 3x Shares")
                                            (asset
                                             "BIL"
                                             "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                            (asset
                                             "EWZ"
                                             "iShares MSCI Brazil ETF")
                                            (asset
                                             "UPRO"
                                             "ProShares UltraPro S&P500")
                                            (asset
                                             "QQQ"
                                             "Invesco QQQ Trust")
                                            (asset
                                             "TECL"
                                             "Direxion Daily Technology Bull 3x Shares")
                                            (asset
                                             "SPY"
                                             "SPDR S&P 500 ETF Trust")
                                            (asset
                                             "TNA"
                                             "Direxion Daily Small Cap Bull 3x Shares")])])]
                                       [(asset
                                         "BSV"
                                         "Vanguard Short-Term Bond ETF")
                                        (asset
                                         "TLT"
                                         "iShares 20+ Year Treasury Bond ETF")])])])])])]
                             [(weight-equal
                               [(if
                                 (< (rsi "TQQQ" {:window 9}) 32)
                                 [(weight-equal
                                   [(if
                                     (>=
                                      (cumulative-return
                                       "TQQQ"
                                       {:window 2})
                                      (cumulative-return
                                       "TQQQ"
                                       {:window 5}))
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 10})
                                         (select-bottom 1)
                                         [(asset
                                           "TECL"
                                           "Direxion Daily Technology Bull 3x Shares")
                                          (asset
                                           "SOXL"
                                           "Direxion Daily Semiconductor Bull 3x Shares")
                                          (asset
                                           "SHY"
                                           "iShares 1-3 Year Treasury Bond ETF")])
                                        (filter
                                         (rsi {:window 5})
                                         (select-bottom 1)
                                         [(asset
                                           "SOXL"
                                           "Direxion Daily Semiconductor Bull 3x Shares")
                                          (asset
                                           "SHY"
                                           "iShares 1-3 Year Treasury Bond ETF")])])]
                                     [(weight-equal
                                       [(if
                                         (<
                                          (rsi "SPY" {:window 10})
                                          30)
                                         [(weight-equal
                                           [(filter
                                             (rsi {:window 10})
                                             (select-bottom 1)
                                             [(asset
                                               "SPXL"
                                               "Direxion Daily S&P 500 Bull 3x Shares")
                                              (asset
                                               "SHY"
                                               "iShares 1-3 Year Treasury Bond ETF")])])]
                                         [(weight-equal
                                           [(if
                                             (>
                                              (rsi "UVXY" {:window 10})
                                              74)
                                             [(weight-equal
                                               [(if
                                                 (>
                                                  (rsi
                                                   "UVXY"
                                                   {:window 10})
                                                  84)
                                                 [(weight-equal
                                                   [(filter
                                                     (rsi {:window 10})
                                                     (select-top 1)
                                                     [(asset
                                                       "BSV"
                                                       "Vanguard Short-Term Bond ETF")
                                                      (asset
                                                       "SOXS"
                                                       "Direxion Daily Semiconductor Bear 3x Shares")])])]
                                                 [(asset
                                                   "UVXY"
                                                   "ProShares Ultra VIX Short-Term Futures ETF")])])]
                                             [(weight-equal
                                               [(if
                                                 (>
                                                  (current-price
                                                   "TQQQ")
                                                  (moving-average-price
                                                   "TQQQ"
                                                   {:window 20}))
                                                 [(weight-equal
                                                   [(if
                                                     (<
                                                      (rsi
                                                       "SQQQ"
                                                       {:window 10})
                                                      31)
                                                     [(asset
                                                       "SQQQ"
                                                       "ProShares UltraPro Short QQQ")]
                                                     [(asset
                                                       "SOXL"
                                                       "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                                 [(weight-equal
                                                   [(filter
                                                     (rsi {:window 10})
                                                     (select-top 1)
                                                     [(asset
                                                       "BSV"
                                                       "Vanguard Short-Term Bond ETF")
                                                      (asset
                                                       "SOXS"
                                                       "Direxion Daily Semiconductor Bear 3x Shares")])])])])])])])])])])]
                                 [(weight-equal
                                   [(if
                                     (< (rsi "SPY" {:window 10}) 30)
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 10})
                                         (select-bottom 1)
                                         [(asset
                                           "SPXL"
                                           "Direxion Daily S&P 500 Bull 3x Shares")
                                          (asset
                                           "SHY"
                                           "iShares 1-3 Year Treasury Bond ETF")])])]
                                     [(weight-equal
                                       [(if
                                         (>
                                          (rsi "UVXY" {:window 10})
                                          74)
                                         [(weight-equal
                                           [(if
                                             (>
                                              (rsi "UVXY" {:window 10})
                                              84)
                                             [(weight-equal
                                               [(filter
                                                 (rsi {:window 10})
                                                 (select-top 1)
                                                 [(asset
                                                   "BSV"
                                                   "Vanguard Short-Term Bond ETF")
                                                  (asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")])])]
                                             [(asset
                                               "UVXY"
                                               "ProShares Ultra VIX Short-Term Futures ETF")])])]
                                         [(weight-equal
                                           [(if
                                             (>
                                              (current-price "TQQQ")
                                              (moving-average-price
                                               "TQQQ"
                                               {:window 20}))
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (rsi
                                                   "SQQQ"
                                                   {:window 10})
                                                  31)
                                                 [(asset
                                                   "SOXS"
                                                   "Direxion Daily Semiconductor Bear 3x Shares")]
                                                 [(asset
                                                   "SOXL"
                                                   "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                             [(weight-equal
                                               [(filter
                                                 (rsi {:window 10})
                                                 (select-top 1)
                                                 [(asset
                                                   "BSV"
                                                   "Vanguard Short-Term Bond ETF")
                                                  (asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ")])])])])])])])])])])])])])])])])])])])])])
        (group
         "EM's"
         [(weight-equal
           [(group
             "EM #1 IEIvIWM, IGIBvEEM&SPY SHV Risk-on/Off"
             [(weight-equal
               [(if
                 (< (rsi "EEM" {:window 14}) 30)
                 [(asset "EDC" nil)]
                 [(weight-equal
                   [(if
                     (> (rsi "EEM" {:window 10}) 80)
                     [(asset
                       "EDZ"
                       "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")]
                     [(weight-equal
                       [(if
                         (>
                          (current-price "SHV")
                          (moving-average-price "SHV" {:window 50}))
                         [(weight-equal
                           [(if
                             (>
                              (current-price "EEM")
                              (moving-average-price
                               "EEM"
                               {:window 200}))
                             [(group
                               "IEI vs IWM"
                               [(weight-equal
                                 [(if
                                   (>
                                    (rsi "IEI" {:window 10})
                                    (rsi "IWM" {:window 15}))
                                   [(weight-equal
                                     [(filter
                                       (cumulative-return {:window 5})
                                       (select-bottom 1)
                                       [(asset
                                         "TQQQ"
                                         "ProShares Trust - ProShares UltraPro QQQ 3x Shares")
                                        (asset
                                         "EDC"
                                         "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                                        (asset
                                         "SOXL"
                                         "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")])])]
                                   [(weight-equal
                                     [(filter
                                       (cumulative-return {:window 5})
                                       (select-bottom 1)
                                       [(asset
                                         "EDZ"
                                         "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")])])])])])]
                             [(group
                               "IGIB vs EEM"
                               [(weight-equal
                                 [(if
                                   (>
                                    (rsi "IGIB" {:window 15})
                                    (rsi "EEM" {:window 15}))
                                   [(weight-equal
                                     [(filter
                                       (cumulative-return {:window 5})
                                       (select-bottom 1)
                                       [(asset
                                         "TQQQ"
                                         "ProShares Trust - ProShares UltraPro QQQ 3x Shares")
                                        (asset
                                         "EDC"
                                         "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                                        (asset
                                         "SOXL"
                                         "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")])])]
                                   [(asset "EDZ" nil)])])])
                              (group
                               "IGIB vs SPY"
                               [(weight-equal
                                 [(if
                                   (>
                                    (rsi "IGIB" {:window 10})
                                    (rsi "SPY" {:window 10}))
                                   [(weight-equal
                                     [(filter
                                       (cumulative-return {:window 5})
                                       (select-bottom 1)
                                       [(asset
                                         "TQQQ"
                                         "ProShares Trust - ProShares UltraPro QQQ 3x Shares")
                                        (asset
                                         "EDC"
                                         "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                                        (asset
                                         "SOXL"
                                         "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")])])]
                                   [(asset "EDZ" nil)])])])])])]
                         [(group
                           "IGIB vs SPY"
                           [(weight-equal
                             [(if
                               (>
                                (rsi "IGIB" {:window 10})
                                (rsi "SPY" {:window 10}))
                               [(weight-equal
                                 [(filter
                                   (cumulative-return {:window 5})
                                   (select-bottom 1)
                                   [(asset
                                     "TQQQ"
                                     "ProShares Trust - ProShares UltraPro QQQ 3x Shares")
                                    (asset
                                     "EDC"
                                     "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                                    (asset
                                     "SOXL"
                                     "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")])])]
                               [(asset "EDZ" nil)])])])])])])])])])])
            (group
             "EM #3 SHYvUSRT, IEFvDIA"
             [(weight-equal
               [(if
                 (>
                  (current-price "EEM")
                  (moving-average-price "EEM" {:window 200}))
                 [(weight-equal
                   [(if
                     (> (rsi "EEM" {:window 10}) 80)
                     [(group
                       "Edz/bil 65/35"
                       [(weight-specified
                         0.65
                         (asset
                          "EDZ"
                          "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")
                         0.35
                         (asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF"))])]
                     [(group
                       "Bull"
                       [(weight-equal
                         [(group
                           "SHY/USRT"
                           [(weight-equal
                             [(if
                               (>
                                (rsi "SHY" {:window 10})
                                (rsi "USRT" {:window 10}))
                               [(asset "EDC" nil)]
                               [(asset "EDZ" nil)])])])
                          (group
                           "IEF/DIA"
                           [(weight-equal
                             [(if
                               (>
                                (rsi "IEF" {:window 10})
                                (rsi "DIA" {:window 10}))
                               [(asset "EDC" nil)]
                               [(asset "EDZ" nil)])])])])])])])]
                 [(group
                   "Bear"
                   [(weight-equal
                     [(if
                       (< (rsi "EEM" {:window 10}) 25)
                       [(group
                         "EDC/bil 68/32"
                         [(weight-specified
                           0.68
                           (asset
                            "EDC"
                            "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                           0.32
                           (asset
                            "BIL"
                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF"))])]
                       [(weight-equal
                         [(group
                           "ISCB/IWM"
                           [(weight-equal
                             [(if
                               (>
                                (rsi "ISCB" {:window 10})
                                (rsi "IWM" {:window 10}))
                               [(asset "EDC" nil)]
                               [(asset "EDZ" nil)])])])
                          (group
                           "IGIB/DLN"
                           [(weight-equal
                             [(if
                               (>
                                (rsi "IGIB" {:window 10})
                                (rsi "DLN" {:window 10}))
                               [(asset "EDC" nil)]
                               [(asset "EDZ" nil)])])])])])])])])])])
            (group
             "EM #4 MMTvXLU, HIXvBBH, MHDvXLP"
             [(weight-equal
               [(group
                 "EM | 1999"
                 [(weight-equal
                   [(group
                     "MMT>XLU"
                     [(weight-equal
                       [(if
                         (>
                          (rsi "MMT" {:window 10})
                          (rsi "XLU" {:window 10}))
                         [(asset "EDC" nil)]
                         [(asset "EDZ" nil)])])])
                    (group
                     "HIX>BBH"
                     [(weight-equal
                       [(if
                         (>
                          (rsi "PIM" {:window 10})
                          (rsi "BBH" {:window 10}))
                         [(asset "EDC" nil)]
                         [(asset "EDZ" nil)])])])
                    (group
                     "MHD>XLP"
                     [(weight-equal
                       [(if
                         (>
                          (rsi "MHD" {:window 10})
                          (rsi "XLP" {:window 10}))
                         [(asset "EDC" nil)]
                         [(asset "EDZ" nil)])])])])])])])])])])])]
   [(asset
     "BIL"
     "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])
  0.3
  (if
   (> (current-price "SPY") (moving-average-price "SPY" {:window 200}))
   [(group
     "Pheonix and J?rmungandr"
     [(weight-equal
       [(filter
         (cumulative-return {:window 6})
         (select-top 3)
         [(group
           "(TMF/TMV/Gold Momentum)/Energy Momentum V3 (Final)"
           [(weight-equal
             [(group
               "TMF/TMV/Gold Momentum"
               [(weight-equal
                 [(group
                   "TMV Momentum"
                   [(weight-equal
                     [(if
                       (< (rsi "TMF" {:window 10}) 32)
                       [(asset
                         "TMF"
                         "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                       [(weight-equal
                         [(if
                           (>
                            (moving-average-price "TMV" {:window 15})
                            (moving-average-price "TMV" {:window 50}))
                           [(weight-equal
                             [(if
                               (>
                                (current-price "TMV")
                                (moving-average-price
                                 "TMV"
                                 {:window 135}))
                               [(weight-equal
                                 [(if
                                   (> (rsi "TMV" {:window 10}) 71)
                                   [(asset
                                     "SHV"
                                     "iShares Short Treasury Bond ETF")]
                                   [(weight-equal
                                     [(if
                                       (> (rsi "TMV" {:window 60}) 59)
                                       [(asset
                                         "TLT"
                                         "iShares 20+ Year Treasury Bond ETF")]
                                       [(asset
                                         "TMV"
                                         "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                               [(asset
                                 "BND"
                                 "Vanguard Total Bond Market ETF")])])]
                           [(asset
                             "BND"
                             "Vanguard Total Bond Market ETF")])])])])])
                  (group
                   "TMF Momentum"
                   [(weight-specified
                     1
                     (if
                      (< (rsi "TMF" {:window 10}) 32)
                      [(asset
                        "TMF"
                        "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                      [(weight-equal
                        [(if
                          (>
                           (moving-average-price "TLT" {:window 15})
                           (moving-average-price "TLT" {:window 50}))
                          [(weight-equal
                            [(if
                              (> (rsi "TMF" {:window 10}) 72)
                              [(asset
                                "SHV"
                                "iShares Short Treasury Bond ETF")]
                              [(weight-equal
                                [(if
                                  (> (rsi "TMF" {:window 60}) 57)
                                  [(asset
                                    "TBF"
                                    "Proshares Short 20+ Year Treasury")]
                                  [(asset
                                    "TMF"
                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])]
                          [(asset
                            "SHV"
                            "iShares Short Treasury Bond ETF")])])]))])
                  (group
                   "Gold Momentum"
                   [(weight-equal
                     [(if
                       (>
                        (moving-average-price "GLD" {:window 200})
                        (moving-average-price "GLD" {:window 350}))
                       [(weight-equal
                         [(if
                           (>
                            (moving-average-price "GLD" {:window 60})
                            (moving-average-price "GLD" {:window 150}))
                           [(asset "GLD" nil)]
                           [(asset "SHV" nil)])])]
                       [(asset "SHV" nil)])])])])])
              (group
               "Energy Momentum V3 (Final)"
               [(weight-equal
                 [(weight-equal
                   [(group
                     "Natural Gas"
                     [(weight-equal
                       [(weight-equal
                         [(if
                           (>
                            (moving-average-price "FCG" {:window 100})
                            (moving-average-price "FCG" {:window 500}))
                           [(weight-specified
                             0.9
                             (asset
                              "FCG"
                              "First Trust Natural Gas ETF")
                             0.1
                             (if
                              (>
                               (current-price "UNG")
                               (moving-average-price
                                "UNG"
                                {:window 50}))
                              [(asset
                                "BOIL"
                                "ProShares Ultra Bloomberg Natural Gas")]
                              [(asset
                                "KOLD"
                                "ProShares UltraShort Bloomberg Natural Gas")]))]
                           [(weight-equal
                             [(if
                               (<
                                (moving-average-price
                                 "UNG"
                                 {:window 50})
                                (moving-average-price
                                 "UNG"
                                 {:window 400}))
                               [(weight-equal
                                 [(if
                                   (<
                                    (current-price "UNG")
                                    (moving-average-price
                                     "UNG"
                                     {:window 10}))
                                   [(weight-equal
                                     [(asset
                                       "KOLD"
                                       "ProShares UltraShort Bloomberg Natural Gas")
                                      (asset
                                       "SHY"
                                       "iShares 1-3 Year Treasury Bond ETF")])]
                                   [(weight-equal
                                     [(asset
                                       "SHV"
                                       "iShares Short Treasury Bond ETF")])])])]
                               [(weight-equal
                                 [(asset
                                   "UNG"
                                   "United States Natural Gas Fund LP")])])])])])])])
                    (group
                     "Clean Energy"
                     [(weight-equal
                       [(if
                         (>
                          (current-price "ICLN")
                          (moving-average-price "ICLN" {:window 200}))
                         [(weight-equal
                           [(if
                             (>
                              (moving-average-price "ICLN" {:window 9})
                              (moving-average-price
                               "ICLN"
                               {:window 21}))
                             [(weight-equal
                               [(asset
                                 "ICLN"
                                 "iShares Global Clean Energy ETF")
                                (asset "TAN" "Invesco Solar ETF")
                                (asset
                                 "FAN"
                                 "First Trust Global Wind Energy ETF")])]
                             [(asset
                               "SHV"
                               "iShares Short Treasury Bond ETF")])])]
                         [(asset
                           "SHV"
                           "iShares Short Treasury Bond ETF")])])])
                    (group
                     "Oil"
                     [(weight-equal
                       [(group
                         "There Will Be Blood"
                         [(weight-equal
                           [(if
                             (>=
                              (exponential-moving-average-price
                               "DBO"
                               {:window 50})
                              (moving-average-price
                               "DBO"
                               {:window 200}))
                             [(weight-equal
                               [(if
                                 (>
                                  (moving-average-price
                                   "XOP"
                                   {:window 9})
                                  (moving-average-price
                                   "XOP"
                                   {:window 21}))
                                 [(weight-equal
                                   [(if
                                     (<
                                      (cumulative-return
                                       "XOP"
                                       {:window 30})
                                      -10)
                                     [(weight-equal
                                       [(filter
                                         (moving-average-return
                                          {:window 21})
                                         (select-top 2)
                                         [(asset
                                           "XOM"
                                           "Exxon Mobil Corporation")
                                          (asset
                                           "XLE"
                                           "Energy Select Sector SPDR Fund")
                                          (asset
                                           "ENPH"
                                           "Enphase Energy, Inc.")
                                          (asset
                                           "VLO"
                                           "Valero Energy Corporation")
                                          (asset
                                           "CVE"
                                           "Cenovus Energy Inc.")
                                          (asset
                                           "CVX"
                                           "Chevron Corporation")
                                          (asset
                                           "COP"
                                           "ConocoPhillips")
                                          (asset
                                           "MPC"
                                           "Marathon Petroleum Corporation")
                                          (asset
                                           "DINO"
                                           "HF Sinclair Corporation")])])]
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 9})
                                         (select-top 1)
                                         [(asset
                                           "XOP"
                                           "SPDR Series Trust - SPDR Oil & Gas Exploration and Production ETF")
                                          (asset
                                           "UCO"
                                           "ProShares Trust - ProShares Ultra Bloomberg Crude Oil 2x Shares")])])])
                                    (filter
                                     (moving-average-return
                                      {:window 21})
                                     (select-top 2)
                                     [(asset
                                       "XOM"
                                       "Exxon Mobil Corporation")
                                      (asset
                                       "XLE"
                                       "Energy Select Sector SPDR Fund")
                                      (asset
                                       "ENPH"
                                       "Enphase Energy, Inc.")
                                      (asset
                                       "VLO"
                                       "Valero Energy Corporation")
                                      (asset
                                       "CVE"
                                       "Cenovus Energy Inc.")
                                      (asset
                                       "CVX"
                                       "Chevron Corporation")
                                      (asset "COP" "ConocoPhillips")
                                      (asset
                                       "MPC"
                                       "Marathon Petroleum Corporation")
                                      (asset
                                       "DINO"
                                       "HF Sinclair Corporation")])])]
                                 [(weight-equal
                                   [(filter
                                     (moving-average-return
                                      {:window 100})
                                     (select-top 2)
                                     [(asset
                                       "XOM"
                                       "Exxon Mobil Corporation")
                                      (asset
                                       "ENPH"
                                       "Enphase Energy, Inc.")
                                      (asset
                                       "VLO"
                                       "Valero Energy Corporation")
                                      (asset
                                       "CVE"
                                       "Cenovus Energy Inc.")
                                      (asset
                                       "CVX"
                                       "Chevron Corporation")
                                      (asset "COP" "ConocoPhillips")
                                      (asset
                                       "MPC"
                                       "Marathon Petroleum Corporation")
                                      (asset
                                       "DINO"
                                       "HF Sinclair Corporation")])])])])]
                             [(weight-equal
                               [(if
                                 (<=
                                  (moving-average-price
                                   "UCO"
                                   {:window 50})
                                  (moving-average-price
                                   "UCO"
                                   {:window 400}))
                                 [(weight-equal
                                   [(if
                                     (<
                                      (moving-average-return
                                       "XOP"
                                       {:window 5})
                                      0)
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 7})
                                         (select-top 1)
                                         [(asset
                                           "DUG"
                                           "ProShares Trust - ProShares UltraShort Energy")
                                          (asset
                                           "IEF"
                                           "iShares 7-10 Year Treasury Bond ETF")])])]
                                     [(weight-equal
                                       [(filter
                                         (rsi {:window 10})
                                         (select-top 1)
                                         [(asset
                                           "XOP"
                                           "SPDR Series Trust - SPDR Oil & Gas Exploration and Production ETF")
                                          (asset
                                           "UCO"
                                           "ProShares Trust - ProShares Ultra Bloomberg Crude Oil 2x Shares")])])])
                                    (filter
                                     (moving-average-return
                                      {:window 100})
                                     (select-top 2)
                                     [(asset
                                       "XOM"
                                       "Exxon Mobil Corporation")
                                      (asset
                                       "ENPH"
                                       "Enphase Energy, Inc.")
                                      (asset
                                       "VLO"
                                       "Valero Energy Corporation")
                                      (asset
                                       "CVE"
                                       "Cenovus Energy Inc.")
                                      (asset
                                       "CVX"
                                       "Chevron Corporation")
                                      (asset "COP" "ConocoPhillips")
                                      (asset
                                       "MPC"
                                       "Marathon Petroleum Corporation")
                                      (asset
                                       "DINO"
                                       "HF Sinclair Corporation")])])]
                                 [(weight-equal
                                   [(filter
                                     (moving-average-return
                                      {:window 100})
                                     (select-top 2)
                                     [(asset
                                       "XOM"
                                       "Exxon Mobil Corporation")
                                      (asset
                                       "ENPH"
                                       "Enphase Energy, Inc.")
                                      (asset
                                       "VLO"
                                       "Valero Energy Corporation")
                                      (asset
                                       "CVE"
                                       "Cenovus Energy Inc.")
                                      (asset
                                       "CVX"
                                       "Chevron Corporation")
                                      (asset "COP" "ConocoPhillips")
                                      (asset
                                       "MPC"
                                       "Marathon Petroleum Corporation")
                                      (asset
                                       "DINO"
                                       "HF Sinclair Corporation")])])])])])])])])])
                    (group
                     "V2 XLE Momentum"
                     [(weight-equal
                       [(if
                         (>
                          (exponential-moving-average-price
                           "XLE"
                           {:window 30})
                          (moving-average-price "XLE" {:window 200}))
                         [(weight-equal
                           [(asset
                             "XLE"
                             "Energy Select Sector SPDR Fund")])]
                         [(weight-equal
                           [(asset
                             "SHV"
                             "iShares Short Treasury Bond ETF")])])])])])])])])])
          (group
           "TUSI Custom/ Cautious Fund Surfing"
           [(weight-equal
             [(group
               "TUSI Custom"
               [(weight-equal
                 [(group
                   "Vol Hedge Logic Group"
                   [(weight-equal
                     [(if
                       (> (rsi "QQQ" {:window 10}) 80)
                       [(weight-equal
                         [(asset
                           "UVXY"
                           "ProShares Ultra VIX Short-Term Futures ETF")
                          (asset
                           "BTAL"
                           "AGF U.S. Market Neutral Anti-Beta Fund")])]
                       [(group
                         "Vol Hedge Logic Group"
                         [(weight-specified
                           0.25
                           (group
                            "Spy max dd check | 2.4% cagr, 10.3% stdev, 20.6% dd, 0.29 sharpe, 0.12 calmar, -0.23 beta"
                            [(weight-equal
                              [(if
                                (> (max-drawdown "SPY" {:window 10}) 5)
                                [(weight-equal
                                  [(asset
                                    "UVXY"
                                    "ProShares Ultra VIX Short-Term Futures ETF")
                                   (asset "GLD" "SPDR Gold Shares")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")
                                   (asset
                                    "IEF"
                                    "iShares 7-10 Year Treasury Bond ETF")
                                   (asset
                                    "BTAL"
                                    "AGF U.S. Market Neutral Anti-Beta Fund")])]
                                [(weight-equal
                                  [(asset "GLD" "SPDR Gold Shares")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")
                                   (asset
                                    "XLP"
                                    "Consumer Staples Select Sector SPDR Fund")
                                   (asset
                                    "SHY"
                                    "iShares 1-3 Year Treasury Bond ETF")])])
                               (if
                                (> (max-drawdown "SPY" {:window 20}) 7)
                                [(weight-equal
                                  [(asset
                                    "UVXY"
                                    "ProShares Ultra VIX Short-Term Futures ETF")
                                   (asset "GLD" "SPDR Gold Shares")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")
                                   (asset
                                    "IEF"
                                    "iShares 7-10 Year Treasury Bond ETF")
                                   (asset
                                    "BTAL"
                                    "AGF U.S. Market Neutral Anti-Beta Fund")])]
                                [(weight-equal
                                  [(asset "GLD" "SPDR Gold Shares")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")
                                   (asset
                                    "XLP"
                                    "Consumer Staples Select Sector SPDR Fund")
                                   (asset
                                    "SHY"
                                    "iShares 1-3 Year Treasury Bond ETF")])])
                               (if
                                (>
                                 (max-drawdown "SPY" {:window 40})
                                 10)
                                [(weight-equal
                                  [(weight-equal
                                    [(asset
                                      "UVXY"
                                      "ProShares Ultra VIX Short-Term Futures ETF")
                                     (asset "GLD" "SPDR Gold Shares")
                                     (asset
                                      "UUP"
                                      "Invesco DB US Dollar Index Bullish Fund")
                                     (asset
                                      "IEF"
                                      "iShares 7-10 Year Treasury Bond ETF")
                                     (asset
                                      "BTAL"
                                      "AGF U.S. Market Neutral Anti-Beta Fund")])])]
                                [(weight-equal
                                  [(asset "GLD" "SPDR Gold Shares")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")
                                   (asset
                                    "XLP"
                                    "Consumer Staples Select Sector SPDR Fund")
                                   (asset
                                    "SHY"
                                    "iShares 1-3 Year Treasury Bond ETF")])])])])
                           0.4
                           (group
                            "Vix RSI Check | 6.3% cagr, 9.6% stdev, 13.4% dd, 0.68 sharpe, 0.47 calmar, -0.08 beta"
                            [(weight-equal
                              [(if
                                (> (rsi "VIXY" {:window 20}) 65)
                                [(weight-equal
                                  [(asset
                                    "UVXY"
                                    "ProShares Ultra VIX Short-Term Futures ETF")
                                   (asset
                                    "BTAL"
                                    "AGF U.S. Market Neutral Anti-Beta Fund")
                                   (asset
                                    "IEF"
                                    "iShares 7-10 Year Treasury Bond ETF")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")])]
                                [(weight-equal
                                  [(asset "GLD" "SPDR Gold Shares")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")
                                   (asset
                                    "XLP"
                                    "Consumer Staples Select Sector SPDR Fund")
                                   (asset
                                    "SHY"
                                    "iShares 1-3 Year Treasury Bond ETF")])])
                               (if
                                (> (rsi "VIXY" {:window 40}) 60)
                                [(weight-equal
                                  [(asset
                                    "UVXY"
                                    "ProShares Ultra VIX Short-Term Futures ETF")
                                   (asset
                                    "BTAL"
                                    "AGF U.S. Market Neutral Anti-Beta Fund")
                                   (asset
                                    "IEF"
                                    "iShares 7-10 Year Treasury Bond ETF")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")])]
                                [(weight-equal
                                  [(asset "GLD" "SPDR Gold Shares")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")
                                   (asset
                                    "XLP"
                                    "Consumer Staples Select Sector SPDR Fund")
                                   (asset
                                    "SHY"
                                    "iShares 1-3 Year Treasury Bond ETF")])])
                               (if
                                (> (rsi "VIXY" {:window 60}) 60)
                                [(weight-equal
                                  [(asset
                                    "UVXY"
                                    "ProShares Ultra VIX Short-Term Futures ETF")
                                   (asset
                                    "BTAL"
                                    "AGF U.S. Market Neutral Anti-Beta Fund")
                                   (asset
                                    "IEF"
                                    "iShares 7-10 Year Treasury Bond ETF")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")])]
                                [(weight-equal
                                  [(asset "GLD" "SPDR Gold Shares")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")
                                   (asset
                                    "XLP"
                                    "Consumer Staples Select Sector SPDR Fund")
                                   (asset
                                    "SHY"
                                    "iShares 1-3 Year Treasury Bond ETF")])])])])
                           0.2
                           (group
                            "Spy stdev check | 0.7% cagr, 15.1% stdev, 35.9% dd, 0.12 sharpe, 0.02 calmar, -0.41 beta"
                            [(weight-specified
                              0.35
                              (if
                               (>
                                (stdev-return "SPY" {:window 21})
                                1.25)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])])
                              0.65
                              (if
                               (>
                                (stdev-return "SPY" {:window 21})
                                1.5)
                               [(weight-equal
                                 [(asset
                                   "UVXY"
                                   "ProShares Ultra VIX Short-Term Futures ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")
                                  (asset
                                   "IEF"
                                   "iShares 7-10 Year Treasury Bond ETF")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")])]
                               [(weight-equal
                                 [(asset "GLD" "SPDR Gold Shares")
                                  (asset
                                   "UUP"
                                   "Invesco DB US Dollar Index Bullish Fund")
                                  (asset
                                   "XLP"
                                   "Consumer Staples Select Sector SPDR Fund")
                                  (asset
                                   "SHY"
                                   "iShares 1-3 Year Treasury Bond ETF")])]))])
                           0.15
                           (group
                            "Vix stdev check | 0.3% cagr, 15% stdev, 39.5% dd, 0.09 sharpe, 0.01 calmar, -0.39 beta"
                            [(weight-equal
                              [(if
                                (>
                                 (stdev-return "VIXY" {:window 40})
                                 5)
                                [(weight-equal
                                  [(asset
                                    "UVXY"
                                    "ProShares Ultra VIX Short-Term Futures ETF")
                                   (asset
                                    "BTAL"
                                    "AGF U.S. Market Neutral Anti-Beta Fund")
                                   (asset
                                    "IEF"
                                    "iShares 7-10 Year Treasury Bond ETF")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")])]
                                [(weight-equal
                                  [(asset "GLD" "SPDR Gold Shares")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")
                                   (asset
                                    "XLP"
                                    "Consumer Staples Select Sector SPDR Fund")
                                   (asset
                                    "SHY"
                                    "iShares 1-3 Year Treasury Bond ETF")])])
                               (if
                                (>
                                 (stdev-return "VIXY" {:window 40})
                                 6)
                                [(weight-equal
                                  [(asset
                                    "UVXY"
                                    "ProShares Ultra VIX Short-Term Futures ETF")
                                   (asset
                                    "BTAL"
                                    "AGF U.S. Market Neutral Anti-Beta Fund")
                                   (asset
                                    "IEF"
                                    "iShares 7-10 Year Treasury Bond ETF")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")])]
                                [(weight-equal
                                  [(asset "GLD" "SPDR Gold Shares")
                                   (asset
                                    "UUP"
                                    "Invesco DB US Dollar Index Bullish Fund")
                                   (asset
                                    "XLP"
                                    "Consumer Staples Select Sector SPDR Fund")
                                   (asset
                                    "SHY"
                                    "iShares 1-3 Year Treasury Bond ETF")])])])]))])])])])])])
              (group
               "V2 | Cautious Fund Surfing | 3x with V1.1 | Bear BUYDIPS, Bull HFEAR"
               [(weight-equal
                 [(group
                   "1% stdev https://discord.gg/8e7bHnJMwE"
                   [(weight-equal
                     [(weight-equal
                       [(group
                         "14d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 14}) 1)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 14})
                                  (rsi "SHY" {:window 14}))
                                 [(weight-inverse-volatility
                                   14
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                        (group
                         "21d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 21}) 1)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 21})
                                  (rsi "SHY" {:window 21}))
                                 [(weight-inverse-volatility
                                   21
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                        (group
                         "28d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 28}) 1)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 28})
                                  (rsi "SHY" {:window 28}))
                                 [(weight-inverse-volatility
                                   28
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                        (group
                         "35d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 35}) 1)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 35})
                                  (rsi "SHY" {:window 35}))
                                 [(weight-inverse-volatility
                                   35
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                        (group
                         "42d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 42}) 1)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 42})
                                  (rsi "SHY" {:window 42}))
                                 [(weight-inverse-volatility
                                   42
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])])])
                  (group
                   "1.5% stdev https://discord.gg/8e7bHnJMwE"
                   [(weight-equal
                     [(weight-equal
                       [(group
                         "14d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 14}) 1.5)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 14})
                                  (rsi "SHY" {:window 14}))
                                 [(weight-inverse-volatility
                                   14
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                        (group
                         "21d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 21}) 1.5)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 21})
                                  (rsi "SHY" {:window 21}))
                                 [(weight-inverse-volatility
                                   21
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                        (group
                         "28d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 28}) 1.5)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 28})
                                  (rsi "SHY" {:window 28}))
                                 [(weight-inverse-volatility
                                   28
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                        (group
                         "35d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 35}) 1.5)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 35})
                                  (rsi "SHY" {:window 35}))
                                 [(weight-inverse-volatility
                                   35
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                        (group
                         "42d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 42}) 1.5)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 42})
                                  (rsi "SHY" {:window 42}))
                                 [(weight-inverse-volatility
                                   42
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])])])
                  (group
                   "2% stdev https://discord.gg/8e7bHnJMwE"
                   [(weight-equal
                     [(weight-equal
                       [(group
                         "14d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 14}) 2)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 14})
                                  (rsi "SHY" {:window 14}))
                                 [(weight-inverse-volatility
                                   14
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                        (group
                         "21d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 21}) 2)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 21})
                                  (rsi "SHY" {:window 21}))
                                 [(weight-inverse-volatility
                                   21
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                        (group
                         "35d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 35}) 2)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 35})
                                  (rsi "SHY" {:window 35}))
                                 [(weight-inverse-volatility
                                   35
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                        (group
                         "28d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 28}) 2)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 28})
                                  (rsi "SHY" {:window 28}))
                                 [(weight-inverse-volatility
                                   28
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])
                        (group
                         "42d"
                         [(weight-equal
                           [(if
                             (< (stdev-return "SPY" {:window 42}) 2)
                             [(weight-equal
                               [(if
                                 (<
                                  (rsi "SPY" {:window 42})
                                  (rsi "SHY" {:window 42}))
                                 [(weight-inverse-volatility
                                   42
                                   [(asset
                                     "UPRO"
                                     "ProShares UltraPro S&P500")
                                    (asset
                                     "TQQQ"
                                     "ProShares UltraPro QQQ")])]
                                 [(group
                                   "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                   [(weight-equal
                                     [(if
                                       (>
                                        (max-drawdown
                                         "SPY"
                                         {:window 252})
                                        10)
                                       [(group
                                         "Buy the Dips: Nasdaq 100/S&P 500"
                                         [(weight-equal
                                           [(group
                                             "Nasdaq Dip Check"
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (cumulative-return
                                                   "QQQ"
                                                   {:window 5})
                                                  -5)
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (cumulative-return
                                                       "TQQQ"
                                                       {:window 1})
                                                      5)
                                                     [(weight-equal
                                                       [(group
                                                         "S&P500 Dip Check"
                                                         [(weight-equal
                                                           [(if
                                                             (<
                                                              (cumulative-return
                                                               "SPY"
                                                               {:window
                                                                5})
                                                              -5)
                                                             [(weight-equal
                                                               [(if
                                                                 (>
                                                                  (cumulative-return
                                                                   "UPRO"
                                                                   {:window
                                                                    1})
                                                                  5)
                                                                 [(group
                                                                   "Safety Mix | UUP, GLD, & XLP"
                                                                   [(weight-equal
                                                                     [(asset
                                                                       "UUP"
                                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                                      (asset
                                                                       "GLD"
                                                                       "SPDR Gold Shares")
                                                                      (asset
                                                                       "XLP"
                                                                       "Consumer Staples Select Sector SPDR Fund")])])]
                                                                 [(asset
                                                                   "UPRO"
                                                                   "ProShares UltraPro S&P500")])])]
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                     [(asset
                                                       "TQQQ"
                                                       "ProShares UltraPro QQQ")])])]
                                                 [(weight-equal
                                                   [(group
                                                     "S&P500 Dip Check"
                                                     [(weight-equal
                                                       [(if
                                                         (<
                                                          (cumulative-return
                                                           "SPY"
                                                           {:window 5})
                                                          -5)
                                                         [(weight-equal
                                                           [(if
                                                             (>
                                                              (cumulative-return
                                                               "UPRO"
                                                               {:window
                                                                1})
                                                              5)
                                                             [(group
                                                               "Safety Mix | UUP, GLD, & XLP"
                                                               [(weight-equal
                                                                 [(asset
                                                                   "UUP"
                                                                   "Invesco DB US Dollar Index Bullish Fund")
                                                                  (asset
                                                                   "GLD"
                                                                   "SPDR Gold Shares")
                                                                  (asset
                                                                   "XLP"
                                                                   "Consumer Staples Select Sector SPDR Fund")])])]
                                                             [(asset
                                                               "UPRO"
                                                               "ProShares UltraPro S&P500")])])]
                                                         [(group
                                                           "Safety Mix | UUP, GLD, & XLP"
                                                           [(weight-equal
                                                             [(asset
                                                               "UUP"
                                                               "Invesco DB US Dollar Index Bullish Fund")
                                                              (asset
                                                               "GLD"
                                                               "SPDR Gold Shares")
                                                              (asset
                                                               "XLP"
                                                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                       [(weight-equal
                                         [(group
                                           "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (max-drawdown
                                                 "SPY"
                                                 {:window 10})
                                                5)
                                               [(group
                                                 "Risk ON"
                                                 [(weight-specified
                                                   0.55
                                                   (weight-inverse-volatility
                                                    21
                                                    [(asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")])
                                                   0.45
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                               [(group
                                                 "Risk OFF"
                                                 [(weight-equal
                                                   [(group
                                                     "Safety Mix | UUP, GLD, & XLP"
                                                     [(weight-equal
                                                       [(asset
                                                         "UUP"
                                                         "Invesco DB US Dollar Index Bullish Fund")
                                                        (asset
                                                         "GLD"
                                                         "SPDR Gold Shares")
                                                        (asset
                                                         "XLP"
                                                         "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])]
                             [(weight-equal
                               [(group
                                 "V1 | Bear BUYDIPS, Bull HFEAR | Michael B"
                                 [(weight-equal
                                   [(if
                                     (>
                                      (max-drawdown
                                       "SPY"
                                       {:window 252})
                                      10)
                                     [(group
                                       "Buy the Dips: Nasdaq 100/S&P 500"
                                       [(weight-equal
                                         [(group
                                           "Nasdaq Dip Check"
                                           [(weight-equal
                                             [(if
                                               (<
                                                (cumulative-return
                                                 "QQQ"
                                                 {:window 5})
                                                -5)
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (cumulative-return
                                                     "TQQQ"
                                                     {:window 1})
                                                    5)
                                                   [(weight-equal
                                                     [(group
                                                       "S&P500 Dip Check"
                                                       [(weight-equal
                                                         [(if
                                                           (<
                                                            (cumulative-return
                                                             "SPY"
                                                             {:window
                                                              5})
                                                            -5)
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (cumulative-return
                                                                 "UPRO"
                                                                 {:window
                                                                  1})
                                                                5)
                                                               [(group
                                                                 "Safety Mix | UUP, GLD, & XLP"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "UUP"
                                                                     "Invesco DB US Dollar Index Bullish Fund")
                                                                    (asset
                                                                     "GLD"
                                                                     "SPDR Gold Shares")
                                                                    (asset
                                                                     "XLP"
                                                                     "Consumer Staples Select Sector SPDR Fund")])])]
                                                               [(asset
                                                                 "UPRO"
                                                                 "ProShares UltraPro S&P500")])])]
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])])])])])]
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])])]
                                               [(weight-equal
                                                 [(group
                                                   "S&P500 Dip Check"
                                                   [(weight-equal
                                                     [(if
                                                       (<
                                                        (cumulative-return
                                                         "SPY"
                                                         {:window 5})
                                                        -5)
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (cumulative-return
                                                             "UPRO"
                                                             {:window
                                                              1})
                                                            5)
                                                           [(group
                                                             "Safety Mix | UUP, GLD, & XLP"
                                                             [(weight-equal
                                                               [(asset
                                                                 "UUP"
                                                                 "Invesco DB US Dollar Index Bullish Fund")
                                                                (asset
                                                                 "GLD"
                                                                 "SPDR Gold Shares")
                                                                (asset
                                                                 "XLP"
                                                                 "Consumer Staples Select Sector SPDR Fund")])])]
                                                           [(asset
                                                             "UPRO"
                                                             "ProShares UltraPro S&P500")])])]
                                                       [(group
                                                         "Safety Mix | UUP, GLD, & XLP"
                                                         [(weight-equal
                                                           [(asset
                                                             "UUP"
                                                             "Invesco DB US Dollar Index Bullish Fund")
                                                            (asset
                                                             "GLD"
                                                             "SPDR Gold Shares")
                                                            (asset
                                                             "XLP"
                                                             "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])]
                                     [(weight-equal
                                       [(group
                                         "Hedgefundie's Excellent Adventure Refined | Higher Growth"
                                         [(weight-equal
                                           [(if
                                             (<
                                              (max-drawdown
                                               "SPY"
                                               {:window 10})
                                              5)
                                             [(group
                                               "Risk ON"
                                               [(weight-specified
                                                 0.55
                                                 (weight-inverse-volatility
                                                  21
                                                  [(asset
                                                    "UPRO"
                                                    "ProShares UltraPro S&P500")
                                                   (asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])
                                                 0.45
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares"))])]
                                             [(group
                                               "Risk OFF"
                                               [(weight-equal
                                                 [(group
                                                   "Safety Mix | UUP, GLD, & XLP"
                                                   [(weight-equal
                                                     [(asset
                                                       "UUP"
                                                       "Invesco DB US Dollar Index Bullish Fund")
                                                      (asset
                                                       "GLD"
                                                       "SPDR Gold Shares")
                                                      (asset
                                                       "XLP"
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])])])])])])])
          (group
           "(TMF/TMV/Gold Momentum)/Rising Rates Vol Switch Simple"
           [(weight-equal
             [(group
               "TMF/TMV/Gold Momentum"
               [(weight-equal
                 [(group
                   "TMV Momentum"
                   [(weight-equal
                     [(if
                       (< (rsi "TMF" {:window 10}) 32)
                       [(asset
                         "TMF"
                         "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                       [(weight-equal
                         [(if
                           (>
                            (moving-average-price "TMV" {:window 15})
                            (moving-average-price "TMV" {:window 50}))
                           [(weight-equal
                             [(if
                               (>
                                (current-price "TMV")
                                (moving-average-price
                                 "TMV"
                                 {:window 135}))
                               [(weight-equal
                                 [(if
                                   (> (rsi "TMV" {:window 10}) 71)
                                   [(asset
                                     "SHV"
                                     "iShares Short Treasury Bond ETF")]
                                   [(weight-equal
                                     [(if
                                       (> (rsi "TMV" {:window 60}) 59)
                                       [(asset
                                         "TLT"
                                         "iShares 20+ Year Treasury Bond ETF")]
                                       [(asset
                                         "TMV"
                                         "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                               [(asset
                                 "BND"
                                 "Vanguard Total Bond Market ETF")])])]
                           [(asset
                             "BND"
                             "Vanguard Total Bond Market ETF")])])])])])
                  (group
                   "TMF Momentum"
                   [(weight-specified
                     1
                     (if
                      (< (rsi "TMF" {:window 10}) 32)
                      [(asset
                        "TMF"
                        "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                      [(weight-equal
                        [(if
                          (>
                           (moving-average-price "TLT" {:window 15})
                           (moving-average-price "TLT" {:window 50}))
                          [(weight-equal
                            [(if
                              (> (rsi "TMF" {:window 10}) 72)
                              [(asset
                                "SHV"
                                "iShares Short Treasury Bond ETF")]
                              [(weight-equal
                                [(if
                                  (> (rsi "TMF" {:window 60}) 57)
                                  [(asset
                                    "TBF"
                                    "Proshares Short 20+ Year Treasury")]
                                  [(asset
                                    "TMF"
                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])]
                          [(asset
                            "SHV"
                            "iShares Short Treasury Bond ETF")])])]))])
                  (group
                   "Gold Momentum"
                   [(weight-equal
                     [(if
                       (>
                        (moving-average-price "GLD" {:window 200})
                        (moving-average-price "GLD" {:window 350}))
                       [(weight-equal
                         [(if
                           (>
                            (moving-average-price "GLD" {:window 60})
                            (moving-average-price "GLD" {:window 150}))
                           [(asset "GLD" nil)]
                           [(asset "SHV" nil)])])]
                       [(asset "SHV" nil)])])])])])
              (group
               "Rising Rates Vol Switch Simple"
               [(weight-equal
                 [(if
                   (> (rsi "QQQ" {:window 10}) 79)
                   [(weight-equal
                     [(asset
                       "UVXY"
                       "ProShares Ultra VIX Short-Term Futures ETF")])]
                   [(weight-equal
                     [(if
                       (< (rsi "QQQ" {:window 10}) 32)
                       [(weight-equal
                         [(filter
                           (rsi {:window 10})
                           (select-bottom 1)
                           [(asset "TQQQ" "ProShares UltraPro QQQ")
                            (asset
                             "BSV"
                             "Vanguard Short-Term Bond ETF")])])]
                       [(weight-equal
                         [(if
                           (> (max-drawdown "QQQ" {:window 12}) 6)
                           [(group
                             "Risk Off"
                             [(weight-equal
                               [(filter
                                 (moving-average-return {:window 25})
                                 (select-bottom 1)
                                 [(asset
                                   "DBMF"
                                   "iMGP DBi Managed Futures Strategy ETF")
                                  (asset
                                   "SQQQ"
                                   "ProShares UltraPro Short QQQ")])])])]
                           [(weight-equal
                             [(if
                               (> (max-drawdown "TMF" {:window 10}) 7)
                               [(weight-equal
                                 [(filter
                                   (rsi {:window 20})
                                   (select-bottom 1)
                                   [(asset
                                     "DBMF"
                                     "iMGP DBi Managed Futures Strategy ETF")
                                    (asset
                                     "TMV"
                                     "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])]
                               [(weight-inverse-volatility
                                 45
                                 [(asset
                                   "TMF"
                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                  (asset
                                   "FAS"
                                   "Direxion Daily Financial Bull 3x Shares")
                                  (asset
                                   "TQQQ"
                                   "ProShares UltraPro QQQ")
                                  (asset
                                   "CURE"
                                   "Direxion Daily Healthcare Bull 3x Shares")
                                  (asset
                                   "SOXL"
                                   "Direxion Daily Semiconductor Bull 3x Shares")
                                  (asset
                                   "UPRO"
                                   "ProShares UltraPro S&P500")
                                  (asset
                                   "LABU"
                                   "Direxion Daily S&P Biotech Bull 3X Shares")])])])])])])])])])])])])
          (group
           "Commo Macro/(TMF/TMV/Gold Momentum)"
           [(weight-equal
             [(group
               "TMF/TMV/Gold Momentum"
               [(weight-equal
                 [(group
                   "TMV Momentum"
                   [(weight-equal
                     [(if
                       (< (rsi "TMF" {:window 10}) 32)
                       [(asset
                         "TMF"
                         "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                       [(weight-equal
                         [(if
                           (>
                            (moving-average-price "TMV" {:window 15})
                            (moving-average-price "TMV" {:window 50}))
                           [(weight-equal
                             [(if
                               (>
                                (current-price "TMV")
                                (moving-average-price
                                 "TMV"
                                 {:window 135}))
                               [(weight-equal
                                 [(if
                                   (> (rsi "TMV" {:window 10}) 71)
                                   [(asset
                                     "SHV"
                                     "iShares Short Treasury Bond ETF")]
                                   [(weight-equal
                                     [(if
                                       (> (rsi "TMV" {:window 60}) 59)
                                       [(asset
                                         "TLT"
                                         "iShares 20+ Year Treasury Bond ETF")]
                                       [(asset
                                         "TMV"
                                         "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                               [(asset
                                 "BND"
                                 "Vanguard Total Bond Market ETF")])])]
                           [(asset
                             "BND"
                             "Vanguard Total Bond Market ETF")])])])])])
                  (group
                   "TMF Momentum"
                   [(weight-specified
                     1
                     (if
                      (< (rsi "TMF" {:window 10}) 32)
                      [(asset
                        "TMF"
                        "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                      [(weight-equal
                        [(if
                          (>
                           (moving-average-price "TLT" {:window 15})
                           (moving-average-price "TLT" {:window 50}))
                          [(weight-equal
                            [(if
                              (> (rsi "TMF" {:window 10}) 72)
                              [(asset
                                "SHV"
                                "iShares Short Treasury Bond ETF")]
                              [(weight-equal
                                [(if
                                  (> (rsi "TMF" {:window 60}) 57)
                                  [(asset
                                    "TBF"
                                    "Proshares Short 20+ Year Treasury")]
                                  [(asset
                                    "TMF"
                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])]
                          [(asset
                            "SHV"
                            "iShares Short Treasury Bond ETF")])])]))])
                  (group
                   "Gold Momentum"
                   [(weight-equal
                     [(if
                       (>
                        (moving-average-price "GLD" {:window 200})
                        (moving-average-price "GLD" {:window 350}))
                       [(weight-equal
                         [(if
                           (>
                            (moving-average-price "GLD" {:window 60})
                            (moving-average-price "GLD" {:window 150}))
                           [(asset "GLD" nil)]
                           [(asset "SHV" nil)])])]
                       [(asset "SHV" nil)])])])])])
              (group
               "Commodities Macro Momentum"
               [(weight-equal
                 [(if
                   (< (rsi "DBC" {:window 10}) 17)
                   [(asset
                     "DBC"
                     "Invesco DB Commodity Index Tracking Fund")]
                   [(weight-equal
                     [(if
                       (>
                        (moving-average-price "DBC" {:window 100})
                        (moving-average-price "DBC" {:window 252}))
                       [(weight-equal
                         [(if
                           (>
                            (moving-average-price "DBC" {:window 50})
                            (moving-average-price "DBC" {:window 100}))
                           [(weight-equal
                             [(if
                               (> (rsi "DBC" {:window 60}) 60)
                               [(asset
                                 "SHV"
                                 "iShares Short Treasury Bond ETF")]
                               [(asset
                                 "DBC"
                                 "Invesco DB Commodity Index Tracking Fund")])])]
                           [(asset
                             "SHV"
                             "iShares Short Treasury Bond ETF")])])]
                       [(asset
                         "SHV"
                         "iShares Short Treasury Bond ETF")])])])])])])])])])])]
   [(asset
     "BIL"
     "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])
  0.2
  (weight-equal
   [(group
     "Interest Rate Linked & Wrap Soxl Crash Catcher"
     [(weight-equal
       [(group
         "Vol Catcher Wraps SOXL Twice(26%, 26% DD)"
         [(weight-equal
           [(if
             (> (rsi "UVXY" {:window 21}) 63)
             [(weight-equal
               [(if
                 (> (rsi "UVXY" {:window 10}) 74)
                 [(weight-equal
                   [(if
                     (< (rsi "UVXY" {:window 10}) 84)
                     [(weight-equal
                       [(if
                         (< (cumulative-return "UVXY" {:window 2}) 4.5)
                         [(asset
                           "SPXS"
                           "Direxion Daily S&P 500 Bear 3x Shares")]
                         [(asset
                           "UVXY"
                           "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")
                          (asset
                           "BIL"
                           "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                     [(weight-equal
                       [(if
                         (< (rsi "SOXL" {:window 14}) 30)
                         [(asset
                           "SOXL"
                           "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                         [(asset
                           "BIL"
                           "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                 [(weight-equal
                   [(if
                     (< (rsi "SOXL" {:window 14}) 30)
                     [(asset
                       "SOXL"
                       "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                     [(asset
                       "BIL"
                       "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
             [(group
               "High Win Rates + Anansi's Scale-in"
               [(weight-equal
                 [(if
                   (> (rsi "IOO" {:window 10}) 80)
                   [(group
                     "Scale-In | VIX+ -> VIX++"
                     [(weight-equal
                       [(if
                         (> (rsi "IOO" {:window 10}) 82.5)
                         [(group
                           "VIX Blend++"
                           [(weight-equal
                             [(asset "UVXY" nil)
                              (asset "UVXY" nil)
                              (asset "UVXY" nil)])])]
                         [(group
                           "VIX Blend+"
                           [(weight-equal
                             [(asset "UVXY" nil)
                              (asset "UVXY" nil)
                              (asset "UVXY" nil)])])])])])]
                   [(weight-equal
                     [(if
                       (> (rsi "TQQQ" {:window 10}) 81)
                       [(weight-equal
                         [(if
                           (> (rsi "UVXY" {:window 60}) 40)
                           [(asset "UVXY" nil)]
                           [(weight-equal
                             [(if
                               (> (rsi "RETL" {:window 10}) 82)
                               [(group
                                 "Scale-In | BTAL -> VIX"
                                 [(weight-equal
                                   [(if
                                     (> (rsi "RETL" {:window 10}) 85)
                                     [(group
                                       "VIX Blend"
                                       [(weight-equal
                                         [(asset "UVXY" nil)
                                          (asset "UVXY" nil)
                                          (asset "UVXY" nil)])])]
                                     [(group
                                       "BTAL/BIL"
                                       [(weight-equal
                                         [(asset "BTAL" nil)
                                          (asset "SHV" nil)])])])])])]
                               [(weight-equal
                                 [(if
                                   (> (rsi "XLF" {:window 10}) 81)
                                   [(group
                                     "Scale-In | VIX -> VIX+"
                                     [(weight-equal
                                       [(if
                                         (>
                                          (rsi "XLF" {:window 10})
                                          85)
                                         [(group
                                           "VIX Blend+"
                                           [(weight-equal
                                             [(asset "UVXY" nil)
                                              (asset "UVXY" nil)
                                              (asset "UVXY" nil)])])]
                                         [(group
                                           "VIX Blend"
                                           [(weight-equal
                                             [(asset "UVXY" nil)
                                              (asset "UVXY" nil)
                                              (asset
                                               "UVXY"
                                               nil)])])])])])]
                                   [(weight-equal
                                     [(asset "SHV" nil)])])])])])])])]
                       [(weight-equal
                         [(if
                           (> (rsi "SPY" {:window 10}) 80)
                           [(weight-equal
                             [(if
                               (> (rsi "UVXY" {:window 60}) 40)
                               [(asset "UVXY" nil)]
                               [(weight-equal
                                 [(if
                                   (> (rsi "RETL" {:window 10}) 82)
                                   [(group
                                     "Scale-In | BTAL -> VIX"
                                     [(weight-equal
                                       [(if
                                         (>
                                          (rsi "RETL" {:window 10})
                                          85)
                                         [(group
                                           "VIX Blend"
                                           [(weight-equal
                                             [(asset "UVXY" nil)
                                              (asset "UVXY" nil)
                                              (asset "UVXY" nil)])])]
                                         [(group
                                           "BTAL/BIL"
                                           [(weight-equal
                                             [(asset "BTAL" nil)
                                              (asset
                                               "SHV"
                                               nil)])])])])])]
                                   [(weight-equal
                                     [(if
                                       (> (rsi "XLF" {:window 10}) 81)
                                       [(group
                                         "Scale-In | VIX -> VIX+"
                                         [(weight-equal
                                           [(if
                                             (>
                                              (rsi "XLF" {:window 10})
                                              85)
                                             [(group
                                               "VIX Blend+"
                                               [(weight-equal
                                                 [(asset "UVXY" nil)
                                                  (asset "UVXY" nil)
                                                  (asset
                                                   "UVXY"
                                                   nil)])])]
                                             [(group
                                               "VIX Blend"
                                               [(weight-equal
                                                 [(asset "UVXY" nil)
                                                  (asset "UVXY" nil)
                                                  (asset
                                                   "UVXY"
                                                   nil)])])])])])]
                                       [(weight-equal
                                         [(asset
                                           "SHV"
                                           nil)])])])])])])])]
                           [(weight-equal
                             [(if
                               (< (rsi "SOXL" {:window 14}) 30)
                               [(asset
                                 "SOXL"
                                 "Direxion Daily Semiconductor Bull 3x Shares")]
                               [(weight-equal
                                 [(if
                                   (< (rsi "TECL" {:window 14}) 30)
                                   [(asset
                                     "TECL"
                                     "Direxion Daily Technology Bull 3x Shares")]
                                   [(weight-equal
                                     [(if
                                       (< (rsi "LABU" {:window 10}) 22)
                                       [(weight-equal
                                         [(filter
                                           (cumulative-return
                                            {:window 1})
                                           (select-bottom 1)
                                           [(asset
                                             "LABU"
                                             "Direxion Daily S&P Biotech Bull 3X Shares")
                                            (asset
                                             "SOXL"
                                             "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                       [(weight-equal
                                         [(if
                                           (<
                                            (rsi "QQQ" {:window 14})
                                            30)
                                           [(asset
                                             "TECL"
                                             "Direxion Daily Technology Bull 3x Shares")]
                                           [(weight-equal
                                             [(if
                                               (<
                                                (rsi
                                                 "SMH"
                                                 {:window 10})
                                                25)
                                               [(asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")]
                                               [(weight-equal
                                                 [(if
                                                   (>
                                                    (rsi
                                                     "TQQQ"
                                                     {:window 14})
                                                    80)
                                                   [(asset
                                                     "TECS"
                                                     "Direxion Daily Technology Bear 3X Shares")]
                                                   [(weight-equal
                                                     [(if
                                                       (>
                                                        (rsi
                                                         "SOXL"
                                                         {:window 14})
                                                        80)
                                                       [(asset
                                                         "SOXS"
                                                         "Direxion Daily Semiconductor Bear 3x Shares")]
                                                       [(weight-equal
                                                         [(if
                                                           (>
                                                            (rsi
                                                             "TMV"
                                                             {:window
                                                              14})
                                                            80)
                                                           [(asset
                                                             "TMF"
                                                             nil)]
                                                           [(weight-equal
                                                             [(if
                                                               (>
                                                                (rsi
                                                                 "SMH"
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
                                                                     "RETL"
                                                                     {:window
                                                                      10})
                                                                    82)
                                                                   [(group
                                                                     "Scale-In | BTAL -> VIX"
                                                                     [(weight-equal
                                                                       [(if
                                                                         (>
                                                                          (rsi
                                                                           "RETL"
                                                                           {:window
                                                                            10})
                                                                          85)
                                                                         [(group
                                                                           "VIX Blend"
                                                                           [(weight-equal
                                                                             [(asset
                                                                               "UVXY"
                                                                               nil)
                                                                              (asset
                                                                               "UVXY"
                                                                               nil)
                                                                              (asset
                                                                               "UVXY"
                                                                               nil)])])]
                                                                         [(group
                                                                           "BTAL/BIL"
                                                                           [(weight-equal
                                                                             [(asset
                                                                               "BTAL"
                                                                               nil)
                                                                              (asset
                                                                               "SHV"
                                                                               nil)])])])])])]
                                                                   [(weight-equal
                                                                     [(if
                                                                       (>
                                                                        (rsi
                                                                         "XLF"
                                                                         {:window
                                                                          10})
                                                                        81)
                                                                       [(group
                                                                         "Scale-In | VIX -> VIX+"
                                                                         [(weight-equal
                                                                           [(if
                                                                             (>
                                                                              (rsi
                                                                               "XLF"
                                                                               {:window
                                                                                10})
                                                                              85)
                                                                             [(group
                                                                               "VIX Blend+"
                                                                               [(weight-equal
                                                                                 [(asset
                                                                                   "UVXY"
                                                                                   nil)
                                                                                  (asset
                                                                                   "UVXY"
                                                                                   nil)
                                                                                  (asset
                                                                                   "UVXY"
                                                                                   nil)])])]
                                                                             [(group
                                                                               "VIX Blend"
                                                                               [(weight-equal
                                                                                 [(asset
                                                                                   "UVXY"
                                                                                   nil)
                                                                                  (asset
                                                                                   "UVXY"
                                                                                   nil)
                                                                                  (asset
                                                                                   "UVXY"
                                                                                   nil)])])])])])]
                                                                       [(weight-equal
                                                                         [(if
                                                                           (>
                                                                            (rsi
                                                                             "SPY"
                                                                             {:window
                                                                              10})
                                                                            80)
                                                                           [(group
                                                                             "VIX Blend++"
                                                                             [(weight-equal
                                                                               [(asset
                                                                                 "UVXY"
                                                                                 nil)
                                                                                (asset
                                                                                 "UVXY"
                                                                                 nil)
                                                                                (asset
                                                                                 "UVXY"
                                                                                 nil)])])]
                                                                           [(weight-equal
                                                                             [(if
                                                                               (>
                                                                                (rsi
                                                                                 "IOO"
                                                                                 {:window
                                                                                  10})
                                                                                80)
                                                                               [(group
                                                                                 "Scale-In | VIX+ -> VIX++"
                                                                                 [(weight-equal
                                                                                   [(if
                                                                                     (>
                                                                                      (rsi
                                                                                       "IOO"
                                                                                       {:window
                                                                                        10})
                                                                                      82.5)
                                                                                     [(group
                                                                                       "VIX Blend++"
                                                                                       [(weight-equal
                                                                                         [(asset
                                                                                           "UVXY"
                                                                                           nil)
                                                                                          (asset
                                                                                           "UVXY"
                                                                                           nil)
                                                                                          (asset
                                                                                           "UVXY"
                                                                                           nil)])])]
                                                                                     [(group
                                                                                       "VIX Blend+"
                                                                                       [(weight-equal
                                                                                         [(asset
                                                                                           "UVXY"
                                                                                           nil)
                                                                                          (asset
                                                                                           "UVXY"
                                                                                           nil)
                                                                                          (asset
                                                                                           "UVXY"
                                                                                           nil)])])])])])]
                                                                               [(weight-equal
                                                                                 [(if
                                                                                   (>
                                                                                    (rsi
                                                                                     "QQQ"
                                                                                     {:window
                                                                                      10})
                                                                                    79)
                                                                                   [(group
                                                                                     "Scale-In | VIX+ -> VIX++"
                                                                                     [(weight-equal
                                                                                       [(if
                                                                                         (>
                                                                                          (rsi
                                                                                           "QQQ"
                                                                                           {:window
                                                                                            10})
                                                                                          82.5)
                                                                                         [(group
                                                                                           "VIX Blend++"
                                                                                           [(weight-equal
                                                                                             [(asset
                                                                                               "UVXY"
                                                                                               nil)
                                                                                              (asset
                                                                                               "UVXY"
                                                                                               nil)
                                                                                              (asset
                                                                                               "UVXY"
                                                                                               nil)])])]
                                                                                         [(group
                                                                                           "VIX Blend+"
                                                                                           [(weight-equal
                                                                                             [(asset
                                                                                               "UVXY"
                                                                                               nil)
                                                                                              (asset
                                                                                               "UVXY"
                                                                                               nil)
                                                                                              (asset
                                                                                               "UVXY"
                                                                                               nil)])])])])])]
                                                                                   [(weight-equal
                                                                                     [(if
                                                                                       (>
                                                                                        (rsi
                                                                                         "VTV"
                                                                                         {:window
                                                                                          10})
                                                                                        79)
                                                                                       [(group
                                                                                         "VIX Blend"
                                                                                         [(weight-equal
                                                                                           [(asset
                                                                                             "UVXY"
                                                                                             nil)
                                                                                            (asset
                                                                                             "UVXY"
                                                                                             nil)
                                                                                            (asset
                                                                                             "UVXY"
                                                                                             nil)])])]
                                                                                       [(weight-equal
                                                                                         [(if
                                                                                           (>
                                                                                            (rsi
                                                                                             "XLP"
                                                                                             {:window
                                                                                              10})
                                                                                            77)
                                                                                           [(group
                                                                                             "VIX Blend"
                                                                                             [(weight-equal
                                                                                               [(asset
                                                                                                 "UVXY"
                                                                                                 nil)
                                                                                                (asset
                                                                                                 "UVXY"
                                                                                                 nil)
                                                                                                (asset
                                                                                                 "UVXY"
                                                                                                 nil)])])]
                                                                                           [(weight-equal
                                                                                             [(if
                                                                                               (>
                                                                                                (rsi
                                                                                                 "XLF"
                                                                                                 {:window
                                                                                                  10})
                                                                                                81)
                                                                                               [(group
                                                                                                 "VIX Blend"
                                                                                                 [(weight-equal
                                                                                                   [(asset
                                                                                                     "UVXY"
                                                                                                     nil)
                                                                                                    (asset
                                                                                                     "UVXY"
                                                                                                     nil)
                                                                                                    (asset
                                                                                                     "UVXY"
                                                                                                     nil)])])]
                                                                                               [(weight-equal
                                                                                                 [(if
                                                                                                   (>
                                                                                                    (rsi
                                                                                                     "SPY"
                                                                                                     {:window
                                                                                                      70})
                                                                                                    62)
                                                                                                   [(group
                                                                                                     "Overbought"
                                                                                                     [(weight-equal
                                                                                                       [(group
                                                                                                         "15/15"
                                                                                                         [(weight-equal
                                                                                                           [(if
                                                                                                             (>
                                                                                                              (rsi
                                                                                                               "AGG"
                                                                                                               {:window
                                                                                                                15})
                                                                                                              (rsi
                                                                                                               "QQQ"
                                                                                                               {:window
                                                                                                                15}))
                                                                                                             [(group
                                                                                                               "Ticker Mixer"
                                                                                                               [(weight-equal
                                                                                                                 [(group
                                                                                                                   "Pick Top 3"
                                                                                                                   [(weight-equal
                                                                                                                     [(filter
                                                                                                                       (moving-average-return
                                                                                                                        {:window
                                                                                                                         15})
                                                                                                                       (select-top
                                                                                                                        3)
                                                                                                                       [(asset
                                                                                                                         "SPXL"
                                                                                                                         nil)
                                                                                                                        (asset
                                                                                                                         "TQQQ"
                                                                                                                         nil)
                                                                                                                        (asset
                                                                                                                         "TECL"
                                                                                                                         nil)
                                                                                                                        (asset
                                                                                                                         "SOXL"
                                                                                                                         nil)
                                                                                                                        (asset
                                                                                                                         "TQQQ"
                                                                                                                         "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])])
                                                                                                                  (asset
                                                                                                                   "TQQQ"
                                                                                                                   nil)])])]
                                                                                                             [(group
                                                                                                               "GLD/SLV/DBC"
                                                                                                               [(weight-specified
                                                                                                                 0.5
                                                                                                                 (asset
                                                                                                                  "GLD"
                                                                                                                  nil)
                                                                                                                 0.25
                                                                                                                 (asset
                                                                                                                  "SLV"
                                                                                                                  nil)
                                                                                                                 0.25
                                                                                                                 (asset
                                                                                                                  "DBC"
                                                                                                                  nil))])])])])
                                                                                                        (group
                                                                                                         "VIX Stuff"
                                                                                                         [(weight-equal
                                                                                                           [(if
                                                                                                             (>
                                                                                                              (rsi
                                                                                                               "QQQ"
                                                                                                               {:window
                                                                                                                90})
                                                                                                              60)
                                                                                                             [(asset
                                                                                                               "UVXY"
                                                                                                               nil)]
                                                                                                             [(weight-equal
                                                                                                               [(if
                                                                                                                 (>
                                                                                                                  (rsi
                                                                                                                   "QQQ"
                                                                                                                   {:window
                                                                                                                    14})
                                                                                                                  80)
                                                                                                                 [(asset
                                                                                                                   "UVXY"
                                                                                                                   nil)]
                                                                                                                 [(weight-equal
                                                                                                                   [(if
                                                                                                                     (>
                                                                                                                      (rsi
                                                                                                                       "QQQ"
                                                                                                                       {:window
                                                                                                                        5})
                                                                                                                      90)
                                                                                                                     [(asset
                                                                                                                       "UVXY"
                                                                                                                       nil)]
                                                                                                                     [(weight-equal
                                                                                                                       [(if
                                                                                                                         (>
                                                                                                                          (rsi
                                                                                                                           "QQQ"
                                                                                                                           {:window
                                                                                                                            3})
                                                                                                                          95)
                                                                                                                         [(asset
                                                                                                                           "UVXY"
                                                                                                                           nil)]
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
                                                                                                                               "SVXY"
                                                                                                                               nil)]
                                                                                                                             [(asset
                                                                                                                               "SLV"
                                                                                                                               nil)])])])])])])])])])])])])])]
                                                                                                   [(weight-equal
                                                                                                     [(if
                                                                                                       (>
                                                                                                        (cumulative-return
                                                                                                         "VIXY"
                                                                                                         {:window
                                                                                                          9})
                                                                                                        20)
                                                                                                       [(group
                                                                                                         "High VIX"
                                                                                                         [(weight-equal
                                                                                                           [(if
                                                                                                             (>
                                                                                                              (current-price
                                                                                                               "SPY")
                                                                                                              (moving-average-price
                                                                                                               "SPY"
                                                                                                               {:window
                                                                                                                200}))
                                                                                                             [(weight-equal
                                                                                                               [(if
                                                                                                                 (>
                                                                                                                  (rsi
                                                                                                                   "UVXY"
                                                                                                                   {:window
                                                                                                                    21})
                                                                                                                  65)
                                                                                                                 [(weight-equal
                                                                                                                   [(group
                                                                                                                     "BSC 31 RSI"
                                                                                                                     [(weight-equal
                                                                                                                       [(if
                                                                                                                         (>
                                                                                                                          (rsi
                                                                                                                           "SPY"
                                                                                                                           {:window
                                                                                                                            10})
                                                                                                                          31)
                                                                                                                         [(weight-equal
                                                                                                                           [(if
                                                                                                                             (>
                                                                                                                              (max-drawdown
                                                                                                                               "SVXY"
                                                                                                                               {:window
                                                                                                                                5})
                                                                                                                              15)
                                                                                                                             [(group
                                                                                                                               "UVIX Volatility"
                                                                                                                               [(weight-specified
                                                                                                                                 0.1
                                                                                                                                 (asset
                                                                                                                                  "UVXY"
                                                                                                                                  "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")
                                                                                                                                 0.9
                                                                                                                                 (asset
                                                                                                                                  "BTAL"
                                                                                                                                  "AGF U.S. Market Neutral Anti-Beta Fund"))])]
                                                                                                                             [(group
                                                                                                                               "UVXY Volatility"
                                                                                                                               [(weight-specified
                                                                                                                                 0.1
                                                                                                                                 (asset
                                                                                                                                  "UVXY"
                                                                                                                                  "ProShares Ultra VIX Short-Term Futures ETF")
                                                                                                                                 0.3
                                                                                                                                 (group
                                                                                                                                  "VIX Mix"
                                                                                                                                  [(weight-equal
                                                                                                                                    [(filter
                                                                                                                                      (moving-average-return
                                                                                                                                       {:window
                                                                                                                                        10})
                                                                                                                                      (select-bottom
                                                                                                                                       2)
                                                                                                                                      [(asset
                                                                                                                                        "SOXS"
                                                                                                                                        "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                                                                       (asset
                                                                                                                                        "TECS"
                                                                                                                                        "Direxion Daily Technology Bear 3X Shares")
                                                                                                                                       (asset
                                                                                                                                        "SQQQ"
                                                                                                                                        "ProShares UltraPro Short QQQ")
                                                                                                                                       (asset
                                                                                                                                        "DUG"
                                                                                                                                        "ProShares Trust - ProShares UltraShort Energy")
                                                                                                                                       (asset
                                                                                                                                        "TMV"
                                                                                                                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                                                                                       (asset
                                                                                                                                        "FAZ"
                                                                                                                                        "Direxion Daily Financial Bear 3X Shares")
                                                                                                                                       (asset
                                                                                                                                        "DRV"
                                                                                                                                        "Direxion Daily Real Estate Bear 3X Shares")
                                                                                                                                       (asset
                                                                                                                                        "EDZ"
                                                                                                                                        "Direxion Daily MSCI Emerging Markets Bear 3X Shares")
                                                                                                                                       (asset
                                                                                                                                        "DXD"
                                                                                                                                        "ProShares UltraShort Dow30")
                                                                                                                                       (asset
                                                                                                                                        "SPXS"
                                                                                                                                        "Direxion Daily S&P 500 Bear 3x Shares")
                                                                                                                                       (asset
                                                                                                                                        "SDOW"
                                                                                                                                        "ProShares UltraPro Short Dow30")
                                                                                                                                       (asset
                                                                                                                                        "SQQQ"
                                                                                                                                        "ProShares Trust - ProShares UltraPro Short QQQ -3x Shares")])])])
                                                                                                                                 0.6
                                                                                                                                 (asset
                                                                                                                                  "BTAL"
                                                                                                                                  "AGF U.S. Market Neutral Anti-Beta Fund"))])])])]
                                                                                                                         [(group
                                                                                                                           "SVXY"
                                                                                                                           [(weight-equal
                                                                                                                             [(if
                                                                                                                               (>
                                                                                                                                (max-drawdown
                                                                                                                                 "SVXY"
                                                                                                                                 {:window
                                                                                                                                  3})
                                                                                                                                20)
                                                                                                                               [(group
                                                                                                                                 "Volmageddon Protection"
                                                                                                                                 [(weight-equal
                                                                                                                                   [(asset
                                                                                                                                     "BTAL"
                                                                                                                                     "AGF U.S. Market Neutral Anti-Beta Fund")
                                                                                                                                    (asset
                                                                                                                                     "USMV"
                                                                                                                                     "iShares MSCI USA Min Vol Factor ETF")
                                                                                                                                    (group
                                                                                                                                     "SVIX/SVXY"
                                                                                                                                     [(weight-equal
                                                                                                                                       [(if
                                                                                                                                         (>
                                                                                                                                          (cumulative-return
                                                                                                                                           "SVXY"
                                                                                                                                           {:window
                                                                                                                                            1})
                                                                                                                                          5)
                                                                                                                                         [(asset
                                                                                                                                           "SVXY"
                                                                                                                                           "ProShares Trust - ProShares Short VIX Short-Term Futures ETF -1x Shares")]
                                                                                                                                         [(asset
                                                                                                                                           "SVXY"
                                                                                                                                           "ProShares Short VIX Short-Term Futures ETF")])])])])])]
                                                                                                                               [(weight-equal
                                                                                                                                 [(if
                                                                                                                                   (>
                                                                                                                                    (cumulative-return
                                                                                                                                     "VIXY"
                                                                                                                                     {:window
                                                                                                                                      5})
                                                                                                                                    45)
                                                                                                                                   [(asset
                                                                                                                                     "SVXY"
                                                                                                                                     "ProShares Trust - ProShares Short VIX Short-Term Futures ETF -1x Shares")]
                                                                                                                                   [(asset
                                                                                                                                     "SVXY"
                                                                                                                                     nil)
                                                                                                                                    (group
                                                                                                                                     "Inverse VIX Mix"
                                                                                                                                     [(weight-equal
                                                                                                                                       [(filter
                                                                                                                                         (moving-average-return
                                                                                                                                          {:window
                                                                                                                                           10})
                                                                                                                                         (select-bottom
                                                                                                                                          2)
                                                                                                                                         [(asset
                                                                                                                                           "QLD"
                                                                                                                                           "ProShares Ultra QQQ")
                                                                                                                                          (asset
                                                                                                                                           "UYG"
                                                                                                                                           "ProShares Ultra Financials")
                                                                                                                                          (asset
                                                                                                                                           "SAA"
                                                                                                                                           "ProShares Ultra SmallCap600")
                                                                                                                                          (asset
                                                                                                                                           "EFO"
                                                                                                                                           "ProShares Ultra MSCI EAFE")
                                                                                                                                          (asset
                                                                                                                                           "SSO"
                                                                                                                                           "ProShares Ultra S&P 500")
                                                                                                                                          (asset
                                                                                                                                           "UDOW"
                                                                                                                                           "ProShares UltraPro Dow30")
                                                                                                                                          (asset
                                                                                                                                           "UWM"
                                                                                                                                           "ProShares Ultra Russell2000")
                                                                                                                                          (asset
                                                                                                                                           "ROM"
                                                                                                                                           "ProShares Ultra Technology")
                                                                                                                                          (asset
                                                                                                                                           "ERX"
                                                                                                                                           "Direxion Daily Energy Bull 2x Shares")])])])])])])])])])])])])]
                                                                                                                 [(weight-equal
                                                                                                                   [(group
                                                                                                                     "SVXY"
                                                                                                                     [(weight-equal
                                                                                                                       [(if
                                                                                                                         (>
                                                                                                                          (max-drawdown
                                                                                                                           "SVXY"
                                                                                                                           {:window
                                                                                                                            3})
                                                                                                                          20)
                                                                                                                         [(group
                                                                                                                           "Volmageddon Protection"
                                                                                                                           [(weight-equal
                                                                                                                             [(asset
                                                                                                                               "BTAL"
                                                                                                                               "AGF U.S. Market Neutral Anti-Beta Fund")
                                                                                                                              (asset
                                                                                                                               "USMV"
                                                                                                                               "iShares MSCI USA Min Vol Factor ETF")
                                                                                                                              (group
                                                                                                                               "SVIX/SVXY"
                                                                                                                               [(weight-equal
                                                                                                                                 [(if
                                                                                                                                   (>
                                                                                                                                    (cumulative-return
                                                                                                                                     "SVXY"
                                                                                                                                     {:window
                                                                                                                                      1})
                                                                                                                                    5)
                                                                                                                                   [(asset
                                                                                                                                     "SVXY"
                                                                                                                                     "ProShares Trust - ProShares Short VIX Short-Term Futures ETF -1x Shares")]
                                                                                                                                   [(asset
                                                                                                                                     "SVXY"
                                                                                                                                     "ProShares Short VIX Short-Term Futures ETF")])])])])])]
                                                                                                                         [(weight-equal
                                                                                                                           [(if
                                                                                                                             (>
                                                                                                                              (cumulative-return
                                                                                                                               "VIXY"
                                                                                                                               {:window
                                                                                                                                5})
                                                                                                                              45)
                                                                                                                             [(asset
                                                                                                                               "SVXY"
                                                                                                                               "ProShares Trust - ProShares Short VIX Short-Term Futures ETF -1x Shares")]
                                                                                                                             [(asset
                                                                                                                               "SVXY"
                                                                                                                               nil)
                                                                                                                              (group
                                                                                                                               "Inverse VIX Mix"
                                                                                                                               [(weight-equal
                                                                                                                                 [(filter
                                                                                                                                   (moving-average-return
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   (select-bottom
                                                                                                                                    2)
                                                                                                                                   [(asset
                                                                                                                                     "QLD"
                                                                                                                                     "ProShares Ultra QQQ")
                                                                                                                                    (asset
                                                                                                                                     "UYG"
                                                                                                                                     "ProShares Ultra Financials")
                                                                                                                                    (asset
                                                                                                                                     "SAA"
                                                                                                                                     "ProShares Ultra SmallCap600")
                                                                                                                                    (asset
                                                                                                                                     "EFO"
                                                                                                                                     "ProShares Ultra MSCI EAFE")
                                                                                                                                    (asset
                                                                                                                                     "SSO"
                                                                                                                                     "ProShares Ultra S&P 500")
                                                                                                                                    (asset
                                                                                                                                     "UDOW"
                                                                                                                                     "ProShares UltraPro Dow30")
                                                                                                                                    (asset
                                                                                                                                     "UWM"
                                                                                                                                     "ProShares Ultra Russell2000")
                                                                                                                                    (asset
                                                                                                                                     "ROM"
                                                                                                                                     "ProShares Ultra Technology")
                                                                                                                                    (asset
                                                                                                                                     "ERX"
                                                                                                                                     "Direxion Daily Energy Bull 2x Shares")])])])])])])])])])])])]
                                                                                                             [(weight-equal
                                                                                                               [(if
                                                                                                                 (<
                                                                                                                  (rsi
                                                                                                                   "TQQQ"
                                                                                                                   {:window
                                                                                                                    10})
                                                                                                                  31)
                                                                                                                 [(group
                                                                                                                   "Pick Bottom 3 | 1.5x"
                                                                                                                   [(weight-equal
                                                                                                                     [(filter
                                                                                                                       (moving-average-return
                                                                                                                        {:window
                                                                                                                         10})
                                                                                                                       (select-bottom
                                                                                                                        3)
                                                                                                                       [(asset
                                                                                                                         "SPXL"
                                                                                                                         nil)
                                                                                                                        (asset
                                                                                                                         "TQQQ"
                                                                                                                         nil)
                                                                                                                        (asset
                                                                                                                         "TECL"
                                                                                                                         nil)
                                                                                                                        (asset
                                                                                                                         "SOXL"
                                                                                                                         nil)])
                                                                                                                      (filter
                                                                                                                       (moving-average-return
                                                                                                                        {:window
                                                                                                                         10})
                                                                                                                       (select-bottom
                                                                                                                        3)
                                                                                                                       [(asset
                                                                                                                         "SPY"
                                                                                                                         nil)
                                                                                                                        (asset
                                                                                                                         "QQQ"
                                                                                                                         nil)
                                                                                                                        (asset
                                                                                                                         "XLK"
                                                                                                                         nil)
                                                                                                                        (asset
                                                                                                                         "SOXX"
                                                                                                                         nil)])])])]
                                                                                                                 [(weight-equal
                                                                                                                   [(if
                                                                                                                     (>
                                                                                                                      (cumulative-return
                                                                                                                       "VIXY"
                                                                                                                       {:window
                                                                                                                        10})
                                                                                                                      25)
                                                                                                                     [(group
                                                                                                                       "Volmageddon Protection"
                                                                                                                       [(weight-equal
                                                                                                                         [(asset
                                                                                                                           "BTAL"
                                                                                                                           "AGF U.S. Market Neutral Anti-Beta Fund")
                                                                                                                          (asset
                                                                                                                           "USMV"
                                                                                                                           "iShares MSCI USA Min Vol Factor ETF")])])]
                                                                                                                     [(group
                                                                                                                       "Inverse VIX Mix"
                                                                                                                       [(weight-equal
                                                                                                                         [(filter
                                                                                                                           (moving-average-return
                                                                                                                            {:window
                                                                                                                             10})
                                                                                                                           (select-bottom
                                                                                                                            2)
                                                                                                                           [(asset
                                                                                                                             "QLD"
                                                                                                                             "ProShares Ultra QQQ")
                                                                                                                            (asset
                                                                                                                             "UYG"
                                                                                                                             "ProShares Ultra Financials")
                                                                                                                            (asset
                                                                                                                             "SAA"
                                                                                                                             "ProShares Ultra SmallCap600")
                                                                                                                            (asset
                                                                                                                             "EFO"
                                                                                                                             "ProShares Ultra MSCI EAFE")
                                                                                                                            (asset
                                                                                                                             "SSO"
                                                                                                                             "ProShares Ultra S&P 500")
                                                                                                                            (asset
                                                                                                                             "UDOW"
                                                                                                                             "ProShares UltraPro Dow30")
                                                                                                                            (asset
                                                                                                                             "UWM"
                                                                                                                             "ProShares Ultra Russell2000")
                                                                                                                            (asset
                                                                                                                             "ROM"
                                                                                                                             "ProShares Ultra Technology")
                                                                                                                            (asset
                                                                                                                             "ERX"
                                                                                                                             "Direxion Daily Energy Bull 2x Shares")])])])])])])])])])])]
                                                                                                       [(asset
                                                                                                         "BIL"
                                                                                                         "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])))
