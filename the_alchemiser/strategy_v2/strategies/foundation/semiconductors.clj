(defsymphony
 "Inside Nancy Pelosi's Chips- V3"
 {:asset-class "EQUITIES", :rebalance-threshold 0.03}
 (weight-equal
  [(if
    (> (cumulative-return "SOXX" {:window 5}) 5)
    [(weight-equal
      [(if
        (< (cumulative-return "SOXX" {:window 1}) -2)
        [(asset "SOXL" "Direxion Daily Semiconductor Bull 3x Shares")]
        [(asset
          "SOXS"
          "Direxion Daily Semiconductor Bear 3x Shares")])])]
    [(group
      "Bearish Mean Reversion"
      [(weight-equal
        [(if
          (< (cumulative-return "SOXX" {:window 5}) -5)
          [(weight-equal
            [(if
              (> (cumulative-return "SOXX" {:window 1}) 2)
              [(asset
                "SOXS"
                "Direxion Daily Semiconductor Bear 3x Shares")]
              [(asset
                "SOXL"
                "Direxion Daily Semiconductor Bull 3x Shares")])])]
          [(weight-equal
            [(group
              "NVDA"
              [(weight-equal
                [(if
                  (> (rsi "NVDA" {:window 8}) 90)
                  [(asset
                    "SOXS"
                    "Direxion Daily Semiconductor Bear 3x Shares")]
                  [(weight-equal
                    [(if
                      (< (rsi "NVDA" {:window 3}) 15)
                      [(asset
                        "SOXL"
                        "Direxion Daily Semiconductor Bull 3x Shares")]
                      [(weight-equal
                        [(if
                          (>
                           (exponential-moving-average-price
                            "SOXX"
                            {:window 10})
                           (exponential-moving-average-price
                            "SOXX"
                            {:window 200}))
                          [(weight-equal
                            [(filter
                              (moving-average-return {:window 90})
                              (select-top 1)
                              [(asset
                                "SOXX"
                                "iShares Semiconductor ETF")
                               (asset "NVDA" "NVIDIA Corporation")
                               (asset
                                "AMD"
                                "Advanced Micro Devices, Inc.")
                               (asset
                                "XLE"
                                "Energy Select Sector SPDR Fund")
                               (asset
                                "ENPH"
                                "Enphase Energy, Inc.")])])]
                          [(weight-equal
                            [(filter
                              (moving-average-return {:window 90})
                              (select-top 2)
                              [(asset "SPY" "SPDR S&P 500 ETF Trust")
                               (asset
                                "DBC"
                                "Invesco DB Commodity Index Tracking Fund")
                               (asset
                                "XLE"
                                "Energy Select Sector SPDR Fund")])])])])])])])])])
             (group
              "AMD"
              [(weight-equal
                [(if
                  (> (rsi "AMD" {:window 8}) 90)
                  [(asset
                    "SOXS"
                    "Direxion Daily Semiconductor Bear 3x Shares")]
                  [(weight-equal
                    [(if
                      (< (rsi "AMD" {:window 3}) 15)
                      [(asset
                        "SOXL"
                        "Direxion Daily Semiconductor Bull 3x Shares")]
                      [(weight-equal
                        [(if
                          (>
                           (exponential-moving-average-price
                            "SOXX"
                            {:window 10})
                           (exponential-moving-average-price
                            "SOXX"
                            {:window 200}))
                          [(weight-equal
                            [(filter
                              (moving-average-return {:window 90})
                              (select-top 1)
                              [(asset
                                "SOXX"
                                "iShares Semiconductor ETF")
                               (asset "NVDA" "NVIDIA Corporation")
                               (asset
                                "AMD"
                                "Advanced Micro Devices, Inc.")
                               (asset
                                "XLE"
                                "Energy Select Sector SPDR Fund")
                               (asset
                                "ENPH"
                                "Enphase Energy, Inc.")])])]
                          [(weight-equal
                            [(filter
                              (moving-average-return {:window 90})
                              (select-top 2)
                              [(asset "SPY" "SPDR S&P 500 ETF Trust")
                               (asset
                                "DBC"
                                "Invesco DB Commodity Index Tracking Fund")
                               (asset
                                "XLE"
                                "Energy Select Sector SPDR Fund")])])])])])])])])])])])])])])]))
