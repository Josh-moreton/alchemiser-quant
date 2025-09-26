(defsymphony
 "V1a What Have I Done - K-1 Free"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "V1a What Have I Done - K-1 Free"
    [(weight-equal
      [(filter
        (moving-average-return {:window 10})
        (select-top 1)
        [(group
          "Rally Rider + V1a WMDYN - K-1 Free"
          [(weight-equal
            [(if
              (>
               (exponential-moving-average-price "BITO" {:window 100})
               (moving-average-price "BITO" {:window 300}))
              [(weight-equal
                [(if
                  (>
                   (exponential-moving-average-price
                    "BITO"
                    {:window 20})
                   (moving-average-price "BITO" {:window 50}))
                  [(weight-equal
                    [(group
                      "HODL BTC"
                      [(weight-equal
                        [(filter
                          (moving-average-return {:window 3})
                          (select-top 1)
                          [(asset "COIN" nil)
                           (asset "MARA" nil)
                           (asset "MSTR" nil)
                           (asset
                            "BITQ"
                            "Bitwise Crypto Industry Innovators ETF")
                           (asset
                            "BITS"
                            "Global X Blockchain & Bitcoin Strategy ETF")
                           (asset
                            "BTF"
                            "Valkyrie Bitcoin and Ether Strategy ETF")
                           (asset "BITF" "Bitfarms Ltd.")])])])])]
                  [(group
                    "V1a What More Do You Need? - K-1 Free"
                    [(weight-equal
                      [(if
                        (> (rsi "QQQ" {:window 10}) 80)
                        [(asset
                          "VXX"
                          "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                        [(weight-equal
                          [(if
                            (> (rsi "SPY" {:window 10}) 80)
                            [(asset
                              "VXX"
                              "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                            [(weight-equal
                              [(if
                                (< (rsi "TQQQ" {:window 10}) 31)
                                [(asset "TECL" nil)]
                                [(weight-equal
                                  [(if
                                    (>
                                     (rsi "IEF" {:window 10})
                                     (rsi "PSQ" {:window 20}))
                                    [(weight-equal
                                      [(asset "BULZ" nil)])]
                                    [(weight-equal
                                      [(if
                                        (>
                                         (current-price "SPY")
                                         (moving-average-price
                                          "SPY"
                                          {:window 200}))
                                        [(weight-equal
                                          [(filter
                                            (rsi {:window 20})
                                            (select-top 1)
                                            [(asset
                                              "GUSH"
                                              "Direxion Daily S&P Oil & Gas Exp. & Prod. Bull 2X Shares")
                                             (asset
                                              "ERX"
                                              "Direxion Daily Energy Bull 2x Shares")
                                             (asset
                                              "OILK"
                                              "ProShares K-1 Free Crude Oil Strategy ETF")
                                             (asset
                                              "NRGU"
                                              "MicroSectors U.S. Big Oil Index 3X Leveraged ETN")])])]
                                        [(weight-equal
                                          [(asset "SQQQ" nil)
                                           (asset
                                            "TECS"
                                            nil)])])])])])])])])])])])])])])]
              [(group
                "V1a What More Do You Need? - K-1 Free"
                [(weight-equal
                  [(if
                    (> (rsi "QQQ" {:window 10}) 80)
                    [(asset
                      "VXX"
                      "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                    [(weight-equal
                      [(if
                        (> (rsi "SPY" {:window 10}) 80)
                        [(asset
                          "VXX"
                          "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
                        [(weight-equal
                          [(if
                            (< (rsi "TQQQ" {:window 10}) 31)
                            [(asset "TECL" nil)]
                            [(weight-equal
                              [(if
                                (>
                                 (rsi "IEF" {:window 10})
                                 (rsi "PSQ" {:window 20}))
                                [(weight-equal [(asset "BULZ" nil)])]
                                [(weight-equal
                                  [(if
                                    (>
                                     (current-price "SPY")
                                     (moving-average-price
                                      "SPY"
                                      {:window 200}))
                                    [(weight-equal
                                      [(filter
                                        (rsi {:window 20})
                                        (select-top 1)
                                        [(asset
                                          "GUSH"
                                          "Direxion Daily S&P Oil & Gas Exp. & Prod. Bull 2X Shares")
                                         (asset
                                          "ERX"
                                          "Direxion Daily Energy Bull 2x Shares")
                                         (asset
                                          "OILK"
                                          "ProShares K-1 Free Crude Oil Strategy ETF")
                                         (asset
                                          "NRGU"
                                          "MicroSectors U.S. Big Oil Index 3X Leveraged ETN")])])]
                                    [(weight-equal
                                      [(asset "SQQQ" nil)
                                       (asset
                                        "TECS"
                                        nil)])])])])])])])])])])])])])])])
         (group
          "Rally Rider + V1a WAM FTLT - K-1 Free"
          [(weight-equal
            [(if
              (>
               (exponential-moving-average-price "BITO" {:window 100})
               (moving-average-price "BITO" {:window 300}))
              [(weight-equal
                [(if
                  (>
                   (exponential-moving-average-price
                    "BITO"
                    {:window 20})
                   (moving-average-price "BITO" {:window 50}))
                  [(weight-equal
                    [(group
                      "HODL BTC"
                      [(weight-equal
                        [(filter
                          (moving-average-return {:window 3})
                          (select-top 1)
                          [(asset "COIN" nil)
                           (asset "CONL" nil)
                           (asset "RIOT" nil)
                           (asset "MARA" nil)
                           (asset "MSTR" nil)
                           (asset
                            "BITQ"
                            "Bitwise Crypto Industry Innovators ETF")
                           (asset
                            "BITS"
                            "Global X Blockchain & Bitcoin Strategy ETF")
                           (asset "BITF" "Bitfarms Ltd.")])])])])]
                  [(group
                    "V1a WAM FTLT (TMF Check) - K-1 Free"
                    [(weight-equal
                      [(group
                        "WAM FTLT (long backtest)"
                        [(weight-equal
                          [(if
                            (<
                             (moving-average-return
                              "SHY"
                              {:window 575})
                             0)
                            [(weight-equal
                              [(if
                                (> (rsi "TMF" {:window 14}) 60)
                                [(weight-equal
                                  [(if
                                    (<
                                     (rsi "IEF" {:window 11})
                                     (rsi "IWM" {:window 16}))
                                    [(weight-equal
                                      [(filter
                                        (moving-average-return
                                         {:window 4})
                                        (select-top 1)
                                        [(asset
                                          "TECL"
                                          "Direxion Daily Technology Bull 3x Shares")
                                         (asset
                                          "TQQQ"
                                          "ProShares UltraPro QQQ")
                                         (asset
                                          "DRN"
                                          "Direxion Daily Real Estate Bull 3x Shares")
                                         (asset
                                          "SOXL"
                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                         (asset
                                          "URTY"
                                          "ProShares UltraPro Russell2000")
                                         (asset
                                          "TMF"
                                          "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                         (group
                                          "LAB Check Bull"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (moving-average-return
                                                "XBI"
                                                {:window 600})
                                               0)
                                              [(asset
                                                "LABU"
                                                "Direxion Daily S&P Biotech Bull 3X Shares")]
                                              [(asset
                                                "SPXL"
                                                "Direxion Daily S&P 500 Bull 3x Shares")])])])])])]
                                    [(weight-equal
                                      [(filter
                                        (moving-average-return
                                         {:window 4})
                                        (select-top 1)
                                        [(asset
                                          "PSQ"
                                          "ProShares Short QQQ")
                                         (asset
                                          "TYO"
                                          "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                         (asset
                                          "DRV"
                                          "Direxion Daily Real Estate Bear 3X Shares")
                                         (asset
                                          "TMV"
                                          "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                         (asset
                                          "SH"
                                          "ProShares Short S&P500")
                                         (group
                                          "LAB Check Bear"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (moving-average-return
                                                "XBI"
                                                {:window 600})
                                               0)
                                              [(asset
                                                "LABD"
                                                "Direxion Daily S&P Biotech Bear 3X Shares")]
                                              [(asset
                                                "SPXS"
                                                "Direxion Daily S&P 500 Bear 3x Shares")])])])])])])])]
                                [(weight-equal
                                  [(if
                                    (>
                                     (rsi "IEF" {:window 11})
                                     (rsi "IWM" {:window 16}))
                                    [(weight-equal
                                      [(filter
                                        (moving-average-return
                                         {:window 4})
                                        (select-bottom 1)
                                        [(asset
                                          "TECL"
                                          "Direxion Daily Technology Bull 3x Shares")
                                         (asset
                                          "TQQQ"
                                          "ProShares UltraPro QQQ")
                                         (asset
                                          "DRN"
                                          "Direxion Daily Real Estate Bull 3x Shares")
                                         (asset
                                          "SOXL"
                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                         (asset
                                          "URTY"
                                          "ProShares UltraPro Russell2000")
                                         (asset
                                          "TMF"
                                          "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                         (group
                                          "LAB Check Bull"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (moving-average-return
                                                "XBI"
                                                {:window 600})
                                               0)
                                              [(asset
                                                "LABU"
                                                "Direxion Daily S&P Biotech Bull 3X Shares")]
                                              [(asset
                                                "SPXL"
                                                "Direxion Daily S&P 500 Bull 3x Shares")])])])])])]
                                    [(weight-equal
                                      [(filter
                                        (moving-average-return
                                         {:window 4})
                                        (select-bottom 1)
                                        [(asset
                                          "PSQ"
                                          "ProShares Short QQQ")
                                         (asset
                                          "TYO"
                                          "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                         (asset
                                          "DRV"
                                          "Direxion Daily Real Estate Bear 3X Shares")
                                         (asset
                                          "TMV"
                                          "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                         (asset
                                          "SH"
                                          "ProShares Short S&P500")
                                         (group
                                          "LAB Check Bear"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (moving-average-return
                                                "XBI"
                                                {:window 600})
                                               0)
                                              [(asset
                                                "LABD"
                                                "Direxion Daily S&P Biotech Bear 3X Shares")]
                                              [(asset
                                                "SPXS"
                                                "Direxion Daily S&P 500 Bear 3x Shares")])])])])])])])])])]
                            [(group
                              "V1a TQQQ or not | BlackSwan MeanRev BondSignal - K-1 Free"
                              [(weight-equal
                                [(if
                                  (> (rsi "TQQQ" {:window 10}) 79)
                                  [(asset
                                    "VXX"
                                    "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
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
                                                       (rsi
                                                        "TQQQ"
                                                        {:window 10})
                                                       32)
                                                      [(asset
                                                        "TQQQ"
                                                        "ProShares UltraPro QQQ")]
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (max-drawdown
                                                            "TMF"
                                                            {:window
                                                             10})
                                                           7)
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")]
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
                                                    {:window 10})
                                                   6)
                                                  [(asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")]
                                                  [(weight-equal
                                                    [(if
                                                      (>
                                                       (max-drawdown
                                                        "TMF"
                                                        {:window 10})
                                                       7)
                                                      [(asset
                                                        "BIL"
                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")]
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
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")])]
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
                                                                      "TQQQ"
                                                                      "ProShares UltraPro QQQ")]
                                                                    [(asset
                                                                      "BIL"
                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
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
                                                                        [(asset
                                                                          "BIL"
                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                                                    [(asset
                                                                      "BIL"
                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])
                       (group
                        "WAM FTLT (short backtest)"
                        [(weight-equal
                          [(if
                            (<
                             (moving-average-return
                              "SHY"
                              {:window 575})
                             0)
                            [(weight-equal
                              [(if
                                (> (rsi "TMF" {:window 14}) 60)
                                [(weight-equal
                                  [(if
                                    (<
                                     (rsi "IEF" {:window 11})
                                     (rsi "IWM" {:window 16}))
                                    [(weight-equal
                                      [(filter
                                        (moving-average-return
                                         {:window 4})
                                        (select-top 1)
                                        [(asset
                                          "TECL"
                                          "Direxion Daily Technology Bull 3x Shares")
                                         (asset
                                          "TQQQ"
                                          "ProShares UltraPro QQQ")
                                         (asset
                                          "DRN"
                                          "Direxion Daily Real Estate Bull 3x Shares")
                                         (asset
                                          "HIBL"
                                          "Direxion Daily S&P 500 High Beta Bull 3X Shares")
                                         (asset
                                          "SOXL"
                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                         (asset
                                          "TARK"
                                          "AXS 2X Innovation ETF")
                                         (asset
                                          "URTY"
                                          "ProShares UltraPro Russell2000")
                                         (asset
                                          "TMF"
                                          "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                         (group
                                          "LAB Check Bull"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (moving-average-return
                                                "XBI"
                                                {:window 600})
                                               0)
                                              [(asset
                                                "LABU"
                                                "Direxion Daily S&P Biotech Bull 3X Shares")]
                                              [(asset
                                                "SPXL"
                                                "Direxion Daily S&P 500 Bull 3x Shares")])])])])])]
                                    [(weight-equal
                                      [(filter
                                        (moving-average-return
                                         {:window 4})
                                        (select-top 1)
                                        [(asset
                                          "PSQ"
                                          "ProShares Short QQQ")
                                         (asset
                                          "TYO"
                                          "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                         (asset
                                          "HIBS"
                                          "Direxion Daily S&P 500 High Beta Bear 3X Shares")
                                         (asset
                                          "DRV"
                                          "Direxion Daily Real Estate Bear 3X Shares")
                                         (asset
                                          "TMV"
                                          "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                         (asset
                                          "SH"
                                          "ProShares Short S&P500")
                                         (group
                                          "LAB Check Bear"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (moving-average-return
                                                "XBI"
                                                {:window 600})
                                               0)
                                              [(asset
                                                "LABD"
                                                "Direxion Daily S&P Biotech Bear 3X Shares")]
                                              [(asset
                                                "SPXS"
                                                "Direxion Daily S&P 500 Bear 3x Shares")])])])])])])])]
                                [(weight-equal
                                  [(if
                                    (>
                                     (rsi "IEF" {:window 11})
                                     (rsi "IWM" {:window 16}))
                                    [(weight-equal
                                      [(filter
                                        (moving-average-return
                                         {:window 4})
                                        (select-bottom 1)
                                        [(asset
                                          "TECL"
                                          "Direxion Daily Technology Bull 3x Shares")
                                         (asset
                                          "TQQQ"
                                          "ProShares UltraPro QQQ")
                                         (asset
                                          "DRN"
                                          "Direxion Daily Real Estate Bull 3x Shares")
                                         (asset
                                          "HIBL"
                                          "Direxion Daily S&P 500 High Beta Bull 3X Shares")
                                         (asset
                                          "SOXL"
                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                         (asset
                                          "TARK"
                                          "AXS 2X Innovation ETF")
                                         (asset
                                          "URTY"
                                          "ProShares UltraPro Russell2000")
                                         (asset
                                          "TMF"
                                          "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                         (group
                                          "LAB Check Bull"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (moving-average-return
                                                "XBI"
                                                {:window 600})
                                               0)
                                              [(asset
                                                "LABU"
                                                "Direxion Daily S&P Biotech Bull 3X Shares")]
                                              [(asset
                                                "SPXL"
                                                "Direxion Daily S&P 500 Bull 3x Shares")])])])])])]
                                    [(weight-equal
                                      [(filter
                                        (moving-average-return
                                         {:window 4})
                                        (select-bottom 1)
                                        [(asset
                                          "PSQ"
                                          "ProShares Short QQQ")
                                         (asset
                                          "TYO"
                                          "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                         (asset
                                          "HIBS"
                                          "Direxion Daily S&P 500 High Beta Bear 3X Shares")
                                         (asset
                                          "DRV"
                                          "Direxion Daily Real Estate Bear 3X Shares")
                                         (asset
                                          "TMV"
                                          "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                         (asset
                                          "SH"
                                          "ProShares Short S&P500")
                                         (group
                                          "LAB Check Bear"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (moving-average-return
                                                "XBI"
                                                {:window 600})
                                               0)
                                              [(asset
                                                "LABD"
                                                "Direxion Daily S&P Biotech Bear 3X Shares")]
                                              [(asset
                                                "SPXS"
                                                "Direxion Daily S&P 500 Bear 3x Shares")])])])])])])])])])]
                            [(group
                              "V1a TQQQ or not | BlackSwan MeanRev BondSignal - K-1 Free"
                              [(weight-equal
                                [(if
                                  (> (rsi "TQQQ" {:window 10}) 79)
                                  [(asset
                                    "VXX"
                                    "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
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
                                                       (rsi
                                                        "TQQQ"
                                                        {:window 10})
                                                       32)
                                                      [(asset
                                                        "TQQQ"
                                                        "ProShares UltraPro QQQ")]
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (max-drawdown
                                                            "TMF"
                                                            {:window
                                                             10})
                                                           7)
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")]
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
                                                    {:window 10})
                                                   6)
                                                  [(asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")]
                                                  [(weight-equal
                                                    [(if
                                                      (>
                                                       (max-drawdown
                                                        "TMF"
                                                        {:window 10})
                                                       7)
                                                      [(asset
                                                        "BIL"
                                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")]
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
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")])]
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
                                                                      "TQQQ"
                                                                      "ProShares UltraPro QQQ")]
                                                                    [(asset
                                                                      "BIL"
                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
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
                                                                        [(asset
                                                                          "BIL"
                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                                                    [(asset
                                                                      "BIL"
                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])]
              [(group
                "V1a WAM FTLT (TMF Check) - K-1 Free - (long backtest)"
                [(weight-equal
                  [(group
                    "WAM FTLT (long backtest)"
                    [(weight-equal
                      [(if
                        (<
                         (moving-average-return "SHY" {:window 575})
                         0)
                        [(weight-equal
                          [(if
                            (> (rsi "TMF" {:window 14}) 60)
                            [(weight-equal
                              [(if
                                (<
                                 (rsi "IEF" {:window 11})
                                 (rsi "IWM" {:window 16}))
                                [(weight-equal
                                  [(filter
                                    (moving-average-return {:window 4})
                                    (select-top 1)
                                    [(asset
                                      "TECL"
                                      "Direxion Daily Technology Bull 3x Shares")
                                     (asset
                                      "TQQQ"
                                      "ProShares UltraPro QQQ")
                                     (asset
                                      "DRN"
                                      "Direxion Daily Real Estate Bull 3x Shares")
                                     (asset
                                      "SOXL"
                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                     (asset
                                      "URTY"
                                      "ProShares UltraPro Russell2000")
                                     (asset
                                      "TMF"
                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                     (group
                                      "LAB Check Bull"
                                      [(weight-equal
                                        [(if
                                          (<
                                           (moving-average-return
                                            "XBI"
                                            {:window 600})
                                           0)
                                          [(asset
                                            "LABU"
                                            "Direxion Daily S&P Biotech Bull 3X Shares")]
                                          [(asset
                                            "SPXL"
                                            "Direxion Daily S&P 500 Bull 3x Shares")])])])])])]
                                [(weight-equal
                                  [(filter
                                    (moving-average-return {:window 4})
                                    (select-top 1)
                                    [(asset
                                      "PSQ"
                                      "ProShares Short QQQ")
                                     (asset
                                      "TYO"
                                      "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                     (asset
                                      "DRV"
                                      "Direxion Daily Real Estate Bear 3X Shares")
                                     (asset
                                      "TMV"
                                      "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                     (asset
                                      "SH"
                                      "ProShares Short S&P500")
                                     (group
                                      "LAB Check Bear"
                                      [(weight-equal
                                        [(if
                                          (<
                                           (moving-average-return
                                            "XBI"
                                            {:window 600})
                                           0)
                                          [(asset
                                            "LABD"
                                            "Direxion Daily S&P Biotech Bear 3X Shares")]
                                          [(asset
                                            "SPXS"
                                            "Direxion Daily S&P 500 Bear 3x Shares")])])])])])])])]
                            [(weight-equal
                              [(if
                                (>
                                 (rsi "IEF" {:window 11})
                                 (rsi "IWM" {:window 16}))
                                [(weight-equal
                                  [(filter
                                    (moving-average-return {:window 4})
                                    (select-bottom 1)
                                    [(asset
                                      "TECL"
                                      "Direxion Daily Technology Bull 3x Shares")
                                     (asset
                                      "TQQQ"
                                      "ProShares UltraPro QQQ")
                                     (asset
                                      "DRN"
                                      "Direxion Daily Real Estate Bull 3x Shares")
                                     (asset
                                      "SOXL"
                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                     (asset
                                      "URTY"
                                      "ProShares UltraPro Russell2000")
                                     (asset
                                      "TMF"
                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                     (group
                                      "LAB Check Bull"
                                      [(weight-equal
                                        [(if
                                          (<
                                           (moving-average-return
                                            "XBI"
                                            {:window 600})
                                           0)
                                          [(asset
                                            "LABU"
                                            "Direxion Daily S&P Biotech Bull 3X Shares")]
                                          [(asset
                                            "SPXL"
                                            "Direxion Daily S&P 500 Bull 3x Shares")])])])])])]
                                [(weight-equal
                                  [(filter
                                    (moving-average-return {:window 4})
                                    (select-bottom 1)
                                    [(asset
                                      "PSQ"
                                      "ProShares Short QQQ")
                                     (asset
                                      "TYO"
                                      "Direxion Daily 7-10 Year Treasury Bear 3x Shares")
                                     (asset
                                      "DRV"
                                      "Direxion Daily Real Estate Bear 3X Shares")
                                     (asset
                                      "TMV"
                                      "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                     (asset
                                      "SH"
                                      "ProShares Short S&P500")
                                     (group
                                      "LAB Check Bear"
                                      [(weight-equal
                                        [(if
                                          (<
                                           (moving-average-return
                                            "XBI"
                                            {:window 600})
                                           0)
                                          [(asset
                                            "LABD"
                                            "Direxion Daily S&P Biotech Bear 3X Shares")]
                                          [(asset
                                            "SPXS"
                                            "Direxion Daily S&P 500 Bear 3x Shares")])])])])])])])])])]
                        [(group
                          "V1a TQQQ or not | BlackSwan MeanRev BondSignal - K-1 Free"
                          [(weight-equal
                            [(if
                              (> (rsi "TQQQ" {:window 10}) 79)
                              [(asset
                                "VXX"
                                "iPath Series B S&P 500 VIX Short-Term Futures ETN")]
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
                                                   (rsi
                                                    "TQQQ"
                                                    {:window 10})
                                                   32)
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (max-drawdown
                                                        "TMF"
                                                        {:window 10})
                                                       7)
                                                      [(asset
                                                        "TQQQ"
                                                        "ProShares UltraPro QQQ")]
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
                                                {:window 10})
                                               6)
                                              [(asset
                                                "BIL"
                                                "SPDR Bloomberg 1-3 Month T-Bill ETF")]
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (max-drawdown
                                                    "TMF"
                                                    {:window 10})
                                                   7)
                                                  [(asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")]
                                                  [(weight-equal
                                                    [(if
                                                      (>
                                                       (current-price
                                                        "QQQ")
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
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")]
                                                                [(asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])]
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
                                                                    [(asset
                                                                      "BIL"
                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                                                [(asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]))
