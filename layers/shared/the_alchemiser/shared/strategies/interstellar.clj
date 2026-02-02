(defsymphony
 "Interstellar (Public Copy)"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "V12"
    [(weight-equal
      [(weight-specified
        0.0444
        (group
         "TQQQ FTLT"
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
                                 (moving-average-return {:window 15})
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
                                   "VTI"
                                   "Vanguard Total Stock Market ETF")
                                  (asset
                                   "IWM"
                                   "iShares Russell 2000 ETF")
                                  (asset
                                   "SCO"
                                   "ProShares UltraShort Bloomberg Crude Oil")])])]
                             [(weight-specified
                               0.67
                               (filter
                                (moving-average-return {:window 21})
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
                                 (asset "FNGU" nil)
                                 (asset
                                  "BULZ"
                                  "MicroSectors Solactive FANG & Innovation 3X Leveraged ETN")])
                               0.33
                               (asset
                                "SVXY"
                                "ProShares Short VIX Short-Term Futures ETF"))])])])])])])])])]
             [(weight-equal
               [(group
                 "Dip Buy Strategy"
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
                             (< (rsi "FNGS" {:window 10}) 30)
                             [(asset "FNGU" nil)]
                             [(weight-equal
                               [(if
                                 (< (rsi "SPY" {:window 10}) 30)
                                 [(asset
                                   "UPRO"
                                   "ProShares UltraPro S&P500")]
                                 [(group
                                   "Bear Market Sideways Protection"
                                   [(weight-equal
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
                                                     "ProShares UltraPro Short QQQ")])])])]
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
                                                       "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])])])])])])])])
        0.0458
        (group
         "New WAM & SLUNT Collection - 10/6/23 (Public Version)"
         [(weight-equal
           [(group
             "BSC / Drop Those Pops Combo - Huge Volatility"
             [(weight-equal
               [(if
                 (< (cumulative-return "TQQQ" {:window 6}) -10.5)
                 [(weight-equal
                   [(if
                     (> (cumulative-return "TQQQ" {:window 1}) 5.5)
                     [(weight-equal
                       [(group
                         "BSC Group"
                         [(weight-equal
                           [(filter
                             (moving-average-return {:window 10})
                             (select-top 2)
                             [(asset
                               "VIXY"
                               "ProShares VIX Short-Term Futures ETF")
                              (asset
                               "TMV"
                               "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                              (asset
                               "TMF"
                               "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                              (asset "QID" "ProShares UltraShort QQQ")
                              (asset
                               "UUP"
                               "Invesco DB US Dollar Index Bullish Fund")
                              (asset
                               "SPLV"
                               "Invesco S&P 500 Low Volatility ETF")
                              (asset
                               "XLP"
                               "Consumer Staples Select Sector SPDR Fund")])])])])]
                     [(weight-equal
                       [(group
                         "BSC - 10d Std Dev SPY"
                         [(weight-equal
                           [(if
                             (> (stdev-return "SPY" {:window 10}) 2.5)
                             [(weight-equal
                               [(group
                                 "TG 7 - b2"
                                 [(weight-equal
                                   [(filter
                                     (stdev-return {:window 5})
                                     (select-bottom 2)
                                     [(asset
                                       "TMV"
                                       "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                      (asset
                                       "TMF"
                                       "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                      (asset
                                       "SVXY"
                                       "ProShares Short VIX Short-Term Futures ETF")
                                      (asset
                                       "BTAL"
                                       "AGF U.S. Market Neutral Anti-Beta Fund")
                                      (asset
                                       "VIXM"
                                       "ProShares VIX Mid-Term Futures ETF")])])])])]
                             [(weight-equal
                               [(group
                                 "Wooden ARKK Machine Collection - Note: Delete 1 Year Backtest Group to run a 3yr backtest"
                                 [(weight-equal
                                   [(group
                                     "WAM Collection - 3 Year Backtest Version (without TARK or SARK)"
                                     [(weight-equal
                                       [(group
                                         "3YR BT Copy of WAM Collection - Updated 6/10/23"
                                         [(weight-specified
                                           0.2
                                           (group
                                            "Wooden ARKK Machine - 15d BND vs. 15d QQQ"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "BND"
                                                  {:window 15})
                                                 (rsi
                                                  "QQQ"
                                                  {:window 15}))
                                                [(weight-equal
                                                  [(filter
                                                    (max-drawdown
                                                     {:window 5})
                                                    (select-top 1)
                                                    [(asset
                                                      "TECL"
                                                      "Direxion Daily Technology Bull 3x Shares")
                                                     (asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TMF"
                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                     (asset
                                                      "YINN"
                                                      "Direxion Daily FTSE China Bull 3X Shares")
                                                     (asset
                                                      "EDC"
                                                      "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                                     (asset
                                                      "SOXX"
                                                      "iShares Semiconductor ETF")
                                                     (asset
                                                      "LABU"
                                                      "Direxion Daily S&P Biotech Bull 3X Shares")
                                                     (asset
                                                      "HIBL"
                                                      "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])]
                                                [(weight-equal
                                                  [(filter
                                                    (moving-average-return
                                                     {:window 4})
                                                    (select-bottom 2)
                                                    [(asset
                                                      "PSQ"
                                                      "ProShares Short QQQ")
                                                     (asset
                                                      "TMV"
                                                      "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                     (asset
                                                      "DRV"
                                                      "Direxion Daily Real Estate Bear 3X Shares")
                                                     (asset
                                                      "TYO"
                                                      "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                                     (asset
                                                      "LABD"
                                                      "Direxion Daily S&P Biotech Bear 3X Shares")
                                                     (asset
                                                      "YANG"
                                                      "Direxion Daily FTSE China Bear 3X Shares")])])])])])
                                           0.2
                                           (group
                                            "Wooden ARKK Machine - 10d AGG vs. 10d QQQ"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "AGG"
                                                  {:window 10})
                                                 (rsi
                                                  "QQQ"
                                                  {:window 10}))
                                                [(weight-equal
                                                  [(filter
                                                    (max-drawdown
                                                     {:window 5})
                                                    (select-top 1)
                                                    [(asset
                                                      "TECL"
                                                      "Direxion Daily Technology Bull 3x Shares")
                                                     (asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TMF"
                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                     (asset
                                                      "YINN"
                                                      "Direxion Daily FTSE China Bull 3X Shares")
                                                     (asset
                                                      "EDC"
                                                      "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                                     (asset
                                                      "SOXX"
                                                      "iShares Semiconductor ETF")
                                                     (asset
                                                      "LABU"
                                                      "Direxion Daily S&P Biotech Bull 3X Shares")
                                                     (asset
                                                      "HIBL"
                                                      "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])]
                                                [(weight-equal
                                                  [(filter
                                                    (moving-average-return
                                                     {:window 4})
                                                    (select-bottom 2)
                                                    [(asset
                                                      "PSQ"
                                                      "ProShares Short QQQ")
                                                     (asset
                                                      "TMV"
                                                      "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                     (asset
                                                      "DRV"
                                                      "Direxion Daily Real Estate Bear 3X Shares")
                                                     (asset
                                                      "TYO"
                                                      "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                                     (asset
                                                      "LABD"
                                                      "Direxion Daily S&P Biotech Bear 3X Shares")
                                                     (asset
                                                      "YANG"
                                                      "Direxion Daily FTSE China Bear 3X Shares")])])])])])
                                           0.2
                                           (group
                                            "Wooden ARKK Machine - 15d AGG vs. 15d QQQ"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "AGG"
                                                  {:window 15})
                                                 (rsi
                                                  "QQQ"
                                                  {:window 15}))
                                                [(weight-equal
                                                  [(filter
                                                    (max-drawdown
                                                     {:window 5})
                                                    (select-top 1)
                                                    [(asset
                                                      "TECL"
                                                      "Direxion Daily Technology Bull 3x Shares")
                                                     (asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TMF"
                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                     (asset
                                                      "YINN"
                                                      "Direxion Daily FTSE China Bull 3X Shares")
                                                     (asset
                                                      "EDC"
                                                      "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                                     (asset
                                                      "SOXX"
                                                      "iShares Semiconductor ETF")
                                                     (asset
                                                      "LABU"
                                                      "Direxion Daily S&P Biotech Bull 3X Shares")
                                                     (asset
                                                      "HIBL"
                                                      "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])]
                                                [(weight-equal
                                                  [(filter
                                                    (moving-average-return
                                                     {:window 4})
                                                    (select-bottom 2)
                                                    [(asset
                                                      "PSQ"
                                                      "ProShares Short QQQ")
                                                     (asset
                                                      "TMV"
                                                      "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                     (asset
                                                      "DRV"
                                                      "Direxion Daily Real Estate Bear 3X Shares")
                                                     (asset
                                                      "TYO"
                                                      "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                                     (asset
                                                      "LABD"
                                                      "Direxion Daily S&P Biotech Bear 3X Shares")
                                                     (asset
                                                      "YANG"
                                                      "Direxion Daily FTSE China Bear 3X Shares")])])])])])
                                           0.2
                                           (group
                                            "Wooden ARKK Machine - 10d SCHZ vs. 10d URTY"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "SCHZ"
                                                  {:window 10})
                                                 (rsi
                                                  "URTY"
                                                  {:window 10}))
                                                [(weight-equal
                                                  [(filter
                                                    (moving-average-return
                                                     {:window 4})
                                                    (select-bottom 1)
                                                    [(asset
                                                      "TECL"
                                                      "Direxion Daily Technology Bull 3x Shares")
                                                     (asset
                                                      "URTY"
                                                      "ProShares UltraPro Russell2000")
                                                     (asset
                                                      "TMF"
                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                     (asset
                                                      "YINN"
                                                      "Direxion Daily FTSE China Bull 3X Shares")
                                                     (asset
                                                      "EDC"
                                                      "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                                     (asset
                                                      "SOXX"
                                                      "iShares Semiconductor ETF")
                                                     (asset
                                                      "LABU"
                                                      "Direxion Daily S&P Biotech Bull 3X Shares")
                                                     (asset
                                                      "WEBL"
                                                      "Direxion Daily Dow Jones Internet Bull 3X Shares")
                                                     (asset
                                                      "HIBL"
                                                      "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])]
                                                [(weight-equal
                                                  [(filter
                                                    (moving-average-return
                                                     {:window 4})
                                                    (select-bottom 1)
                                                    [(asset
                                                      "PSQ"
                                                      "ProShares Short QQQ")
                                                     (asset
                                                      "TMV"
                                                      "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                     (asset
                                                      "DRV"
                                                      "Direxion Daily Real Estate Bear 3X Shares")
                                                     (asset
                                                      "LABD"
                                                      "Direxion Daily S&P Biotech Bear 3X Shares")
                                                     (asset
                                                      "SH"
                                                      "ProShares Short S&P500")])])])])])
                                           0.2
                                           (group
                                            "Wooden ARKK Machine - 10d TYD vs. 10d URTY"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "TYD"
                                                  {:window 10})
                                                 (rsi
                                                  "URTY"
                                                  {:window 10}))
                                                [(weight-equal
                                                  [(filter
                                                    (moving-average-return
                                                     {:window 4})
                                                    (select-bottom 1)
                                                    [(asset
                                                      "TECL"
                                                      "Direxion Daily Technology Bull 3x Shares")
                                                     (asset
                                                      "UPRO"
                                                      "ProShares UltraPro S&P500")
                                                     (asset
                                                      "TMF"
                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                     (asset
                                                      "YINN"
                                                      "Direxion Daily FTSE China Bull 3X Shares")
                                                     (asset
                                                      "EDC"
                                                      "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                                     (asset
                                                      "SOXX"
                                                      "iShares Semiconductor ETF")
                                                     (asset
                                                      "LABU"
                                                      "Direxion Daily S&P Biotech Bull 3X Shares")
                                                     (asset
                                                      "HIBL"
                                                      "Direxion Daily S&P 500 High Beta Bull 3X Shares")
                                                     (asset
                                                      "URTY"
                                                      "ProShares UltraPro Russell2000")
                                                     (asset
                                                      "WEBL"
                                                      "Direxion Daily Dow Jones Internet Bull 3X Shares")])])]
                                                [(weight-equal
                                                  [(filter
                                                    (moving-average-return
                                                     {:window 4})
                                                    (select-bottom 1)
                                                    [(asset
                                                      "PSQ"
                                                      "ProShares Short QQQ")
                                                     (asset
                                                      "TMV"
                                                      "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                     (asset
                                                      "DRV"
                                                      "Direxion Daily Real Estate Bear 3X Shares")
                                                     (asset
                                                      "LABD"
                                                      "Direxion Daily S&P Biotech Bear 3X Shares")
                                                     (asset
                                                      "SH"
                                                      "ProShares Short S&P500")])])])])]))])])])])])])])])])])])])]
                 [(weight-equal
                   [(group
                     "BSC - 10d Std Dev SPY"
                     [(weight-equal
                       [(if
                         (> (stdev-return "SPY" {:window 10}) 2.5)
                         [(weight-equal
                           [(group
                             "TG 7 - b2"
                             [(weight-equal
                               [(filter
                                 (stdev-return {:window 5})
                                 (select-bottom 2)
                                 [(asset
                                   "TMV"
                                   "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                  (asset
                                   "TMF"
                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                  (asset
                                   "SVXY"
                                   "ProShares Short VIX Short-Term Futures ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")
                                  (asset
                                   "VIXM"
                                   "ProShares VIX Mid-Term Futures ETF")])])])])]
                         [(weight-equal
                           [(group
                             "Wooden ARKK Machine Collection - Note: Delete 1 Year Backtest Group to run a 3yr backtest"
                             [(weight-equal
                               [(group
                                 "WAM Collection - 3 Year Backtest Version (without TARK or SARK)"
                                 [(weight-equal
                                   [(group
                                     "3YR BT Copy of WAM Collection - Updated 6/10/23"
                                     [(weight-specified
                                       0.2
                                       (group
                                        "Wooden ARKK Machine - 15d BND vs. 15d QQQ"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "BND" {:window 15})
                                             (rsi "QQQ" {:window 15}))
                                            [(weight-equal
                                              [(filter
                                                (max-drawdown
                                                 {:window 5})
                                                (select-top 1)
                                                [(asset
                                                  "TECL"
                                                  "Direxion Daily Technology Bull 3x Shares")
                                                 (asset
                                                  "UPRO"
                                                  "ProShares UltraPro S&P500")
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                 (asset
                                                  "YINN"
                                                  "Direxion Daily FTSE China Bull 3X Shares")
                                                 (asset
                                                  "EDC"
                                                  "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                                 (asset
                                                  "SOXX"
                                                  "iShares Semiconductor ETF")
                                                 (asset
                                                  "LABU"
                                                  "Direxion Daily S&P Biotech Bull 3X Shares")
                                                 (asset
                                                  "HIBL"
                                                  "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])]
                                            [(weight-equal
                                              [(filter
                                                (moving-average-return
                                                 {:window 4})
                                                (select-bottom 2)
                                                [(asset
                                                  "PSQ"
                                                  "ProShares Short QQQ")
                                                 (asset
                                                  "TMV"
                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                 (asset
                                                  "DRV"
                                                  "Direxion Daily Real Estate Bear 3X Shares")
                                                 (asset
                                                  "TYO"
                                                  "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                                 (asset
                                                  "LABD"
                                                  "Direxion Daily S&P Biotech Bear 3X Shares")
                                                 (asset
                                                  "YANG"
                                                  "Direxion Daily FTSE China Bear 3X Shares")])])])])])
                                       0.2
                                       (group
                                        "Wooden ARKK Machine - 10d AGG vs. 10d QQQ"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "AGG" {:window 10})
                                             (rsi "QQQ" {:window 10}))
                                            [(weight-equal
                                              [(filter
                                                (max-drawdown
                                                 {:window 5})
                                                (select-top 1)
                                                [(asset
                                                  "TECL"
                                                  "Direxion Daily Technology Bull 3x Shares")
                                                 (asset
                                                  "UPRO"
                                                  "ProShares UltraPro S&P500")
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                 (asset
                                                  "YINN"
                                                  "Direxion Daily FTSE China Bull 3X Shares")
                                                 (asset
                                                  "EDC"
                                                  "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                                 (asset
                                                  "SOXX"
                                                  "iShares Semiconductor ETF")
                                                 (asset
                                                  "LABU"
                                                  "Direxion Daily S&P Biotech Bull 3X Shares")
                                                 (asset
                                                  "HIBL"
                                                  "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])]
                                            [(weight-equal
                                              [(filter
                                                (moving-average-return
                                                 {:window 4})
                                                (select-bottom 2)
                                                [(asset
                                                  "PSQ"
                                                  "ProShares Short QQQ")
                                                 (asset
                                                  "TMV"
                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                 (asset
                                                  "DRV"
                                                  "Direxion Daily Real Estate Bear 3X Shares")
                                                 (asset
                                                  "TYO"
                                                  "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                                 (asset
                                                  "LABD"
                                                  "Direxion Daily S&P Biotech Bear 3X Shares")
                                                 (asset
                                                  "YANG"
                                                  "Direxion Daily FTSE China Bear 3X Shares")])])])])])
                                       0.2
                                       (group
                                        "Wooden ARKK Machine - 15d AGG vs. 15d QQQ"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "AGG" {:window 15})
                                             (rsi "QQQ" {:window 15}))
                                            [(weight-equal
                                              [(filter
                                                (max-drawdown
                                                 {:window 5})
                                                (select-top 1)
                                                [(asset
                                                  "TECL"
                                                  "Direxion Daily Technology Bull 3x Shares")
                                                 (asset
                                                  "UPRO"
                                                  "ProShares UltraPro S&P500")
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                 (asset
                                                  "YINN"
                                                  "Direxion Daily FTSE China Bull 3X Shares")
                                                 (asset
                                                  "EDC"
                                                  "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                                 (asset
                                                  "SOXX"
                                                  "iShares Semiconductor ETF")
                                                 (asset
                                                  "LABU"
                                                  "Direxion Daily S&P Biotech Bull 3X Shares")
                                                 (asset
                                                  "HIBL"
                                                  "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])]
                                            [(weight-equal
                                              [(filter
                                                (moving-average-return
                                                 {:window 4})
                                                (select-bottom 2)
                                                [(asset
                                                  "PSQ"
                                                  "ProShares Short QQQ")
                                                 (asset
                                                  "TMV"
                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                 (asset
                                                  "DRV"
                                                  "Direxion Daily Real Estate Bear 3X Shares")
                                                 (asset
                                                  "TYO"
                                                  "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                                 (asset
                                                  "LABD"
                                                  "Direxion Daily S&P Biotech Bear 3X Shares")
                                                 (asset
                                                  "YANG"
                                                  "Direxion Daily FTSE China Bear 3X Shares")])])])])])
                                       0.2
                                       (group
                                        "Wooden ARKK Machine - 10d SCHZ vs. 10d URTY"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "SCHZ" {:window 10})
                                             (rsi "URTY" {:window 10}))
                                            [(weight-equal
                                              [(filter
                                                (moving-average-return
                                                 {:window 4})
                                                (select-bottom 1)
                                                [(asset
                                                  "TECL"
                                                  "Direxion Daily Technology Bull 3x Shares")
                                                 (asset
                                                  "URTY"
                                                  "ProShares UltraPro Russell2000")
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                 (asset
                                                  "YINN"
                                                  "Direxion Daily FTSE China Bull 3X Shares")
                                                 (asset
                                                  "EDC"
                                                  "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                                 (asset
                                                  "SOXX"
                                                  "iShares Semiconductor ETF")
                                                 (asset
                                                  "LABU"
                                                  "Direxion Daily S&P Biotech Bull 3X Shares")
                                                 (asset
                                                  "WEBL"
                                                  "Direxion Daily Dow Jones Internet Bull 3X Shares")
                                                 (asset
                                                  "HIBL"
                                                  "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])]
                                            [(weight-equal
                                              [(filter
                                                (moving-average-return
                                                 {:window 4})
                                                (select-bottom 1)
                                                [(asset
                                                  "PSQ"
                                                  "ProShares Short QQQ")
                                                 (asset
                                                  "TMV"
                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                 (asset
                                                  "DRV"
                                                  "Direxion Daily Real Estate Bear 3X Shares")
                                                 (asset
                                                  "LABD"
                                                  "Direxion Daily S&P Biotech Bear 3X Shares")
                                                 (asset
                                                  "SH"
                                                  "ProShares Short S&P500")])])])])])
                                       0.2
                                       (group
                                        "Wooden ARKK Machine - 10d TYD vs. 10d URTY"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "TYD" {:window 10})
                                             (rsi "URTY" {:window 10}))
                                            [(weight-equal
                                              [(filter
                                                (moving-average-return
                                                 {:window 4})
                                                (select-bottom 1)
                                                [(asset
                                                  "TECL"
                                                  "Direxion Daily Technology Bull 3x Shares")
                                                 (asset
                                                  "UPRO"
                                                  "ProShares UltraPro S&P500")
                                                 (asset
                                                  "TMF"
                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                 (asset
                                                  "YINN"
                                                  "Direxion Daily FTSE China Bull 3X Shares")
                                                 (asset
                                                  "EDC"
                                                  "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                                 (asset
                                                  "SOXX"
                                                  "iShares Semiconductor ETF")
                                                 (asset
                                                  "LABU"
                                                  "Direxion Daily S&P Biotech Bull 3X Shares")
                                                 (asset
                                                  "HIBL"
                                                  "Direxion Daily S&P 500 High Beta Bull 3X Shares")
                                                 (asset
                                                  "URTY"
                                                  "ProShares UltraPro Russell2000")
                                                 (asset
                                                  "WEBL"
                                                  "Direxion Daily Dow Jones Internet Bull 3X Shares")])])]
                                            [(weight-equal
                                              [(filter
                                                (moving-average-return
                                                 {:window 4})
                                                (select-bottom 1)
                                                [(asset
                                                  "PSQ"
                                                  "ProShares Short QQQ")
                                                 (asset
                                                  "TMV"
                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                 (asset
                                                  "DRV"
                                                  "Direxion Daily Real Estate Bear 3X Shares")
                                                 (asset
                                                  "LABD"
                                                  "Direxion Daily S&P Biotech Bear 3X Shares")
                                                 (asset
                                                  "SH"
                                                  "ProShares Short S&P500")])])])])]))])])])])])])])])])])])])])])])
        0.032799999999999996
        (group
         "SOXL RSI Strategy"
         [(weight-equal
           [(if
             (>
              (current-price "SOXL")
              (moving-average-price "SOXL" {:window 200}))
             [(weight-equal
               [(if
                 (< (rsi "SOXL" {:window 10}) 49)
                 [(weight-equal
                   [(if
                     (< (cumulative-return "SOXL" {:window 1}) -2)
                     [(weight-equal
                       [(group
                         "SOXL Percentage Price Oscillator"
                         [(weight-equal
                           [(if
                             (>
                              (current-price "SOXL")
                              (moving-average-price
                               "SOXL"
                               {:window 200}))
                             [(weight-equal
                               [(if
                                 (<
                                  (percentage-price-oscillator
                                   "SOXL"
                                   {:short-window 12, :long-window 26})
                                  0)
                                 [(weight-equal
                                   [(if
                                     (<
                                      (percentage-price-oscillator-signal
                                       "SOXL"
                                       {:short-window 12,
                                        :long-window 26,
                                        :smooth-window 9})
                                      0)
                                     [(weight-equal
                                       [(if
                                         (>
                                          (percentage-price-oscillator-signal
                                           "SOXL"
                                           {:short-window 12,
                                            :long-window 26,
                                            :smooth-window 9})
                                          (percentage-price-oscillator
                                           "SOXL"
                                           {:short-window 12,
                                            :long-window 26}))
                                         [(asset
                                           "SOXL"
                                           "Direxion Daily Semiconductor Bull 3x Shares")]
                                         [(asset
                                           "SHV"
                                           "iShares Short Treasury Bond ETF")])])]
                                     [(asset
                                       "SHV"
                                       "iShares Short Treasury Bond ETF")])])]
                                 [(asset
                                   "SHV"
                                   "iShares Short Treasury Bond ETF")])])]
                             [(weight-equal
                               [(asset
                                 "SHV"
                                 "iShares Short Treasury Bond ETF")])])])])])]
                     [(weight-equal
                       [(if
                         (> (cumulative-return "SOXL" {:window 1}) 8.5)
                         [(weight-equal
                           [(if
                             (< (rsi "SOXL" {:window 10}) 30)
                             [(weight-equal
                               [(asset
                                 "SOXL"
                                 "Direxion Daily Semiconductor Bull 3x Shares")])]
                             [(weight-equal
                               [(asset
                                 "SOXS"
                                 "Direxion Daily Semiconductor Bear 3x Shares")])])])]
                         [(weight-equal
                           [(asset
                             "SOXL"
                             "Direxion Daily Semiconductor Bull 3x Shares")])])])])])]
                 [(weight-equal
                   [(if
                     (> (rsi "SOXL" {:window 10}) 80)
                     [(weight-equal
                       [(asset
                         "UVXY"
                         "ProShares Ultra VIX Short-Term Futures ETF")])]
                     [(group
                       "SOXL Percentage Price Oscillator"
                       [(weight-equal
                         [(if
                           (>
                            (current-price "SOXL")
                            (moving-average-price
                             "SOXL"
                             {:window 200}))
                           [(weight-equal
                             [(if
                               (<
                                (percentage-price-oscillator
                                 "SOXL"
                                 {:short-window 12, :long-window 26})
                                0)
                               [(weight-equal
                                 [(if
                                   (<
                                    (percentage-price-oscillator-signal
                                     "SOXL"
                                     {:short-window 12,
                                      :long-window 26,
                                      :smooth-window 9})
                                    0)
                                   [(weight-equal
                                     [(if
                                       (>
                                        (percentage-price-oscillator-signal
                                         "SOXL"
                                         {:short-window 12,
                                          :long-window 26,
                                          :smooth-window 9})
                                        (percentage-price-oscillator
                                         "SOXL"
                                         {:short-window 12,
                                          :long-window 26}))
                                       [(asset
                                         "SOXL"
                                         "Direxion Daily Semiconductor Bull 3x Shares")]
                                       [(asset
                                         "SHV"
                                         "iShares Short Treasury Bond ETF")])])]
                                   [(asset
                                     "SHV"
                                     "iShares Short Treasury Bond ETF")])])]
                               [(asset
                                 "SHV"
                                 "iShares Short Treasury Bond ETF")])])]
                           [(weight-equal
                             [(asset
                               "SHV"
                               "iShares Short Treasury Bond ETF")])])])])])])])])]
             [(weight-equal
               [(if
                 (< (rsi "SOXL" {:window 10}) 30)
                 [(weight-equal
                   [(if
                     (< (cumulative-return "SOXL" {:window 1}) -6)
                     [(weight-equal
                       [(asset
                         "UVXY"
                         "ProShares Ultra VIX Short-Term Futures ETF")
                        (asset
                         "SOXL"
                         "Direxion Daily Semiconductor Bull 3x Shares")])]
                     [(asset
                       "SOXL"
                       "Direxion Daily Semiconductor Bull 3x Shares")])])]
                 [(weight-equal
                   [(group
                     "SOXL Percentage Price Oscillator"
                     [(weight-equal
                       [(if
                         (>
                          (current-price "SOXL")
                          (moving-average-price "SOXL" {:window 200}))
                         [(weight-equal
                           [(if
                             (<
                              (percentage-price-oscillator
                               "SOXL"
                               {:short-window 12, :long-window 26})
                              0)
                             [(weight-equal
                               [(if
                                 (<
                                  (percentage-price-oscillator-signal
                                   "SOXL"
                                   {:short-window 12,
                                    :long-window 26,
                                    :smooth-window 9})
                                  0)
                                 [(weight-equal
                                   [(if
                                     (>
                                      (percentage-price-oscillator-signal
                                       "SOXL"
                                       {:short-window 12,
                                        :long-window 26,
                                        :smooth-window 9})
                                      (percentage-price-oscillator
                                       "SOXL"
                                       {:short-window 12,
                                        :long-window 26}))
                                     [(asset
                                       "SOXL"
                                       "Direxion Daily Semiconductor Bull 3x Shares")]
                                     [(asset
                                       "SHV"
                                       "iShares Short Treasury Bond ETF")])])]
                                 [(asset
                                   "SHV"
                                   "iShares Short Treasury Bond ETF")])])]
                             [(asset
                               "SHV"
                               "iShares Short Treasury Bond ETF")])])]
                         [(weight-equal
                           [(asset
                             "SHV"
                             "iShares Short Treasury Bond ETF")])])])])])])])])])])
        0.0888
        (group
         "Oil (08/14/2023)"
         [(weight-equal
           [(if
             (>
              (current-price "DBO")
              (moving-average-price "DBO" {:window 150}))
             [(weight-equal
               [(if
                 (>
                  (exponential-moving-average-price "UCO" {:window 15})
                  (exponential-moving-average-price
                   "UCO"
                   {:window 30}))
                 [(weight-equal [(asset "DBO" "Invesco DB Oil Fund")])]
                 [(asset "SHV" "iShares Short Treasury Bond ETF")])])]
             [(asset "SHV" "iShares Short Treasury Bond ETF")])
            (group
             "There Will Be Blood"
             [(weight-equal
               [(if
                 (>=
                  (exponential-moving-average-price "DBO" {:window 50})
                  (moving-average-price "DBO" {:window 200}))
                 [(weight-equal
                   [(if
                     (>
                      (moving-average-price "UCO" {:window 9})
                      (moving-average-price "UCO" {:window 21}))
                     [(weight-equal
                       [(if
                         (< (cumulative-return "UCO" {:window 30}) -10)
                         [(weight-equal
                           [(filter
                             (moving-average-return {:window 21})
                             (select-top 2)
                             [(asset "XOM" "Exxon Mobil Corporation")
                              (asset
                               "XLE"
                               "Energy Select Sector SPDR Fund")
                              (asset "ENPH" "Enphase Energy, Inc.")
                              (asset "VLO" "Valero Energy Corporation")
                              (asset "CVE" "Cenovus Energy Inc.")
                              (asset "CVX" "Chevron Corporation")
                              (asset "COP" "ConocoPhillips")
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
                             [(asset "UCO" nil)
                              (asset
                               "OILK"
                               "ProShares K-1 Free Crude Oil Strategy ETF")])])])
                        (filter
                         (moving-average-return {:window 21})
                         (select-top 2)
                         [(asset "XOM" "Exxon Mobil Corporation")
                          (asset
                           "XLE"
                           "Energy Select Sector SPDR Fund")
                          (asset "ENPH" "Enphase Energy, Inc.")
                          (asset "VLO" "Valero Energy Corporation")
                          (asset "CVE" "Cenovus Energy Inc.")
                          (asset "CVX" "Chevron Corporation")
                          (asset "COP" "ConocoPhillips")
                          (asset
                           "MPC"
                           "Marathon Petroleum Corporation")
                          (asset "DINO" "HF Sinclair Corporation")])])]
                     [(weight-equal
                       [(filter
                         (moving-average-return {:window 100})
                         (select-top 2)
                         [(asset "XOM" "Exxon Mobil Corporation")
                          (asset "ENPH" "Enphase Energy, Inc.")
                          (asset "VLO" "Valero Energy Corporation")
                          (asset "CVE" "Cenovus Energy Inc.")
                          (asset "CVX" "Chevron Corporation")
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
                      (moving-average-price "OILK" {:window 50})
                      (moving-average-price "OILK" {:window 400}))
                     [(weight-equal
                       [(if
                         (<
                          (moving-average-return "UCO" {:window 5})
                          0)
                         [(weight-equal
                           [(filter
                             (rsi {:window 7})
                             (select-top 1)
                             [(asset "SCO" nil)
                              (asset
                               "IEF"
                               "iShares 7-10 Year Treasury Bond ETF")])])]
                         [(weight-equal
                           [(filter
                             (rsi {:window 10})
                             (select-top 1)
                             [(asset "UCO" nil)
                              (asset
                               "OILK"
                               "ProShares K-1 Free Crude Oil Strategy ETF")])])])
                        (filter
                         (moving-average-return {:window 100})
                         (select-top 2)
                         [(asset "XOM" "Exxon Mobil Corporation")
                          (asset "ENPH" "Enphase Energy, Inc.")
                          (asset "VLO" "Valero Energy Corporation")
                          (asset "CVE" "Cenovus Energy Inc.")
                          (asset "CVX" "Chevron Corporation")
                          (asset "COP" "ConocoPhillips")
                          (asset
                           "MPC"
                           "Marathon Petroleum Corporation")
                          (asset "DINO" "HF Sinclair Corporation")])])]
                     [(weight-equal
                       [(filter
                         (moving-average-return {:window 100})
                         (select-top 2)
                         [(asset "XOM" "Exxon Mobil Corporation")
                          (asset "ENPH" "Enphase Energy, Inc.")
                          (asset "VLO" "Valero Energy Corporation")
                          (asset "CVE" "Cenovus Energy Inc.")
                          (asset "CVX" "Chevron Corporation")
                          (asset "COP" "ConocoPhillips")
                          (asset
                           "MPC"
                           "Marathon Petroleum Corporation")
                          (asset
                           "DINO"
                           "HF Sinclair Corporation")])])])])])])])
            (group
             "V2 | 3x Big Oil | by DereckNielsen"
             [(weight-equal
               [(weight-specified
                 0.25
                 (if
                  (>
                   (current-price "UCO")
                   (moving-average-price "UCO" {:window 350}))
                  [(weight-equal
                    [(if
                      (<
                       (current-price "UCO")
                       (moving-average-price "UCO" {:window 40}))
                      [(weight-equal
                        [(filter
                          (rsi {:window 20})
                          (select-top 1)
                          [(asset "SCO" nil)
                           (asset
                            "ERY"
                            "Direxion Daily Energy Bear 2X Shares")
                           (asset
                            "BSV"
                            "Vanguard Short-Term Bond ETF")])])]
                      [(asset "UCO" nil)])])]
                  [(weight-equal
                    [(if
                      (< (rsi "UCO" {:window 10}) 26)
                      [(asset "UCO" nil)]
                      [(weight-equal
                        [(if
                          (<
                           (current-price "UCO")
                           (moving-average-price "UCO" {:window 40}))
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-bottom 1)
                              [(asset "SCO" nil) (asset "UCO" nil)])])]
                          [(asset "UCO" nil)])])])])])
                 0.75
                 (group
                  "Oil"
                  [(weight-equal
                    [(if
                      (>
                       (current-price "OILK")
                       (moving-average-price "OILK" {:window 252}))
                      [(weight-equal
                        [(if
                          (>
                           (moving-average-price "OILK" {:window 20})
                           (moving-average-price "OILK" {:window 80}))
                          [(asset
                            "OILK"
                            "ProShares K-1 Free Crude Oil Strategy ETF")]
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-top 1)
                              [(asset "GLD" "SPDR Gold Shares")
                               (asset
                                "UUP"
                                "Invesco DB US Dollar Index Bullish Fund")])])])])]
                      [(weight-equal
                        [(if
                          (<
                           (current-price "OILK")
                           (moving-average-price "OILK" {:window 20}))
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-top 1)
                              [(asset "GLD" "SPDR Gold Shares")
                               (asset
                                "SCO"
                                "ProShares UltraShort Bloomberg Crude Oil")])])]
                          [(weight-equal
                            [(filter
                              (rsi {:window 10})
                              (select-top 1)
                              [(asset "GLD" "SPDR Gold Shares")
                               (asset
                                "UCO"
                                "ProShares Ultra Bloomberg Crude Oil")])])])])])])]))])])])])
        0.07780000000000001
        (group
         "V1a BWC Market Assassin"
         [(weight-equal
           [(if
             (<
              (current-price "SPY")
              (moving-average-price "SPY" {:window 85}))
             [(weight-specified
               0.25
               (group
                "V1a WAM Collection - 3 Year Backtest Version (without TARK or SARK)"
                [(weight-equal
                  [(group
                    "3YR BT Copy of WAM Collection - Updated 6/10/23"
                    [(weight-equal
                      [(group
                        "Wooden ARKK Machine - 10d AGG vs. 10d QQQ"
                        [(weight-equal
                          [(if
                            (>
                             (rsi "AGG" {:window 10})
                             (rsi "QQQ" {:window 10}))
                            [(weight-equal
                              [(filter
                                (moving-average-return {:window 4})
                                (select-bottom 1)
                                [(asset
                                  "TECL"
                                  "Direxion Daily Technology Bull 3x Shares")
                                 (asset
                                  "UPRO"
                                  "ProShares UltraPro S&P500")
                                 (asset
                                  "TMF"
                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                 (asset
                                  "YINN"
                                  "Direxion Daily FTSE China Bull 3X Shares")
                                 (asset
                                  "EDC"
                                  "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                 (asset
                                  "SOXX"
                                  "iShares Semiconductor ETF")
                                 (asset
                                  "LABU"
                                  "Direxion Daily S&P Biotech Bull 3X Shares")
                                 (asset
                                  "HIBL"
                                  "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])]
                            [(weight-equal
                              [(filter
                                (moving-average-return {:window 4})
                                (select-bottom 2)
                                [(asset "PSQ" "ProShares Short QQQ")
                                 (asset
                                  "TMV"
                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                 (asset
                                  "DRV"
                                  "Direxion Daily Real Estate Bear 3X Shares")
                                 (asset
                                  "TYO"
                                  "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                 (asset
                                  "JDST"
                                  "Direxion Daily Junior Gold Miners Index Bear 2X Shares")
                                 (asset
                                  "LABD"
                                  "Direxion Daily S&P Biotech Bear 3X Shares")
                                 (asset
                                  "YANG"
                                  "Direxion Daily FTSE China Bear 3X Shares")])])])])])
                       (group
                        "Wooden ARKK Machine - 10d SCHZ vs. 10d URTY"
                        [(weight-equal
                          [(if
                            (>
                             (rsi "SCHZ" {:window 10})
                             (rsi "URTY" {:window 10}))
                            [(weight-equal
                              [(filter
                                (moving-average-return {:window 4})
                                (select-bottom 1)
                                [(asset
                                  "TECL"
                                  "Direxion Daily Technology Bull 3x Shares")
                                 (asset
                                  "URTY"
                                  "ProShares UltraPro Russell2000")
                                 (asset
                                  "TMF"
                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                 (asset
                                  "YINN"
                                  "Direxion Daily FTSE China Bull 3X Shares")
                                 (asset
                                  "EDC"
                                  "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                 (asset
                                  "SOXX"
                                  "iShares Semiconductor ETF")
                                 (asset
                                  "LABU"
                                  "Direxion Daily S&P Biotech Bull 3X Shares")
                                 (asset
                                  "WEBL"
                                  "Direxion Daily Dow Jones Internet Bull 3X Shares")
                                 (asset
                                  "HIBL"
                                  "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])]
                            [(weight-equal
                              [(filter
                                (moving-average-return {:window 4})
                                (select-bottom 1)
                                [(asset "PSQ" "ProShares Short QQQ")
                                 (asset
                                  "TMV"
                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                 (asset
                                  "DRV"
                                  "Direxion Daily Real Estate Bear 3X Shares")
                                 (asset
                                  "JDST"
                                  "Direxion Daily Junior Gold Miners Index Bear 2X Shares")
                                 (asset
                                  "LABD"
                                  "Direxion Daily S&P Biotech Bear 3X Shares")
                                 (asset
                                  "SH"
                                  "ProShares Short S&P500")])])])])])
                       (group
                        "Wooden ARKK Machine - 10d TYD vs. 10d URTY"
                        [(weight-equal
                          [(if
                            (>
                             (rsi "TYD" {:window 10})
                             (rsi "URTY" {:window 10}))
                            [(weight-equal
                              [(filter
                                (moving-average-return {:window 4})
                                (select-bottom 1)
                                [(asset
                                  "TECL"
                                  "Direxion Daily Technology Bull 3x Shares")
                                 (asset
                                  "UPRO"
                                  "ProShares UltraPro S&P500")
                                 (asset
                                  "TMF"
                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                 (asset
                                  "YINN"
                                  "Direxion Daily FTSE China Bull 3X Shares")
                                 (asset
                                  "EDC"
                                  "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                 (asset
                                  "SOXX"
                                  "iShares Semiconductor ETF")
                                 (asset
                                  "LABU"
                                  "Direxion Daily S&P Biotech Bull 3X Shares")
                                 (asset
                                  "HIBL"
                                  "Direxion Daily S&P 500 High Beta Bull 3X Shares")
                                 (asset
                                  "URTY"
                                  "ProShares UltraPro Russell2000")
                                 (asset
                                  "WEBL"
                                  "Direxion Daily Dow Jones Internet Bull 3X Shares")])])]
                            [(weight-equal
                              [(filter
                                (moving-average-return {:window 4})
                                (select-bottom 1)
                                [(asset "PSQ" "ProShares Short QQQ")
                                 (asset
                                  "TMV"
                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                 (asset
                                  "DRV"
                                  "Direxion Daily Real Estate Bear 3X Shares")
                                 (asset
                                  "JDST"
                                  "Direxion Daily Junior Gold Miners Index Bear 2X Shares")
                                 (asset
                                  "LABD"
                                  "Direxion Daily S&P Biotech Bear 3X Shares")
                                 (asset
                                  "SH"
                                  "ProShares Short S&P500")])])])])])])])])])
               0.75
               (group
                "V1a TQQQ or not | + Dash of SQQQ - Deez - Replace UVXY w/ SOXS"
                [(weight-equal
                  [(group
                    "V1a TQQQ or not | BlackSwan MeanRev BondSignal - Replace UVXY w/ SOXS"
                    [(weight-equal
                      [(if
                        (> (rsi "TQQQ" {:window 10}) 79)
                        [(asset
                          "VIXY"
                          "ProShares VIX Short-Term Futures ETF")]
                        [(weight-equal
                          [(group
                            "Huge volatility"
                            [(weight-equal
                              [(if
                                (<
                                 (cumulative-return "TQQQ" {:window 6})
                                 -13)
                                [(weight-equal
                                  [(if
                                    (>
                                     (cumulative-return
                                      "TQQQ"
                                      {:window 1})
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
                                             (rsi "TQQQ" {:window 10})
                                             32)
                                            [(asset
                                              "SOXL"
                                              "Direxion Daily Semiconductor Bull 3x Shares")]
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (max-drawdown
                                                  "TMF"
                                                  {:window 10})
                                                 7)
                                                [(asset
                                                  "SOXL"
                                                  "Direxion Daily Semiconductor Bull 3x Shares")]
                                                [(weight-specified
                                                  0.6
                                                  (asset
                                                   "BIL"
                                                   "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                  0.4
                                                  (asset
                                                   "SQQQ"
                                                   "ProShares UltraPro Short QQQ"))])])])])])])])])]
                                [(weight-equal
                                  [(group
                                    "Normal market"
                                    [(weight-equal
                                      [(if
                                        (>
                                         (max-drawdown
                                          "QQQ"
                                          {:window 10})
                                         6)
                                        [(weight-specified
                                          0.6
                                          (asset
                                           "BIL"
                                           "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                          0.4
                                          (asset
                                           "SQQQ"
                                           "ProShares UltraPro Short QQQ"))]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (max-drawdown
                                              "TMF"
                                              {:window 10})
                                             7)
                                            [(weight-specified
                                              0.6
                                              (asset
                                               "BIL"
                                               "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                              0.4
                                              (asset
                                               "SQQQ"
                                               "ProShares UltraPro Short QQQ"))]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (current-price "QQQ")
                                                 (moving-average-price
                                                  "QQQ"
                                                  {:window 25}))
                                                [(weight-equal
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "SPY"
                                                      {:window 60})
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
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")]
                                                          [(weight-specified
                                                            0.6
                                                            (asset
                                                             "BIL"
                                                             "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                            0.4
                                                            (asset
                                                             "SQQQ"
                                                             "ProShares UltraPro Short QQQ"))])])])]
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
                                                                "TQQQ"
                                                                "ProShares UltraPro QQQ")]
                                                              [(weight-specified
                                                                0.6
                                                                (asset
                                                                 "BIL"
                                                                 "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                0.4
                                                                (asset
                                                                 "SQQQ"
                                                                 "ProShares UltraPro Short QQQ"))])])]
                                                          [(weight-specified
                                                            0.6
                                                            (asset
                                                             "BIL"
                                                             "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                            0.4
                                                            (asset
                                                             "SQQQ"
                                                             "ProShares UltraPro Short QQQ"))])])])])])])])])])])])])])])])])])])])])])]))]
             [(weight-equal
               [(group
                 "V1a WAM Collection - 3 Year Backtest Version (without TARK or SARK)"
                 [(weight-equal
                   [(group
                     "3YR BT Copy of WAM Collection - Updated 6/10/23"
                     [(weight-equal
                       [(group
                         "Wooden ARKK Machine - 10d AGG vs. 10d QQQ"
                         [(weight-equal
                           [(if
                             (>
                              (rsi "AGG" {:window 10})
                              (rsi "QQQ" {:window 10}))
                             [(weight-equal
                               [(filter
                                 (moving-average-return {:window 4})
                                 (select-bottom 1)
                                 [(asset
                                   "TECL"
                                   "Direxion Daily Technology Bull 3x Shares")
                                  (asset
                                   "UPRO"
                                   "ProShares UltraPro S&P500")
                                  (asset
                                   "TMF"
                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                  (asset
                                   "YINN"
                                   "Direxion Daily FTSE China Bull 3X Shares")
                                  (asset
                                   "EDC"
                                   "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                  (asset
                                   "SOXX"
                                   "iShares Semiconductor ETF")
                                  (asset
                                   "LABU"
                                   "Direxion Daily S&P Biotech Bull 3X Shares")
                                  (asset
                                   "HIBL"
                                   "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])]
                             [(weight-equal
                               [(filter
                                 (moving-average-return {:window 4})
                                 (select-bottom 2)
                                 [(asset "PSQ" "ProShares Short QQQ")
                                  (asset
                                   "TMV"
                                   "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                  (asset
                                   "DRV"
                                   "Direxion Daily Real Estate Bear 3X Shares")
                                  (asset
                                   "TYO"
                                   "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                  (asset
                                   "JDST"
                                   "Direxion Daily Junior Gold Miners Index Bear 2X Shares")
                                  (asset
                                   "LABD"
                                   "Direxion Daily S&P Biotech Bear 3X Shares")
                                  (asset
                                   "YANG"
                                   "Direxion Daily FTSE China Bear 3X Shares")])])])])])
                        (group
                         "Wooden ARKK Machine - 10d SCHZ vs. 10d URTY"
                         [(weight-equal
                           [(if
                             (>
                              (rsi "SCHZ" {:window 10})
                              (rsi "URTY" {:window 10}))
                             [(weight-equal
                               [(filter
                                 (moving-average-return {:window 4})
                                 (select-bottom 1)
                                 [(asset
                                   "TECL"
                                   "Direxion Daily Technology Bull 3x Shares")
                                  (asset
                                   "URTY"
                                   "ProShares UltraPro Russell2000")
                                  (asset
                                   "TMF"
                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                  (asset
                                   "YINN"
                                   "Direxion Daily FTSE China Bull 3X Shares")
                                  (asset
                                   "EDC"
                                   "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                  (asset
                                   "SOXX"
                                   "iShares Semiconductor ETF")
                                  (asset
                                   "LABU"
                                   "Direxion Daily S&P Biotech Bull 3X Shares")
                                  (asset
                                   "WEBL"
                                   "Direxion Daily Dow Jones Internet Bull 3X Shares")
                                  (asset
                                   "HIBL"
                                   "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])]
                             [(weight-equal
                               [(filter
                                 (moving-average-return {:window 4})
                                 (select-bottom 1)
                                 [(asset "PSQ" "ProShares Short QQQ")
                                  (asset
                                   "TMV"
                                   "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                  (asset
                                   "DRV"
                                   "Direxion Daily Real Estate Bear 3X Shares")
                                  (asset
                                   "JDST"
                                   "Direxion Daily Junior Gold Miners Index Bear 2X Shares")
                                  (asset
                                   "LABD"
                                   "Direxion Daily S&P Biotech Bear 3X Shares")
                                  (asset
                                   "SH"
                                   "ProShares Short S&P500")])])])])])
                        (group
                         "Wooden ARKK Machine - 10d TYD vs. 10d URTY"
                         [(weight-equal
                           [(if
                             (>
                              (rsi "TYD" {:window 10})
                              (rsi "URTY" {:window 10}))
                             [(weight-equal
                               [(filter
                                 (moving-average-return {:window 4})
                                 (select-bottom 1)
                                 [(asset
                                   "TECL"
                                   "Direxion Daily Technology Bull 3x Shares")
                                  (asset
                                   "UPRO"
                                   "ProShares UltraPro S&P500")
                                  (asset
                                   "TMF"
                                   "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                  (asset
                                   "YINN"
                                   "Direxion Daily FTSE China Bull 3X Shares")
                                  (asset
                                   "EDC"
                                   "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                                  (asset
                                   "SOXX"
                                   "iShares Semiconductor ETF")
                                  (asset
                                   "LABU"
                                   "Direxion Daily S&P Biotech Bull 3X Shares")
                                  (asset
                                   "HIBL"
                                   "Direxion Daily S&P 500 High Beta Bull 3X Shares")
                                  (asset
                                   "URTY"
                                   "ProShares UltraPro Russell2000")
                                  (asset
                                   "WEBL"
                                   "Direxion Daily Dow Jones Internet Bull 3X Shares")])])]
                             [(weight-equal
                               [(filter
                                 (moving-average-return {:window 4})
                                 (select-bottom 1)
                                 [(asset "PSQ" "ProShares Short QQQ")
                                  (asset
                                   "TMV"
                                   "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                  (asset
                                   "DRV"
                                   "Direxion Daily Real Estate Bear 3X Shares")
                                  (asset
                                   "JDST"
                                   "Direxion Daily Junior Gold Miners Index Bear 2X Shares")
                                  (asset
                                   "LABD"
                                   "Direxion Daily S&P Biotech Bear 3X Shares")
                                  (asset
                                   "SH"
                                   "ProShares Short S&P500")])])])])])])])])])
                (group
                 "V1a TQQQ or not | + Dash of SQQQ - Deez - Replace UVXY w/ SOXS"
                 [(weight-equal
                   [(group
                     "V1a TQQQ or not | BlackSwan MeanRev BondSignal - Replace UVXY w/ SOXS"
                     [(weight-equal
                       [(if
                         (> (rsi "TQQQ" {:window 10}) 79)
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
                                   {:window 6})
                                  -13)
                                 [(weight-equal
                                   [(if
                                     (>
                                      (cumulative-return
                                       "TQQQ"
                                       {:window 1})
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
                                              (rsi "TQQQ" {:window 10})
                                              32)
                                             [(asset
                                               "SOXL"
                                               "Direxion Daily Semiconductor Bull 3x Shares")]
                                             [(weight-equal
                                               [(if
                                                 (<
                                                  (max-drawdown
                                                   "TMF"
                                                   {:window 10})
                                                  7)
                                                 [(asset
                                                   "SOXL"
                                                   "Direxion Daily Semiconductor Bull 3x Shares")]
                                                 [(weight-specified
                                                   0.6
                                                   (asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                   0.4
                                                   (asset
                                                    "SQQQ"
                                                    "ProShares UltraPro Short QQQ"))])])])])])])])])]
                                 [(weight-equal
                                   [(group
                                     "Normal market"
                                     [(weight-equal
                                       [(if
                                         (>
                                          (max-drawdown
                                           "QQQ"
                                           {:window 10})
                                          6)
                                         [(weight-specified
                                           0.6
                                           (asset
                                            "BIL"
                                            "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                           0.4
                                           (asset
                                            "SQQQ"
                                            "ProShares UltraPro Short QQQ"))]
                                         [(weight-equal
                                           [(if
                                             (>
                                              (max-drawdown
                                               "TMF"
                                               {:window 10})
                                              7)
                                             [(weight-specified
                                               0.6
                                               (asset
                                                "BIL"
                                                "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                               0.4
                                               (asset
                                                "SQQQ"
                                                "ProShares UltraPro Short QQQ"))]
                                             [(weight-equal
                                               [(if
                                                 (>
                                                  (current-price "QQQ")
                                                  (moving-average-price
                                                   "QQQ"
                                                   {:window 25}))
                                                 [(weight-equal
                                                   [(asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")])]
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (rsi
                                                       "SPY"
                                                       {:window 60})
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
                                                             "TQQQ"
                                                             "ProShares UltraPro QQQ")]
                                                           [(weight-specified
                                                             0.6
                                                             (asset
                                                              "BIL"
                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                             0.4
                                                             (asset
                                                              "SQQQ"
                                                              "ProShares UltraPro Short QQQ"))])])])]
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
                                                                 "TQQQ"
                                                                 "ProShares UltraPro QQQ")]
                                                               [(weight-specified
                                                                 0.6
                                                                 (asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                 0.4
                                                                 (asset
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ"))])])]
                                                           [(weight-specified
                                                             0.6
                                                             (asset
                                                              "BIL"
                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                             0.4
                                                             (asset
                                                              "SQQQ"
                                                              "ProShares UltraPro Short QQQ"))])])])])])])])])])])])])])])])])])])])])])])])])])])
        0.06
        (group
         "V2 TINA"
         [(weight-equal
           [(if
             (>
              (current-price "QQQ")
              (moving-average-price "QQQ" {:window 20}))
             [(weight-equal
               [(if
                 (> (cumulative-return "QQQ" {:window 10}) 5.5)
                 [(asset "PSQ" "ProShares Short QQQ")]
                 [(weight-equal
                   [(if
                     (< (cumulative-return "TQQQ" {:window 62}) -33)
                     [(asset "TQQQ" "ProShares UltraPro QQQ")]
                     [(weight-equal
                       [(if
                         (> (rsi "QQQ" {:window 60}) 50)
                         [(weight-equal
                           [(filter
                             (rsi {:window 20})
                             (select-top 1)
                             [(asset
                               "BND"
                               "Vanguard Total Bond Market ETF")
                              (asset
                               "XLP"
                               "Consumer Staples Select Sector SPDR Fund")])])]
                         [(weight-equal
                           [(filter
                             (rsi {:window 20})
                             (select-top 1)
                             [(asset
                               "TLT"
                               "iShares 20+ Year Treasury Bond ETF")
                              (asset
                               "XLP"
                               "Consumer Staples Select Sector SPDR Fund")])])])])])])])])]
             [(weight-equal
               [(if
                 (< (rsi "QQQ" {:window 10}) 30)
                 [(asset
                   "TECL"
                   "Direxion Daily Technology Bull 3x Shares")]
                 [(weight-equal
                   [(if
                     (< (cumulative-return "TQQQ" {:window 62}) -33)
                     [(asset "TQQQ" "ProShares UltraPro QQQ")]
                     [(weight-equal
                       [(if
                         (> (rsi "QQQ" {:window 60}) 50)
                         [(weight-equal
                           [(filter
                             (rsi {:window 20})
                             (select-top 1)
                             [(asset
                               "BND"
                               "Vanguard Total Bond Market ETF")
                              (asset
                               "XLP"
                               "Consumer Staples Select Sector SPDR Fund")])])]
                         [(weight-equal
                           [(filter
                             (rsi {:window 10})
                             (select-top 1)
                             [(asset
                               "TLT"
                               "iShares 20+ Year Treasury Bond ETF")
                              (asset
                               "PSQ"
                               "ProShares Short QQQ")])])])])])])])])])])])
        0.1536
        (group
         "Let The Data Speak"
         [(weight-equal
           [(weight-equal
             [(group
               "WAM + Colonel Sanders [RSI 20d SPY TFLO]"
               [(weight-equal
                 [(if
                   (>
                    (rsi "SPY" {:window 20})
                    (rsi "TFLO" {:window 20}))
                   [(group
                     "Colonel Sanders 21 Spices ?"
                     [(weight-specified
                       0.4
                       (group
                        "V1.4 [RSI 4d TLH UPRO] | ? Colonel Sanders 21 Spices | slowloss1 performance replica | HTX"
                        [(weight-equal
                          [(if
                            (>
                             (rsi "TLH" {:window 4})
                             (rsi "UPRO" {:window 4}))
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "BND" {:window 15})
                                 (rsi "TQQQ" {:window 15}))
                                [(asset
                                  "SQQQ"
                                  "ProShares UltraPro Short QQQ")]
                                [(asset
                                  "TQQQ"
                                  "ProShares UltraPro QQQ")])])]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "SPHB" {:window 3})
                                 (stdev-return "SPHB" {:window 9}))
                                [(asset
                                  "HIBS"
                                  "Direxion Daily S&P 500 High Beta Bear 3X Shares")]
                                [(asset
                                  "HIBL"
                                  "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])])])])
                       0.3
                       (group
                        "V1.4 [CR 6d TLT 5d QQQ] | ? Colonel Sanders 21 Spices | slowloss1 performance replica | HTX"
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "TLT" {:window 6})
                             (cumulative-return "QQQ" {:window 5}))
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "BND" {:window 15})
                                 (rsi "TQQQ" {:window 15}))
                                [(asset
                                  "SQQQ"
                                  "ProShares UltraPro Short QQQ")]
                                [(asset
                                  "TQQQ"
                                  "ProShares UltraPro QQQ")])])]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "SPHB" {:window 3})
                                 (stdev-return "SPHB" {:window 9}))
                                [(asset
                                  "HIBS"
                                  "Direxion Daily S&P 500 High Beta Bear 3X Shares")]
                                [(asset
                                  "HIBL"
                                  "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])])])])
                       0.3
                       (group
                        "V1.4 [CR 6d TLH FNGS] | ? Colonel Sanders 21 Spices | slowloss1 performance replica | HTX"
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "TLH" {:window 6})
                             (cumulative-return "FNGS" {:window 6}))
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "BND" {:window 15})
                                 (rsi "TQQQ" {:window 15}))
                                [(asset
                                  "SQQQ"
                                  "ProShares UltraPro Short QQQ")]
                                [(asset
                                  "TQQQ"
                                  "ProShares UltraPro QQQ")])])]
                            [(weight-equal
                              [(if
                                (>
                                 (cumulative-return "SPHB" {:window 3})
                                 (stdev-return "SPHB" {:window 9}))
                                [(asset
                                  "HIBS"
                                  "Direxion Daily S&P 500 High Beta Bear 3X Shares")]
                                [(asset
                                  "HIBL"
                                  "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])])])]))])]
                   [(group
                     "Wooden ARKK Machine 2.2b no IEF no TYO [RSI 10d SCHZ URTY]"
                     [(weight-equal
                       [(if
                         (>
                          (rsi "SCHZ" {:window 10})
                          (rsi "URTY" {:window 10}))
                         [(weight-equal
                           [(filter
                             (moving-average-return {:window 4})
                             (select-bottom 1)
                             [(asset
                               "TECL"
                               "Direxion Daily Technology Bull 3x Shares")
                              (asset "TARK" "AXS 2X Innovation ETF")
                              (asset
                               "URTY"
                               "ProShares UltraPro Russell2000")
                              (asset
                               "TMF"
                               "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                              (asset
                               "YINN"
                               "Direxion Daily FTSE China Bull 3X Shares")
                              (asset
                               "EDC"
                               "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                              (asset
                               "SOXX"
                               "iShares Semiconductor ETF")
                              (asset
                               "LABU"
                               "Direxion Daily S&P Biotech Bull 3X Shares")
                              (asset
                               "HIBL"
                               "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])]
                         [(weight-equal
                           [(filter
                             (moving-average-return {:window 4})
                             (select-bottom 1)
                             [(asset "PSQ" "ProShares Short QQQ")
                              (asset
                               "SARK"
                               "AXS Short Innovation Daily ETF")
                              (asset
                               "TMV"
                               "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                              (asset
                               "DRV"
                               "Direxion Daily Real Estate Bear 3X Shares")
                              (asset
                               "JDST"
                               "Direxion Daily Junior Gold Miners Index Bear 2X Shares")
                              (asset
                               "LABD"
                               "Direxion Daily S&P Biotech Bear 3X Shares")
                              (asset
                               "SH"
                               "ProShares Short S&P500")])])])])])])])])
              (group
               "CONS v1.0.0 RR | ARK Baller + Plaid Inner Baller [? Experimental strategy - limited backtest]"
               [(weight-equal
                 [(if
                   (<
                    (moving-average-return "ARKK" {:window 60})
                    (moving-average-return "QID" {:window 85}))
                   [(weight-equal
                     [(if
                       (< (rsi "ARKK" {:window 7}) 77)
                       [(weight-equal
                         [(if
                           (>=
                            (cumulative-return "ARKK" {:window 1})
                            2)
                           [(weight-equal
                             [(group
                               "ARK Fund Surfing"
                               [(weight-equal
                                 [(filter
                                   (rsi {:window 7})
                                   (select-bottom 1)
                                   [(asset
                                     "TARK"
                                     "AXS 2X Innovation ETF")
                                    (asset
                                     "STIP"
                                     "iShares 0-5 Year TIPS Bond ETF")])
                                  (filter
                                   (rsi {:window 7})
                                   (select-bottom 1)
                                   [(asset "ARKK" "ARK Innovation ETF")
                                    (asset
                                     "ARKW"
                                     "ARK Next Generation Internet ETF")
                                    (asset
                                     "ARKG"
                                     "ARK Genomic Revolution ETF")
                                    (asset
                                     "ARKQ"
                                     "ARK Autonomous Technology & Robotics ETF")
                                    (asset
                                     "ARKW"
                                     "ARK Next Generation Internet ETF")
                                    (asset
                                     "TARK"
                                     "AXS 2X Innovation ETF")
                                    (asset
                                     "ARKX"
                                     "ARK Space Exploration & Innovation ETF")])])])])]
                           [(weight-equal
                             [(if
                               (>=
                                (cumulative-return "ARKK" {:window 7})
                                (stdev-return "ARKK" {:window 5}))
                               [(weight-equal
                                 [(if
                                   (>=
                                    (stdev-return "ARKK" {:window 3})
                                    (stdev-return "ARKK" {:window 5}))
                                   [(asset
                                     "SARK"
                                     "AXS Short Innovation Daily ETF")]
                                   [(weight-equal
                                     [(if
                                       (>
                                        (moving-average-return
                                         "SARK"
                                         {:window 2})
                                        (stdev-return
                                         "SARK"
                                         {:window 4}))
                                       [(group
                                         "See You Tmrw"
                                         [(weight-equal
                                           [(filter
                                             (max-drawdown {:window 2})
                                             (select-top 1)
                                             [(asset
                                               "VIXY"
                                               "ProShares VIX Short-Term Futures ETF")
                                              (asset
                                               "BTAL"
                                               "AGFiQ US Market Neutral Anti-Beta Fund")
                                              (asset
                                               "SPHB"
                                               "Invesco S&P 500 High Beta ETF")])
                                            (filter
                                             (max-drawdown {:window 4})
                                             (select-top 1)
                                             [(asset
                                               "TMV"
                                               "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                              (asset
                                               "PSQ"
                                               "ProShares Short QQQ")
                                              (asset
                                               "UGL"
                                               "ProShares Ultra Gold")])])])]
                                       [(asset
                                         "SARK"
                                         "AXS Short Innovation Daily ETF")])])])])]
                               [(weight-equal
                                 [(if
                                   (>=
                                    (moving-average-return
                                     "TARK"
                                     {:window 3})
                                    (stdev-return "ARKK" {:window 5}))
                                   [(weight-equal
                                     [(if
                                       (>
                                        (cumulative-return
                                         "SARK"
                                         {:window 1})
                                        4)
                                       [(weight-equal
                                         [(filter
                                           (cumulative-return
                                            {:window 21})
                                           (select-bottom 1)
                                           [(asset
                                             "ARKK"
                                             "ARK Innovation ETF")
                                            (asset
                                             "ARKW"
                                             "ARK Next Generation Internet ETF")
                                            (asset
                                             "ARKG"
                                             "ARK Genomic Revolution ETF")
                                            (asset
                                             "ARKQ"
                                             "ARK Autonomous Technology & Robotics ETF")
                                            (asset
                                             "ARKW"
                                             "ARK Next Generation Internet ETF")
                                            (asset
                                             "TARK"
                                             "AXS 2X Innovation ETF")
                                            (asset
                                             "ARKX"
                                             "ARK Space Exploration & Innovation ETF")])])]
                                       [(asset
                                         "TARK"
                                         "AXS 2X Innovation ETF")])])]
                                   [(group
                                     "ARK Baller (short side)"
                                     [(weight-equal
                                       [(if
                                         (<
                                          (rsi "BIL" {:window 5})
                                          (rsi "IEF" {:window 4}))
                                         [(weight-equal
                                           [(if
                                             (<
                                              (rsi "TARK" {:window 7})
                                              75)
                                             [(weight-equal
                                               [(asset
                                                 "TARK"
                                                 "AXS 2X Innovation ETF")])]
                                             [(weight-equal
                                               [(filter
                                                 (rsi {:window 10})
                                                 (select-bottom 1)
                                                 [(asset
                                                   "SARK"
                                                   "AXS Short Innovation Daily ETF")
                                                  (asset
                                                   "USDU"
                                                   "WisdomTree Bloomberg US Dollar Bullish Fund")])])])])]
                                         [(weight-equal
                                           [(if
                                             (<
                                              (rsi "SARK" {:window 7})
                                              75)
                                             [(weight-equal
                                               [(group
                                                 "Plaid Inner Baller (short bias)"
                                                 [(weight-equal
                                                   [(if
                                                     (>
                                                      (moving-average-return
                                                       "IEF"
                                                       {:window 20})
                                                      (moving-average-return
                                                       "TLH"
                                                       {:window 20}))
                                                     [(weight-equal
                                                       [(filter
                                                         (rsi
                                                          {:window 10})
                                                         (select-bottom
                                                          1)
                                                         [(asset
                                                           "SARK"
                                                           "AXS Short Innovation Daily ETF")
                                                          (asset
                                                           "USDU"
                                                           "WisdomTree Bloomberg US Dollar Bullish Fund")])])]
                                                     [(weight-equal
                                                       [(filter
                                                         (rsi
                                                          {:window 10})
                                                         (select-top 1)
                                                         [(asset
                                                           "SARK"
                                                           "AXS Short Innovation Daily ETF")
                                                          (asset
                                                           "UBT"
                                                           "ProShares Ultra 20+ Year Treasury")])])])])])])]
                                             [(asset
                                               "TARK"
                                               "AXS 2X Innovation ETF")])])])])])])])])])])])]
                       [(weight-equal
                         [(filter
                           (rsi {:window 10})
                           (select-bottom 1)
                           [(asset
                             "UVXY"
                             "ProShares Ultra VIX Short-Term Futures ETF")
                            (asset
                             "SARK"
                             "AXS Short Innovation Daily ETF")])])])])]
                   [(weight-equal
                     [(if
                       (>
                        (moving-average-return "ARKK" {:window 2})
                        (stdev-return "ARKK" {:window 4}))
                       [(weight-equal
                         [(group
                           "See You Tmrw"
                           [(weight-equal
                             [(filter
                               (max-drawdown {:window 2})
                               (select-top 1)
                               [(asset
                                 "VIXY"
                                 "ProShares VIX Short-Term Futures ETF")
                                (asset
                                 "BTAL"
                                 "AGFiQ US Market Neutral Anti-Beta Fund")
                                (asset
                                 "SPHB"
                                 "Invesco S&P 500 High Beta ETF")])
                              (filter
                               (max-drawdown {:window 4})
                               (select-top 1)
                               [(asset
                                 "TMV"
                                 "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                (asset "PSQ" "ProShares Short QQQ")
                                (asset
                                 "UGL"
                                 "ProShares Ultra Gold")])])])])]
                       [(weight-equal
                         [(group
                           "ARK Baller (long side)"
                           [(weight-equal
                             [(if
                               (<
                                (rsi "BIL" {:window 5})
                                (rsi "IEF" {:window 4}))
                               [(weight-equal
                                 [(if
                                   (< (rsi "TARK" {:window 7}) 75)
                                   [(weight-equal
                                     [(asset
                                       "TARK"
                                       "AXS 2X Innovation ETF")])]
                                   [(weight-equal
                                     [(filter
                                       (rsi {:window 10})
                                       (select-bottom 1)
                                       [(asset
                                         "SARK"
                                         "AXS Short Innovation Daily ETF")
                                        (asset
                                         "USDU"
                                         "WisdomTree Bloomberg US Dollar Bullish Fund")])])])])]
                               [(weight-equal
                                 [(if
                                   (< (rsi "SARK" {:window 7}) 75)
                                   [(weight-specified
                                     0
                                     (group
                                      "Plaid Inner Baller (long / short)"
                                      [(weight-equal
                                        [(if
                                          (<
                                           (rsi "IEI" {:window 10})
                                           (rsi "IEF" {:window 9}))
                                          [(weight-equal
                                            [(group
                                              "3yr 10yr cumulative returns check"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (moving-average-return
                                                    "IEI"
                                                    {:window 20})
                                                   (moving-average-return
                                                    "TLH"
                                                    {:window 20}))
                                                  [(weight-equal
                                                    [(filter
                                                      (rsi
                                                       {:window 10})
                                                      (select-bottom 1)
                                                      [(asset
                                                        "SARK"
                                                        "AXS Short Innovation Daily ETF")
                                                       (asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")])])]
                                                  [(weight-equal
                                                    [(filter
                                                      (rsi
                                                       {:window 10})
                                                      (select-bottom 1)
                                                      [(asset
                                                        "BTAL"
                                                        "AGF U.S. Market Neutral Anti-Beta Fund")
                                                       (asset
                                                        "UGL"
                                                        "ProShares Ultra Gold")])])])])])])]
                                          [(weight-equal
                                            [(group
                                              "3yr 10yr cumulative returns check"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (moving-average-return
                                                    "IEI"
                                                    {:window 20})
                                                   (moving-average-return
                                                    "IEF"
                                                    {:window 20}))
                                                  [(weight-equal
                                                    [(filter
                                                      (rsi
                                                       {:window 10})
                                                      (select-bottom 1)
                                                      [(asset
                                                        "TARK"
                                                        "AXS 2X Innovation ETF")
                                                       (asset
                                                        "USDU"
                                                        "WisdomTree Bloomberg US Dollar Bullish Fund")])])]
                                                  [(weight-equal
                                                    [(filter
                                                      (rsi
                                                       {:window 10})
                                                      (select-top 1)
                                                      [(asset
                                                        "TARK"
                                                        "AXS 2X Innovation ETF")
                                                       (asset
                                                        "TARK"
                                                        "AXS 2X Innovation ETF")])])])])])])])])])
                                     1
                                     (group
                                      "Plaid Inner Baller 'The Voting Booth' (long / short)  "
                                      [(weight-equal
                                        [(if
                                          (>
                                           (moving-average-return
                                            "IEF"
                                            {:window 20})
                                           (moving-average-return
                                            "TLH"
                                            {:window 20}))
                                          [(weight-equal
                                            [(group
                                              "3yr 10yr cumulative returns check"
                                              [(weight-equal
                                                [(if
                                                  (<
                                                   (rsi
                                                    "IEI"
                                                    {:window 10})
                                                   (rsi
                                                    "IEF"
                                                    {:window 9}))
                                                  [(weight-equal
                                                    [(filter
                                                      (rsi
                                                       {:window 10})
                                                      (select-bottom 1)
                                                      [(asset
                                                        "SARK"
                                                        "AXS Short Innovation Daily ETF")
                                                       (asset
                                                        "UUP"
                                                        "Invesco DB US Dollar Index Bullish Fund")])])]
                                                  [(weight-equal
                                                    [(filter
                                                      (rsi
                                                       {:window 10})
                                                      (select-bottom 1)
                                                      [(asset
                                                        "BTAL"
                                                        "AGF U.S. Market Neutral Anti-Beta Fund")
                                                       (asset
                                                        "UGL"
                                                        "ProShares Ultra Gold")])])])])])])]
                                          [(weight-equal
                                            [(group
                                              "3yr 10yr cumulative returns check"
                                              [(weight-equal
                                                [(if
                                                  (<
                                                   (rsi
                                                    "IEI"
                                                    {:window 10})
                                                   (rsi
                                                    "IEF"
                                                    {:window 9}))
                                                  [(weight-equal
                                                    [(filter
                                                      (rsi
                                                       {:window 10})
                                                      (select-bottom 1)
                                                      [(asset
                                                        "TARK"
                                                        "AXS 2X Innovation ETF")
                                                       (asset
                                                        "USDU"
                                                        "WisdomTree Bloomberg US Dollar Bullish Fund")])])]
                                                  [(weight-equal
                                                    [(filter
                                                      (rsi
                                                       {:window 10})
                                                      (select-top 1)
                                                      [(asset
                                                        "TARK"
                                                        "AXS 2X Innovation ETF")
                                                       (asset
                                                        "TARK"
                                                        "AXS 2X Innovation ETF")])])])])])])])])]))]
                                   [(asset
                                     "TARK"
                                     "AXS 2X Innovation ETF")])])])])])])])])])])])
              (group
               "Mean Reversion"
               [(weight-equal
                 [(if
                   (> (cumulative-return "FXI" {:window 5}) 10)
                   [(weight-equal
                     [(if
                       (< (cumulative-return "FXI" {:window 1}) -2)
                       [(asset
                         "YINN"
                         "Direxion Daily FTSE China Bull 3X Shares")]
                       [(asset
                         "YANG"
                         "Direxion Daily FTSE China Bear 3X Shares")])])]
                   [(group
                     "Bearish Mean Reversion"
                     [(weight-equal
                       [(if
                         (< (cumulative-return "FXI" {:window 5}) -10)
                         [(weight-equal
                           [(if
                             (>
                              (cumulative-return "FXI" {:window 1})
                              2)
                             [(asset
                               "YANG"
                               "Direxion Daily FTSE China Bear 3X Shares")]
                             [(asset
                               "YINN"
                               "Direxion Daily FTSE China Bull 3X Shares")])])]
                         [(asset
                           "SHY"
                           "iShares 1-3 Year Treasury Bond ETF")])])])])])])])])])
        0.1388
        (group
         "Bitcoin"
         [(weight-equal
           [(if
             (< (rsi "TQQQ" {:window 10}) 31)
             [(asset
               "TECL"
               "Direxion Daily Technology Bull 3x Shares")]
             [(weight-equal
               [(if
                 (> (rsi "QQQ" {:window 10}) 80)
                 [(asset
                   "TMF"
                   "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                 [(weight-equal
                   [(if
                     (> (rsi "SPY" {:window 10}) 80)
                     [(asset
                       "TMF"
                       "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                     [(weight-equal
                       [(if
                         (>
                          (rsi "IEF" {:window 10})
                          (rsi "PSQ" {:window 20}))
                         [(weight-equal
                           [(if
                             (>
                              (exponential-moving-average-price
                               "GBTC"
                               {:window 8})
                              (moving-average-price
                               "GBTC"
                               {:window 22}))
                             [(asset "GBTC" "Grayscale Bitcoin Trust")]
                             [(weight-equal
                               [(if
                                 (< (rsi "GBTC" {:window 10}) 27)
                                 [(asset
                                   "GBTC"
                                   "Grayscale Bitcoin Trust")]
                                 [(asset
                                   "SHV"
                                   "iShares Short Treasury Bond ETF")])])])])]
                         [(weight-equal
                           [(if
                             (< (rsi "GBTC" {:window 10}) 27)
                             [(asset "GBTC" "Grayscale Bitcoin Trust")]
                             [(weight-equal
                               [(filter
                                 (rsi {:window 10})
                                 (select-top 1)
                                 [(asset
                                   "BSV"
                                   "Vanguard Short-Term Bond ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")])
                                (filter
                                 (moving-average-return {:window 10})
                                 (select-top 1)
                                 [(asset
                                   "BSV"
                                   "Vanguard Short-Term Bond ETF")
                                  (asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")])])])])])])])])])])])])])
        0.358
        (group
         "DereckN Hedge System"
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
                          (moving-average-price "TMV" {:window 135}))
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
                (> (rsi "QQQ" {:window 10}) 80)
                [(asset "VIXY" "ProShares VIX Short-Term Futures ETF")]
                [(weight-equal
                  [(if
                    (> (rsi "SPY" {:window 10}) 80)
                    [(asset
                      "VIXY"
                      "ProShares VIX Short-Term Futures ETF")]
                    [(weight-equal
                      [(if
                        (< (rsi "TMF" {:window 10}) 32)
                        [(asset
                          "TMF"
                          "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                        [(weight-equal
                          [(if
                            (<
                             (rsi "BIL" {:window 30})
                             (rsi "TLT" {:window 20}))
                            [(weight-equal
                              [(if
                                (<
                                 (exponential-moving-average-price
                                  "TMF"
                                  {:window 8})
                                 (moving-average-price
                                  "TMF"
                                  {:window 10}))
                                [(weight-equal
                                  [(if
                                    (> (rsi "TMF" {:window 10}) 72)
                                    [(asset
                                      "SHV"
                                      "iShares Short Treasury Bond ETF")]
                                    [(weight-equal
                                      [(asset
                                        "TMF"
                                        "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])]
                                [(weight-equal
                                  [(if
                                    (< (rsi "TQQQ" {:window 10}) 31)
                                    [(asset
                                      "TECL"
                                      "Direxion Daily Technology Bull 3x Shares")]
                                    [(weight-equal
                                      [(asset
                                        "SHV"
                                        "iShares Short Treasury Bond ETF")])])])])])]
                            [(weight-equal
                              [(if
                                (< (rsi "TQQQ" {:window 10}) 31)
                                [(asset
                                  "TECL"
                                  "Direxion Daily Technology Bull 3x Shares")]
                                [(weight-equal
                                  [(asset
                                    "SHV"
                                    "iShares Short Treasury Bond ETF")])])])])])])])])])]))])
            (group
             "SVXY FTLT"
             [(weight-equal
               [(if
                 (> (rsi "QQQ" {:window 10}) 80)
                 [(asset
                   "VIXY"
                   "ProShares VIX Short-Term Futures ETF")]
                 [(weight-equal
                   [(if
                     (> (rsi "SPY" {:window 10}) 80)
                     [(asset
                       "VIXY"
                       "ProShares VIX Short-Term Futures ETF")]
                     [(weight-equal
                       [(if
                         (< (rsi "QQQ" {:window 10}) 30)
                         [(asset
                           "XLK"
                           "Technology Select Sector SPDR Fund")]
                         [(weight-equal
                           [(if
                             (>
                              (current-price "SVXY")
                              (moving-average-price
                               "SVXY"
                               {:window 24}))
                             [(weight-equal
                               [(filter
                                 (moving-average-return {:window 20})
                                 (select-top 1)
                                 [(asset
                                   "SVXY"
                                   "ProShares Short VIX Short-Term Futures ETF")
                                  (asset
                                   "VTI"
                                   "Vanguard Total Stock Market ETF")])])]
                             [(weight-equal
                               [(asset
                                 "BTAL"
                                 "AGF U.S. Market Neutral Anti-Beta Fund")])])])])])])])])])])
            (group
             "TINA"
             [(weight-equal
               [(if
                 (>
                  (current-price "QQQ")
                  (moving-average-price "QQQ" {:window 20}))
                 [(weight-equal
                   [(if
                     (> (cumulative-return "QQQ" {:window 10}) 5.5)
                     [(asset "PSQ" "ProShares Short QQQ")]
                     [(weight-equal
                       [(if
                         (<
                          (cumulative-return "TQQQ" {:window 62})
                          -33)
                         [(asset "TQQQ" "ProShares UltraPro QQQ")]
                         [(weight-equal
                           [(asset
                             "SHV"
                             "iShares Short Treasury Bond ETF")])])])])])]
                 [(weight-equal
                   [(if
                     (< (rsi "QQQ" {:window 10}) 30)
                     [(asset
                       "TECL"
                       "Direxion Daily Technology Bull 3x Shares")]
                     [(weight-equal
                       [(if
                         (<
                          (cumulative-return "TQQQ" {:window 62})
                          -33)
                         [(asset "TQQQ" "ProShares UltraPro QQQ")]
                         [(weight-equal
                           [(filter
                             (rsi {:window 20})
                             (select-top 1)
                             [(asset "PSQ" "ProShares Short QQQ")
                              (asset
                               "BSV"
                               "Vanguard Short-Term Bond ETF")
                              (asset
                               "TLT"
                               "iShares 20+ Year Treasury Bond ETF")])])])])])])])])])
            (group
             "Shorting SPY"
             [(weight-equal
               [(group
                 "20d BND vs 60d SH Logic To Go Short"
                 [(weight-equal
                   [(if
                     (>
                      (rsi "BND" {:window 20})
                      (rsi "SH" {:window 60}))
                     [(weight-equal
                       [(if
                         (>
                          (current-price "SPY")
                          (moving-average-price "SPY" {:window 200}))
                         [(weight-equal
                           [(asset
                             "SHV"
                             "iShares Short Treasury Bond ETF")])]
                         [(weight-equal
                           [(if
                             (< (rsi "QQQ" {:window 10}) 30)
                             [(asset
                               "XLK"
                               "Technology Select Sector SPDR Fund")]
                             [(asset
                               "SHV"
                               "iShares Short Treasury Bond ETF")])])])])]
                     [(weight-equal
                       [(if
                         (< (rsi "QQQ" {:window 10}) 30)
                         [(asset
                           "XLK"
                           "Technology Select Sector SPDR Fund")]
                         [(weight-equal
                           [(if
                             (<
                              (exponential-moving-average-price
                               "SPY"
                               {:window 10})
                              (moving-average-price
                               "SPY"
                               {:window 10}))
                             [(asset "SH" "ProShares Short S&P500")]
                             [(asset
                               "SHV"
                               "iShares Short Treasury Bond ETF")])])])])])])])])])
            (group
             "SVXY FTLT | V2"
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
                         (< (rsi "QQQ" {:window 10}) 30)
                         [(asset
                           "XLK"
                           "Technology Select Sector SPDR Fund")]
                         [(weight-equal
                           [(if
                             (>
                              (current-price "SVXY")
                              (moving-average-price
                               "SVXY"
                               {:window 21}))
                             [(weight-specified
                               0.7
                               (filter
                                (moving-average-return {:window 20})
                                (select-top 1)
                                [(asset
                                  "SVXY"
                                  "ProShares Short VIX Short-Term Futures ETF")
                                 (asset
                                  "VTI"
                                  "Vanguard Total Stock Market ETF")])
                               0.3
                               (weight-equal
                                [(asset
                                  "VIXM"
                                  "ProShares VIX Mid-Term Futures ETF")]))]
                             [(weight-equal
                               [(filter
                                 (moving-average-return {:window 20})
                                 (select-top 1)
                                 [(asset
                                   "BTAL"
                                   "AGF U.S. Market Neutral Anti-Beta Fund")])])])])])])])])])])])])]))])])]))
