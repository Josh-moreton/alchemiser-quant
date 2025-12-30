(defsymphony
 "Nuclear Energy with Feaver Frontrunner V5 | BT 2022-03-24"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "Nuclear Energy with Feaver Frontrunner V5 | BT 2022-03-24"
    [(weight-equal
      [(if
        (> (rsi "SPY" {:window 10}) 79)
        [(weight-equal
          [(if
            (> (rsi "SPY" {:window 10}) 81)
            [(asset
              "UVXY"
              "ProShares Ultra VIX Short-Term Futures ETF")]
            [(weight-equal
              [(if
                (> (rsi "IOO" {:window 10}) 81)
                [(asset
                  "UVXY"
                  "ProShares Ultra VIX Short-Term Futures ETF")]
                [(weight-equal
                  [(if
                    (> (rsi "TQQQ" {:window 10}) 81)
                    [(asset
                      "UVXY"
                      "ProShares Ultra VIX Short-Term Futures ETF")]
                    [(weight-equal
                      [(if
                        (> (rsi "VTV" {:window 10}) 81)
                        [(asset
                          "UVXY"
                          "ProShares Ultra VIX Short-Term Futures ETF")]
                        [(weight-equal
                          [(if
                            (> (rsi "XLF" {:window 10}) 81)
                            [(asset
                              "UVXY"
                              "ProShares Ultra VIX Short-Term Futures ETF")]
                            [(group
                              "UVXY 75|25 BTAL"
                              [(weight-specified
                                0.75
                                (asset
                                 "UVXY"
                                 "ProShares Ultra VIX Short-Term Futures ETF")
                                0.25
                                (asset
                                 "BTAL"
                                 "AGF U.S. Market Neutral Anti-Beta Fund"))])])])])])])])])])])])]
        [(weight-equal
          [(if
            (> (rsi "IOO" {:window 10}) 79)
            [(weight-equal
              [(if
                (> (rsi "IOO" {:window 10}) 81)
                [(asset
                  "UVXY"
                  "ProShares Ultra VIX Short-Term Futures ETF")]
                [(weight-equal
                  [(if
                    (> (rsi "TQQQ" {:window 10}) 81)
                    [(asset
                      "UVXY"
                      "ProShares Ultra VIX Short-Term Futures ETF")]
                    [(weight-equal
                      [(if
                        (> (rsi "VTV" {:window 10}) 81)
                        [(asset
                          "UVXY"
                          "ProShares Ultra VIX Short-Term Futures ETF")]
                        [(weight-equal
                          [(if
                            (> (rsi "XLF" {:window 10}) 81)
                            [(asset
                              "UVXY"
                              "ProShares Ultra VIX Short-Term Futures ETF")]
                            [(group
                              "UVXY 75|25 BTAL"
                              [(weight-specified
                                0.75
                                (asset
                                 "UVXY"
                                 "ProShares Ultra VIX Short-Term Futures ETF")
                                0.25
                                (asset
                                 "BTAL"
                                 "AGF U.S. Market Neutral Anti-Beta Fund"))])])])])])])])])])]
            [(weight-equal
              [(if
                (> (rsi "TQQQ" {:window 10}) 79)
                [(weight-equal
                  [(if
                    (> (rsi "TQQQ" {:window 10}) 81)
                    [(asset
                      "UVXY"
                      "ProShares Ultra VIX Short-Term Futures ETF")]
                    [(weight-equal
                      [(if
                        (> (rsi "VTV" {:window 10}) 81)
                        [(asset
                          "UVXY"
                          "ProShares Ultra VIX Short-Term Futures ETF")]
                        [(weight-equal
                          [(if
                            (> (rsi "XLF" {:window 10}) 81)
                            [(asset
                              "UVXY"
                              "ProShares Ultra VIX Short-Term Futures ETF")]
                            [(group
                              "UVXY 75|25 BTAL"
                              [(weight-specified
                                0.75
                                (asset
                                 "UVXY"
                                 "ProShares Ultra VIX Short-Term Futures ETF")
                                0.25
                                (asset
                                 "BTAL"
                                 "AGF U.S. Market Neutral Anti-Beta Fund"))])])])])])])])]
                [(weight-equal
                  [(if
                    (> (rsi "VTV" {:window 10}) 79)
                    [(weight-equal
                      [(if
                        (> (rsi "VTV" {:window 10}) 81)
                        [(asset
                          "UVXY"
                          "ProShares Ultra VIX Short-Term Futures ETF")]
                        [(weight-equal
                          [(if
                            (> (rsi "XLF" {:window 10}) 81)
                            [(asset
                              "UVXY"
                              "ProShares Ultra VIX Short-Term Futures ETF")]
                            [(group
                              "UVXY 75|25 BTAL"
                              [(weight-specified
                                0.75
                                (asset
                                 "UVXY"
                                 "ProShares Ultra VIX Short-Term Futures ETF")
                                0.25
                                (asset
                                 "BTAL"
                                 "AGF U.S. Market Neutral Anti-Beta Fund"))])])])])])]
                    [(weight-equal
                      [(if
                        (> (rsi "XLF" {:window 10}) 79)
                        [(weight-equal
                          [(if
                            (> (rsi "XLF" {:window 10}) 81)
                            [(asset
                              "UVXY"
                              "ProShares Ultra VIX Short-Term Futures ETF")]
                            [(group
                              "UVXY 75|25 BTAL"
                              [(weight-specified
                                0.75
                                (asset
                                 "UVXY"
                                 "ProShares Ultra VIX Short-Term Futures ETF")
                                0.25
                                (asset
                                 "BTAL"
                                 "AGF U.S. Market Neutral Anti-Beta Fund"))])])])]
                        [(weight-equal
                          [(if
                            (> (rsi "VOX" {:window 10}) 79)
                            [(weight-equal
                              [(weight-equal
                                [(if
                                  (> (rsi "XLF" {:window 10}) 81)
                                  [(asset
                                    "UVXY"
                                    "ProShares Ultra VIX Short-Term Futures ETF")]
                                  [(group
                                    "UVXY 75|25 BTAL"
                                    [(weight-specified
                                      0.75
                                      (asset
                                       "UVXY"
                                       "ProShares Ultra VIX Short-Term Futures ETF")
                                      0.25
                                      (asset
                                       "BTAL"
                                       "AGF U.S. Market Neutral Anti-Beta Fund"))])])])])]
                            [(weight-equal
                              [(if
                                (< (rsi "TQQQ" {:window 10}) 30)
                                [(asset
                                  "TQQQ"
                                  "ProShares UltraPro QQQ")]
                                [(weight-equal
                                  [(if
                                    (< (rsi "SPY" {:window 10}) 30)
                                    [(asset
                                      "UPRO"
                                      "ProShares UltraPro S&P500")]
                                    [(weight-equal
                                      [(if
                                        (>
                                         (current-price "SPY")
                                         (moving-average-price
                                          "SPY"
                                          {:window 200}))
                                        [(group
                                          "Bull"
                                          [(weight-equal
                                            [(group
                                              "Nuclear Energy Portfolio"
                                              [(weight-inverse-volatility
                                                90
                                                [(filter
                                                  (moving-average-return
                                                   {:window 90})
                                                  (select-top 3)
                                                  [(asset "SMR" nil)
                                                   (asset "BWXT" nil)
                                                   (asset "LEU" nil)
                                                   (asset "EXC" nil)
                                                   (asset "NLR" nil)
                                                   (asset
                                                    "OKLO"
                                                    "Oklo Inc. Class A")])])])])])]
                                        [(group
                                          "Bear"
                                          [(weight-inverse-volatility
                                            14
                                            [(group
                                              "Bear 1"
                                              [(weight-equal
                                                [(if
                                                  (<
                                                   (rsi
                                                    "PSQ"
                                                    {:window 10})
                                                   35)
                                                  [(asset
                                                    "SQQQ"
                                                    "ProShares UltraPro Short QQQ")]
                                                  [(weight-equal
                                                    [(if
                                                      (<
                                                       (cumulative-return
                                                        "QQQ"
                                                        {:window 60})
                                                       -10)
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (rsi
                                                            "TLT"
                                                            {:window
                                                             20})
                                                           (rsi
                                                            "PSQ"
                                                            {:window
                                                             20}))
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")]
                                                          [(asset
                                                            "PSQ"
                                                            "ProShares Short QQQ")])])]
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (current-price
                                                            "TQQQ")
                                                           (moving-average-price
                                                            "TQQQ"
                                                            {:window
                                                             20}))
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (rsi
                                                                "TLT"
                                                                {:window
                                                                 20})
                                                               (rsi
                                                                "PSQ"
                                                                {:window
                                                                 20}))
                                                              [(asset
                                                                "TQQQ"
                                                                "ProShares UltraPro QQQ")]
                                                              [(asset
                                                                "SQQQ"
                                                                "ProShares UltraPro Short QQQ")])])]
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
                                                                "SQQQ"
                                                                "ProShares UltraPro Short QQQ")]
                                                              [(weight-equal
                                                                [(if
                                                                  (>
                                                                   (rsi
                                                                    "TLT"
                                                                    {:window
                                                                     20})
                                                                   (rsi
                                                                    "PSQ"
                                                                    {:window
                                                                     20}))
                                                                  [(asset
                                                                    "QQQ"
                                                                    "Invesco QQQ Trust Series I")]
                                                                  [(asset
                                                                    "SQQQ"
                                                                    "ProShares UltraPro Short QQQ")])])])])])])])])])])])
                                             (group
                                              "Bear 2"
                                              [(weight-equal
                                                [(if
                                                  (<
                                                   (rsi
                                                    "PSQ"
                                                    {:window 10})
                                                   35)
                                                  [(asset
                                                    "SQQQ"
                                                    "ProShares UltraPro Short QQQ")]
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
                                                          (>
                                                           (rsi
                                                            "TLT"
                                                            {:window
                                                             20})
                                                           (rsi
                                                            "PSQ"
                                                            {:window
                                                             20}))
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")]
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")])])]
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (rsi
                                                            "TLT"
                                                            {:window
                                                             20})
                                                           (rsi
                                                            "PSQ"
                                                            {:window
                                                             20}))
                                                          [(asset
                                                            "QQQ"
                                                            "Invesco QQQ Trust Series I")]
                                                          [(asset
                                                            "SQQQ"
                                                            "ProShares UltraPro Short QQQ")])])])])])])])])])])])])])])])])])])])])])])])])])])])])]))
