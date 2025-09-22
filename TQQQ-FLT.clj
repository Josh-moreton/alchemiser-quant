(defsymphony
 "TQQQ FTLT | Full Package | Diceroll Group | Shorter Backtest v2 [FTL]"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                 (cumulative-return "TQQQ" {:window 5})
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
                                                          {:window 10})
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
                                                          {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "QQQ" {:window 10})
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
                                            "NRGU"
                                            "MicroSectors U.S. Big Oil Index 3X Leveraged ETN")])])]
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
                                            "NRGD"
                                            "MicroSectors U.S. Big Oil Index -3X Inverse Leveraged ETN")])])])])]
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                 (cumulative-return "TQQQ" {:window 5})
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
                                                          {:window 10})
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
                                                          {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "QQQ" {:window 10})
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
                                            "NRGU"
                                            "MicroSectors U.S. Big Oil Index 3X Leveraged ETN")])])]
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
                                            "NRGD"
                                            "MicroSectors U.S. Big Oil Index -3X Inverse Leveraged ETN")])])])])]
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "TLT" {:window 10})
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
                                 (cumulative-return "TQQQ" {:window 5})
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
                                                          {:window 10})
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
                                                          {:window 10})
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
                                                          {:window 10})
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
                                               (rsi "QQQ" {:window 10})
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
                                            "NRGU"
                                            "MicroSectors U.S. Big Oil Index 3X Leveraged ETN")])])]
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
                                            "NRGD"
                                            "MicroSectors U.S. Big Oil Index -3X Inverse Leveraged ETN")])])])])]
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
                                                  "ProShares UltraPro Short QQQ")])])])])])])])])])])])])])])])])])])])])])])])]))
