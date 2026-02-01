(defsymphony
 "2017 BT TQQQ For The Long Term w/ SPXT Switch"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
    (> (rsi "SPY" {:window 10}) 80)
    [(asset
      "UVXY"
      "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
    [(weight-equal
      [(if
        (> (rsi "TECL" {:window 10}) 79)
        [(asset
          "UVXY"
          "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
        [(weight-equal
          [(if
            (> (rsi "XLP" {:window 10}) 77.5)
            [(weight-equal
              [(if
                (> (rsi "XLP" {:window 10}) 80)
                [(asset
                  "UVXY"
                  "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
                [(asset
                  "VIXY"
                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")])])]
            [(weight-equal
              [(if
                (> (rsi "QQQ" {:window 10}) 79)
                [(weight-equal
                  [(if
                    (> (rsi "QQQ" {:window 10}) 81)
                    [(asset
                      "UVXY"
                      "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
                    [(asset
                      "VIXY"
                      "ProShares Trust - ProShares VIX Short-Term Futures ETF")])])]
                [(weight-equal
                  [(if
                    (> (rsi "QQQE" {:window 10}) 79)
                    [(weight-equal
                      [(if
                        (> (rsi "QQQE" {:window 10}) 83)
                        [(asset
                          "UVXY"
                          "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
                        [(asset
                          "VIXY"
                          "ProShares Trust - ProShares VIX Short-Term Futures ETF")])])]
                    [(weight-equal
                      [(if
                        (< (rsi "TQQQ" {:window 10}) 31)
                        [(weight-equal
                          [(if
                            (< (rsi "SMH" {:window 10}) 23)
                            [(asset
                              "SOXL"
                              "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                            [(weight-equal
                              [(if
                                (< (rsi "QQQ" {:window 10}) 27)
                                [(asset
                                  "TECL"
                                  "Direxion Shares ETF Trust - Direxion Daily Technology Bull 3X Shares")]
                                [(group
                                  "Check With Bonds"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (rsi "AGG" {:window 20})
                                       (rsi "SH" {:window 60}))
                                      [(group
                                        "Safe Sectors or Bonds"
                                        [(weight-equal
                                          [(filter
                                            (rsi {:window 10})
                                            (select-bottom 1)
                                            [(asset
                                              "BSV"
                                              "Vanguard Group, Inc. - Vanguard Short-Term Bond ETF")
                                             (asset
                                              "TLT"
                                              "BlackRock Institutional Trust Company N.A. - iShares 20+ Year Treasury Bond ETF")
                                             (asset
                                              "LQD"
                                              "BlackRock Institutional Trust Company N.A. - iShares iBoxx USD Investment Grade Corporate Bond ETF")
                                             (asset
                                              "VBF"
                                              "Invesco Bond Fund")
                                             (asset
                                              "XLP"
                                              "SSgA Active Trust - Consumer Staples Select Sector SPDR")
                                             (asset
                                              "UGE"
                                              "ProShares Trust - ProShares Ultra Consumer Staples")
                                             (asset
                                              "XLV"
                                              "SSgA Active Trust - Health Care Select Sector SPDR")
                                             (asset
                                              "XLU"
                                              "SSgA Active Trust - Utilities Select Sector SPDR ETF")])])])]
                                      [(asset
                                        "TECL"
                                        "Direxion Shares ETF Trust - Direxion Daily Technology Bull 3X Shares")])
                                     (if
                                      (>
                                       (rsi "AGG" {:window 15})
                                       (rsi "SH" {:window 15}))
                                      [(group
                                        "Safe Sectors or Bonds"
                                        [(weight-equal
                                          [(filter
                                            (rsi {:window 10})
                                            (select-bottom 1)
                                            [(asset "BSV" nil)
                                             (asset "TLT" nil)
                                             (asset "LQD" nil)
                                             (asset "VBF" nil)
                                             (asset "XLP" nil)
                                             (asset "UGE" nil)
                                             (asset "XLV" nil)
                                             (asset "XLU" nil)])])])]
                                      [(asset
                                        "TECL"
                                        "Direxion Shares ETF Trust - Direxion Daily Technology Bull 3X Shares")])
                                     (if
                                      (>
                                       (rsi "IEF" {:window 10})
                                       (rsi "SH" {:window 20}))
                                      [(group
                                        "Safe Sectors or Bonds"
                                        [(weight-equal
                                          [(filter
                                            (rsi {:window 10})
                                            (select-bottom 1)
                                            [(asset "BSV" nil)
                                             (asset "TLT" nil)
                                             (asset "LQD" nil)
                                             (asset "VBF" nil)
                                             (asset "XLP" nil)
                                             (asset "UGE" nil)
                                             (asset "XLV" nil)
                                             (asset "XLU" nil)])])])]
                                      [(asset
                                        "TECL"
                                        "Direxion Shares ETF Trust - Direxion Daily Technology Bull 3X Shares")])])])])])])])]
                        [(weight-equal
                          [(if
                            (> (rsi "VTV" {:window 10}) 79)
                            [(asset "VIXY" nil)]
                            [(weight-equal
                              [(if
                                (> (rsi "XLY" {:window 10}) 80)
                                [(asset "VIXY" nil)]
                                [(weight-equal
                                  [(if
                                    (> (rsi "XLF" {:window 10}) 80)
                                    [(asset "VIXY" nil)]
                                    [(weight-equal
                                      [(group
                                        "TQQQ For The Long Term (Reddit Post Link) (177,53,2011)"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (current-price "SPY")
                                             (moving-average-price
                                              "SPY"
                                              {:window 200}))
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "QQQ"
                                                  {:window 15})
                                                 (rsi
                                                  "SPXT"
                                                  {:window 15}))
                                                [(asset
                                                  "TQQQ"
                                                  "ProShares Trust - ProShares UltraPro QQQ 3x Shares")
                                                 (asset
                                                  "SOXL"
                                                  "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")
                                                 (asset
                                                  "TECL"
                                                  "Direxion Shares ETF Trust - Direxion Daily Technology Bull 3X Shares")]
                                                [(weight-equal
                                                  [(filter
                                                    (cumulative-return
                                                     {:window 30})
                                                    (select-top 3)
                                                    [(asset
                                                      "UDOW"
                                                      "ProShares Trust - ProShares UltraPro Dow30 3x Shares")
                                                     (asset
                                                      "SPXL"
                                                      "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bull 3X Shares")
                                                     (asset
                                                      "URTY"
                                                      "ProShares Trust - ProShares UltraPro Russell2000 3x Shares")
                                                     (asset
                                                      "CURE"
                                                      "Direxion Shares ETF Trust - Direxion Daily Healthcare Bull 3X Shares")
                                                     (asset
                                                      "TNA"
                                                      "Direxion Shares ETF Trust - Direxion Daily Small Cap Bull 3X Shares")
                                                     (asset
                                                      "LABU"
                                                      "Direxion Shares ETF Trust - Direxion Daily S&P Biotech Bull 3X Shares")
                                                     (asset
                                                      "EDC"
                                                      "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                                                     (asset
                                                      "YINN"
                                                      "Direxion Shares ETF Trust - Direxion Daily FTSE China Bull 3X Shares")
                                                     (asset
                                                      "RETL"
                                                      "Direxion Shares ETF Trust - Direxion Daily Retail Bull 3x Shares")
                                                     (asset
                                                      "FAZ"
                                                      "Direxion Shares ETF Trust - Direxion Daily Financial Bear 3x Shares")
                                                     (asset
                                                      "UTSL"
                                                      "Direxion Shares ETF Trust - Direxion Daily Utilities Bull 3X Shares")
                                                     (asset
                                                      "PILL"
                                                      "Direxion Shares ETF Trust - Direxion Daily Pharmaceutical & Medical Bull 3X Shares")
                                                     (asset
                                                      "TQQQ"
                                                      "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])])])]
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
                                                         (rsi
                                                          "QQQ"
                                                          {:window 15})
                                                         (rsi
                                                          "SPXT"
                                                          {:window
                                                           15}))
                                                        [(asset
                                                          "TQQQ"
                                                          "ProShares Trust - ProShares UltraPro QQQ 3x Shares")
                                                         (asset
                                                          "SOXL"
                                                          "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")
                                                         (asset
                                                          "TECL"
                                                          "Direxion Shares ETF Trust - Direxion Daily Technology Bull 3X Shares")]
                                                        [(weight-equal
                                                          [(filter
                                                            (cumulative-return
                                                             {:window
                                                              30})
                                                            (select-top
                                                             3)
                                                            [(asset
                                                              "UDOW"
                                                              "ProShares Trust - ProShares UltraPro Dow30 3x Shares")
                                                             (asset
                                                              "SPXL"
                                                              "Direxion Shares ETF Trust - Direxion Daily S&P 500 Bull 3X Shares")
                                                             (asset
                                                              "URTY"
                                                              "ProShares Trust - ProShares UltraPro Russell2000 3x Shares")
                                                             (asset
                                                              "CURE"
                                                              "Direxion Shares ETF Trust - Direxion Daily Healthcare Bull 3X Shares")
                                                             (asset
                                                              "TNA"
                                                              "Direxion Shares ETF Trust - Direxion Daily Small Cap Bull 3X Shares")
                                                             (asset
                                                              "LABU"
                                                              "Direxion Shares ETF Trust - Direxion Daily S&P Biotech Bull 3X Shares")
                                                             (asset
                                                              "EDC"
                                                              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")
                                                             (asset
                                                              "YINN"
                                                              "Direxion Shares ETF Trust - Direxion Daily FTSE China Bull 3X Shares")
                                                             (asset
                                                              "RETL"
                                                              "Direxion Shares ETF Trust - Direxion Daily Retail Bull 3x Shares")
                                                             (asset
                                                              "FAZ"
                                                              "Direxion Shares ETF Trust - Direxion Daily Financial Bear 3x Shares")
                                                             (asset
                                                              "UTSL"
                                                              "Direxion Shares ETF Trust - Direxion Daily Utilities Bull 3X Shares")
                                                             (asset
                                                              "PILL"
                                                              "Direxion Shares ETF Trust - Direxion Daily Pharmaceutical & Medical Bull 3X Shares")
                                                             (asset
                                                              "TQQQ"
                                                              "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]))
