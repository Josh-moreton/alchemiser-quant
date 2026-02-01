(defsymphony
 "BT 1Nov16-22Nov22 AR 1317.2% DD 37.7% Daily TQQQ For The Long Term V4.2.5a  16d CR 11d + 12d Rule | Garen Mod selectively replaced SQQQ -> SOXS & TQQQ -> SOXL"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(weight-equal
    [(group
      "TQQQ For The Long Term V4.2 (1957.0% RR/27.6% Max DD)"
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
                        (< (cumulative-return "QQQ" {:window 5}) -6)
                        [(weight-equal
                          [(if
                            (>
                             (cumulative-return "TQQQ" {:window 1})
                             5)
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
                                  "SOXL"
                                  "Direxion Daily Semiconductor Bull 3x Shares")])])])])]
                        [(weight-specified
                          1
                          (if
                           (> (rsi "QQQ" {:window 10}) 80)
                           [(asset
                             "SQQQ"
                             "ProShares UltraPro Short QQQ")]
                           [(weight-equal
                             [(if
                               (< (rsi "QQQ" {:window 10}) 31)
                               [(asset
                                 "SOXL"
                                 "Direxion Daily Semiconductor Bull 3x Shares")]
                               [(group
                                 "\"A Better QQQ\""
                                 [(weight-equal
                                   [(weight-specified
                                     0.49
                                     (filter
                                      (moving-average-return
                                       {:window 11})
                                      (select-top 1)
                                      [(asset
                                        "ACLS"
                                        "Axcelis Technologies, Inc.")
                                       (asset
                                        "MNST"
                                        "Monster Beverage Corporation")
                                       (asset
                                        "LULU"
                                        "Lululemon Athletica Inc")
                                       (asset
                                        "JKHY"
                                        "Jack Henry & Associates, Inc.")
                                       (asset
                                        "INFY"
                                        "Infosys Limited Sponsored ADR")
                                       (asset
                                        "GNRC"
                                        "Generac Holdings Inc.")
                                       (asset "EXPO" "Exponent, Inc.")
                                       (asset
                                        "DVAX"
                                        "Dynavax Technologies Corporation")
                                       (asset
                                        "DAC"
                                        "Danaos Corporation")
                                       (asset
                                        "SIMO"
                                        "Silicon Motion Technology Corporation Sponsored ADR")
                                       (asset
                                        "SFM"
                                        "Sprouts Farmers Market, Inc.")
                                       (asset
                                        "ROST"
                                        "Ross Stores, Inc.")
                                       (asset
                                        "QCOM"
                                        "Qualcomm Incorporated")
                                       (asset "BIL" nil)
                                       (asset
                                        "PCH"
                                        "PotlatchDeltic Corporation")
                                       (asset
                                        "PAYC"
                                        "Paycom Software, Inc.")
                                       (asset
                                        "NVDA"
                                        "NVIDIA Corporation")
                                       (asset "MOS" "Mosaic Company")
                                       (asset
                                        "MU"
                                        "Micron Technology, Inc.")
                                       (asset "TSLA" "Tesla Inc")
                                       (asset "TPR" "Tapestry, Inc.")
                                       (asset
                                        "SQM"
                                        "Sociedad Quimica Y Minera De Chile S.A. Sponsored ADR Pfd Class B")])
                                     0.12
                                     (filter
                                      (moving-average-return
                                       {:window 12})
                                      (select-top 1)
                                      [(asset "AA" "Alcoa Corporation")
                                       (asset
                                        "ALGN"
                                        "Align Technology, Inc.")
                                       (asset
                                        "AMD"
                                        "Advanced Micro Devices, Inc.")
                                       (asset
                                        "AR"
                                        "Antero Resources Corporation")
                                       (asset
                                        "ASML"
                                        "ASML Holding NV ADR")
                                       (asset "AVGO" "Broadcom Inc.")
                                       (asset
                                        "ENPH"
                                        "Enphase Energy, Inc.")
                                       (asset "JYNT" "Joint Corp")
                                       (asset
                                        "MU"
                                        "Micron Technology, Inc.")
                                       (asset
                                        "OXY"
                                        "Occidental Petroleum Corporation")
                                       (asset
                                        "TQQQ"
                                        "ProShares UltraPro QQQ")
                                       (asset
                                        "TSM"
                                        "Taiwan Semiconductor Manufacturing Co., Ltd. Sponsored ADR")])
                                     0.39
                                     (filter
                                      (moving-average-return
                                       {:window 16})
                                      (select-top 1)
                                      [(asset
                                        "AMD"
                                        "Advanced Micro Devices, Inc.")
                                       (asset
                                        "ENPH"
                                        "Enphase Energy, Inc.")
                                       (asset "EQT" "EQT Corporation")
                                       (asset
                                        "SON"
                                        "Sonoco Products Company")
                                       (asset
                                        "VRTX"
                                        "Vertex Pharmaceuticals Incorporated")
                                       (asset
                                        "AA"
                                        "Alcoa Corporation")]))])])])])]))])])])])])])])]
          [(weight-equal
            [(if
              (< (rsi "TQQQ" {:window 9}) 32)
              [(weight-equal
                [(if
                  (>=
                   (cumulative-return "TQQQ" {:window 2})
                   (cumulative-return "TQQQ" {:window 5}))
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
                      (rsi {:window 10})
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
                            (> (rsi "UVXY" {:window 10}) 74)
                            [(weight-equal
                              [(if
                                (> (rsi "UVXY" {:window 10}) 84)
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
                                    (< (rsi "SQQQ" {:window 10}) 31)
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
                      (> (rsi "UVXY" {:window 10}) 74)
                      [(weight-equal
                        [(if
                          (> (rsi "UVXY" {:window 10}) 84)
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
                           (moving-average-price "TQQQ" {:window 20}))
                          [(weight-equal
                            [(if
                              (< (rsi "SQQQ" {:window 10}) 31)
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
                                "ProShares UltraPro Short QQQ")])])])])])])])])])])])])])])]))
