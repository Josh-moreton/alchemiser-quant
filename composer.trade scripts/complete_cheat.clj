(defsymphony
 "Algo 1.2"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    ""
    [(weight-equal
      [(if
        (> (rsi "QQQE" {:window 10}) 79)
        [(asset "UVXY" "ProShares Ultra VIX Short-Term Futures ETF")]
        [(weight-equal
          [(if
            (> (rsi "VTV" {:window 10}) 79)
            [(asset
              "UVXY"
              "ProShares Ultra VIX Short-Term Futures ETF")]
            [(weight-equal
              [(if
                (> (rsi "VOX" {:window 10}) 79)
                [(asset
                  "UVXY"
                  "ProShares Ultra VIX Short-Term Futures ETF")]
                [(weight-equal
                  [(if
                    (> (rsi "TECL" {:window 10}) 79)
                    [(asset
                      "UVXY"
                      "ProShares Ultra VIX Short-Term Futures ETF")]
                    [(weight-equal
                      [(if
                        (> (rsi "VOOG" {:window 10}) 79)
                        [(asset
                          "UVXY"
                          "ProShares Ultra VIX Short-Term Futures ETF")]
                        [(weight-equal
                          [(if
                            (> (rsi "VOOV" {:window 10}) 79)
                            [(asset
                              "UVXY"
                              "ProShares Ultra VIX Short-Term Futures ETF")]
                            [(weight-equal
                              [(if
                                (> (rsi "XLP" {:window 10}) 75)
                                [(asset
                                  "UVXY"
                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                [(weight-equal
                                  [(if
                                    (> (rsi "TQQQ" {:window 10}) 79)
                                    [(weight-equal
                                      [(asset
                                        "UVXY"
                                        "ProShares Ultra VIX Short-Term Futures ETF")])]
                                    [(weight-equal
                                      [(if
                                        (> (rsi "XLY" {:window 10}) 80)
                                        [(asset
                                          "UVXY"
                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "FAS" {:window 10})
                                             80)
                                            [(asset
                                              "UVXY"
                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "SPY"
                                                  {:window 10})
                                                 80)
                                                [(asset
                                                  "UVXY"
                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                [(weight-equal
                                                  [(group
                                                    "Single Popped KMLM"
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "UVXY"
                                                          {:window 21})
                                                         65)
                                                        [(weight-equal
                                                          [(group
                                                            "BSC"
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   21})
                                                                 30)
                                                                [(weight-equal
                                                                  [(filter
                                                                    (rsi
                                                                     {:window
                                                                      14})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "SOXS"
                                                                      "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bear 3X Shares")
                                                                     (asset
                                                                      "TECS"
                                                                      "Direxion Shares ETF Trust - Direxion Daily Technology Bear -3X Shares")
                                                                     (asset
                                                                      "SQQQ"
                                                                      "ProShares Trust - ProShares UltraPro Short QQQ -3x Shares")])])]
                                                                [(weight-equal
                                                                  [(filter
                                                                    (rsi
                                                                     {:window
                                                                      3})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "SOXL"
                                                                      "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")
                                                                     (asset
                                                                      "TECL"
                                                                      "Direxion Shares ETF Trust - Direxion Daily Technology Bull 3X Shares")
                                                                     (asset
                                                                      "BULZ"
                                                                      "Bank of Montreal - MicroSectorsTM Solactive FANG Innovation 3X Leveraged ETNs")])])])])])])]
                                                        [(weight-equal
                                                          [(group
                                                            "Combined Pop Bot"
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (rsi
                                                                  "TQQQ"
                                                                  {:window
                                                                   10})
                                                                 30)
                                                                [(asset
                                                                  "TECL"
                                                                  "Direxion Daily Technology Bull 3x Shares")]
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (rsi
                                                                      "SOXL"
                                                                      {:window
                                                                       10})
                                                                     30)
                                                                    [(asset
                                                                      "SOXL"
                                                                      "Direxion Daily Semiconductor Bull 3x Shares")]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "SPXL"
                                                                          {:window
                                                                           10})
                                                                         30)
                                                                        [(asset
                                                                          "TQQQ"
                                                                          "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                                        [(weight-equal
                                                                          [(group
                                                                            "Copypasta YOLO GainZs Here"
                                                                            [(weight-equal
                                                                              [(group
                                                                                "KMLM switcher: TECL, SVIX, or L/S Rotator | BT 4/13/22 = AR 164% / DD 22.2%"
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (>
                                                                                     (rsi
                                                                                      "XLK"
                                                                                      {:window
                                                                                       10})
                                                                                     (rsi
                                                                                      "KMLM"
                                                                                      {:window
                                                                                       10}))
                                                                                    [(weight-equal
                                                                                      [(filter
                                                                                        (rsi
                                                                                         {:window
                                                                                          3})
                                                                                        (select-bottom
                                                                                         1)
                                                                                        [(asset
                                                                                          "TECL"
                                                                                          "Direxion Daily Technology Bull 3x Shares")
                                                                                         (asset
                                                                                          "SOXL"
                                                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                         (asset
                                                                                          "BULZ"
                                                                                          "Bank of Montreal - MicroSectorsTM Solactive FANG Innovation 3X Leveraged ETNs")])])]
                                                                                    [(weight-equal
                                                                                      [(filter
                                                                                        (rsi
                                                                                         {:window
                                                                                          3})
                                                                                        (select-top
                                                                                         1)
                                                                                        [(asset
                                                                                          "SQQQ"
                                                                                          "ProShares UltraPro Short QQQ")
                                                                                         (asset
                                                                                          "SOXS"
                                                                                          "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bear 3X Shares")
                                                                                         (asset
                                                                                          "TECS"
                                                                                          "Direxion Shares ETF Trust - Direxion Daily Technology Bear -3X Shares")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]))
