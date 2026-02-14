(defsymphony
 "Pals Minor Spell of Summon Money"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
    (> (rsi "GDXU" {:window 10}) 79)
    [(asset
      "GDXD"
      "Bank of Montreal - MicroSectors Gold Miners -3X Inverse Leveraged ETNs")]
    [(weight-equal
      [(if
        (< (rsi "GDXU" {:window 10}) 30)
        [(asset
          "GDXU"
          "Bank of Montreal - MicroSectors Gold Miners 3X Leveraged ETN")]
        [(weight-equal
          [(if
            (>
             (cumulative-return "QQQ" {:window 90})
             (cumulative-return "QQQ" {:window 70}))
            [(weight-equal
              [(if
                (<
                 (cumulative-return "GDXU" {:window 70})
                 (cumulative-return "GDXU" {:window 75}))
                [(asset
                  "GDXU"
                  "Bank of Montreal - MicroSectors Gold Miners 3X Leveraged ETN")]
                [(weight-equal
                  [(group
                    "PP MAX TEC"
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
                                  [(group
                                    "Feaver Frontrunner V3 Con PP filter"
                                    [(weight-equal
                                      [(if
                                        (> (rsi "SPY" {:window 10}) 79)
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "SPY" {:window 10})
                                             81)
                                            [(asset
                                              "UVXY"
                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "IOO"
                                                  {:window 10})
                                                 81)
                                                [(asset
                                                  "UVXY"
                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "TQQQ"
                                                      {:window 10})
                                                     81)
                                                    [(asset
                                                      "UVXY"
                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         81)
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "XLF"
                                                              {:window
                                                               10})
                                                             81)
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                            [(group
                                                              "UVXY 75|25 BIL/BTAL"
                                                              [(weight-specified
                                                                0.75
                                                                (asset
                                                                 "UVXY"
                                                                 "ProShares Ultra VIX Short-Term Futures ETF")
                                                                0.25
                                                                (group
                                                                 "BIL 50|50 BTAL"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "BIL"
                                                                     "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                    (asset
                                                                     "BTAL"
                                                                     "AGF U.S. Market Neutral Anti-Beta Fund")])]))])])])])])])])])])])])]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "IOO" {:window 10})
                                             79)
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "IOO"
                                                  {:window 10})
                                                 81)
                                                [(asset
                                                  "UVXY"
                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "TQQQ"
                                                      {:window 10})
                                                     81)
                                                    [(asset
                                                      "UVXY"
                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         81)
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "XLF"
                                                              {:window
                                                               10})
                                                             81)
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                            [(group
                                                              "UVXY 75|25 BIL/BTAL"
                                                              [(weight-specified
                                                                0.75
                                                                (asset
                                                                 "UVXY"
                                                                 "ProShares Ultra VIX Short-Term Futures ETF")
                                                                0.25
                                                                (group
                                                                 "BIL 50|50 BTAL"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "BIL"
                                                                     "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                    (asset
                                                                     "BTAL"
                                                                     "AGF U.S. Market Neutral Anti-Beta Fund")])]))])])])])])])])])])]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "TQQQ"
                                                  {:window 10})
                                                 79)
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "TQQQ"
                                                      {:window 10})
                                                     81)
                                                    [(asset
                                                      "UVXY"
                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         81)
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "XLF"
                                                              {:window
                                                               10})
                                                             81)
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                            [(group
                                                              "UVXY 75|25 BIL/BTAL"
                                                              [(weight-specified
                                                                0.75
                                                                (asset
                                                                 "UVXY"
                                                                 "ProShares Ultra VIX Short-Term Futures ETF")
                                                                0.25
                                                                (group
                                                                 "BIL 50|50 BTAL"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "BIL"
                                                                     "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                    (asset
                                                                     "BTAL"
                                                                     "AGF U.S. Market Neutral Anti-Beta Fund")])]))])])])])])])])]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "VTV"
                                                      {:window 10})
                                                     79)
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "VTV"
                                                          {:window 10})
                                                         81)
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "XLF"
                                                              {:window
                                                               10})
                                                             81)
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                            [(group
                                                              "UVXY 75|25 BIL/BTAL"
                                                              [(weight-specified
                                                                0.75
                                                                (asset
                                                                 "UVXY"
                                                                 "ProShares Ultra VIX Short-Term Futures ETF")
                                                                0.25
                                                                (group
                                                                 "BIL 50|50 BTAL"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "BIL"
                                                                     "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                    (asset
                                                                     "BTAL"
                                                                     "AGF U.S. Market Neutral Anti-Beta Fund")])]))])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "XLF"
                                                          {:window 10})
                                                         79)
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "XLF"
                                                              {:window
                                                               10})
                                                             81)
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                            [(group
                                                              "UVXY 75|25 BIL/BTAL"
                                                              [(weight-specified
                                                                0.75
                                                                (asset
                                                                 "UVXY"
                                                                 "ProShares Ultra VIX Short-Term Futures ETF")
                                                                0.25
                                                                (group
                                                                 "BIL 50|50 BTAL"
                                                                 [(weight-equal
                                                                   [(asset
                                                                     "BIL"
                                                                     "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                    (asset
                                                                     "BTAL"
                                                                     "AGF U.S. Market Neutral Anti-Beta Fund")])]))])])])]
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               10})
                                                             30)
                                                            [(asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")]
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 30)
                                                                [(asset
                                                                  "SPXL"
                                                                  "Direxion Daily S&P 500 Bull 3x Shares")]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (current-price
                                                                      "SPY")
                                                                     (moving-average-price
                                                                      "SPY"
                                                                      {:window
                                                                       200}))
                                                                    [(group
                                                                      "Bull"
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
                                                                              (stdev-return
                                                                               {:window
                                                                                20})
                                                                              (select-top
                                                                               1)
                                                                              [(weight-equal
                                                                                [(if
                                                                                  (>
                                                                                   (moving-average-return
                                                                                    "AAPX"
                                                                                    {:window
                                                                                     10})
                                                                                   0)
                                                                                  [(asset
                                                                                    "AAPX"
                                                                                    "ETF Opportunities Trust - T-Rex 2X Long Apple Daily Target ETF")]
                                                                                  [(asset
                                                                                    "BIL"
                                                                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                                   (asset
                                                                                    "TQQQ"
                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])
                                                                               (weight-equal
                                                                                [(if
                                                                                  (>
                                                                                   (moving-average-return
                                                                                    "NVDL"
                                                                                    {:window
                                                                                     10})
                                                                                   0)
                                                                                  [(asset
                                                                                    "NVDL"
                                                                                    "GraniteShares ETF Trust - GraniteShares 2x Long NVDA Daily ETF")]
                                                                                  [(asset
                                                                                    "BIL"
                                                                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                                   (asset
                                                                                    "TQQQ"
                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])
                                                                               (weight-equal
                                                                                [(if
                                                                                  (>
                                                                                   (moving-average-return
                                                                                    "BITX"
                                                                                    {:window
                                                                                     10})
                                                                                   0)
                                                                                  [(asset
                                                                                    "BITX"
                                                                                    "Volatility Shares Trust - 2x Bitcoin Strategy ETF")]
                                                                                  [(asset
                                                                                    "BIL"
                                                                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                                   (asset
                                                                                    "TQQQ"
                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])
                                                                               (weight-equal
                                                                                [(if
                                                                                  (>
                                                                                   (moving-average-return
                                                                                    "TSLA"
                                                                                    {:window
                                                                                     10})
                                                                                   0)
                                                                                  [(asset
                                                                                    "TSLR"
                                                                                    "GraniteShares ETF Trust - GraniteShares 2x Long TSLA Daily ETF")]
                                                                                  [(asset
                                                                                    "BIL"
                                                                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                                   (asset
                                                                                    "TQQQ"
                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])
                                                                               (weight-equal
                                                                                [(if
                                                                                  (>
                                                                                   (moving-average-return
                                                                                    "META"
                                                                                    {:window
                                                                                     10})
                                                                                   0)
                                                                                  [(asset
                                                                                    "FBL"
                                                                                    "GraniteShares ETF Trust - GraniteShares 2x Long META Daily ETF")]
                                                                                  [(asset
                                                                                    "BIL"
                                                                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                                   (asset
                                                                                    "TQQQ"
                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])
                                                                               (weight-equal
                                                                                [(if
                                                                                  (>
                                                                                   (moving-average-return
                                                                                    "GGLL"
                                                                                    {:window
                                                                                     10})
                                                                                   0)
                                                                                  [(asset
                                                                                    "GGLL"
                                                                                    "Direxion Shares ETF Trust - Direxion Daily GOOGL Bull 2X Shares")]
                                                                                  [(asset
                                                                                    "BIL"
                                                                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                                   (asset
                                                                                    "TQQQ"
                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])
                                                                               (weight-equal
                                                                                [(if
                                                                                  (>
                                                                                   (moving-average-return
                                                                                    "AMZN"
                                                                                    {:window
                                                                                     10})
                                                                                   0)
                                                                                  [(asset
                                                                                    "AMZU"
                                                                                    "Direxion Shares ETF Trust - Direxion Daily AMZN Bull 2X Shares")]
                                                                                  [(asset
                                                                                    "BIL"
                                                                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                                   (asset
                                                                                    "TQQQ"
                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])
                                                                               (weight-equal
                                                                                [(if
                                                                                  (>
                                                                                   (moving-average-return
                                                                                    "RGTI"
                                                                                    {:window
                                                                                     10})
                                                                                   0)
                                                                                  [(asset
                                                                                    "RGTI"
                                                                                    "Rigetti Computing Inc")]
                                                                                  [(asset
                                                                                    "BIL"
                                                                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                                   (asset
                                                                                    "TQQQ"
                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])
                                                                               (weight-equal
                                                                                [(if
                                                                                  (>
                                                                                   (moving-average-return
                                                                                    "PLTR"
                                                                                    {:window
                                                                                     10})
                                                                                   0)
                                                                                  [(asset
                                                                                    "PLTR"
                                                                                    "Palantir Technologies Inc - Ordinary Shares - Class A")]
                                                                                  [(asset
                                                                                    "BIL"
                                                                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                                   (asset
                                                                                    "TQQQ"
                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])
                                                                               (weight-equal
                                                                                [(if
                                                                                  (>
                                                                                   (moving-average-return
                                                                                    "BABA"
                                                                                    {:window
                                                                                     10})
                                                                                   0)
                                                                                  [(asset
                                                                                    "BABA"
                                                                                    "Alibaba Group Holding Ltd - ADR")]
                                                                                  [(asset
                                                                                    "BIL"
                                                                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                                   (asset
                                                                                    "TQQQ"
                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])
                                                                               (weight-equal
                                                                                [(if
                                                                                  (>
                                                                                   (moving-average-return
                                                                                    "COIN"
                                                                                    {:window
                                                                                     10})
                                                                                   0)
                                                                                  [(asset
                                                                                    "CONL"
                                                                                    "GraniteShares ETF Trust - GraniteShares 2x Long COIN Daily ETF")]
                                                                                  [(asset
                                                                                    "BIL"
                                                                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                                   (asset
                                                                                    "TQQQ"
                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])])])]
                                                                          [(weight-equal
                                                                            [(group
                                                                              "Use 20d KMLM SMA"
                                                                              [(weight-equal
                                                                                [(if
                                                                                  (<
                                                                                   (current-price
                                                                                    "KMLM")
                                                                                   (moving-average-price
                                                                                    "KMLM"
                                                                                    {:window
                                                                                     20}))
                                                                                  [(weight-equal
                                                                                    [(filter
                                                                                      (moving-average-return
                                                                                       {:window
                                                                                        15})
                                                                                      (select-top
                                                                                       1)
                                                                                      [(asset
                                                                                        "AAPX"
                                                                                        "ETF Opportunities Trust - T-Rex 2X Long Apple Daily Target ETF")
                                                                                       (asset
                                                                                        "NVDL"
                                                                                        "GraniteShares ETF Trust - GraniteShares 2x Long NVDA Daily ETF")
                                                                                       (asset
                                                                                        "BITX"
                                                                                        "Volatility Shares Trust - 2x Bitcoin Strategy ETF")
                                                                                       (asset
                                                                                        "TSLR"
                                                                                        "GraniteShares ETF Trust - GraniteShares 2x Long TSLA Daily ETF")
                                                                                       (asset
                                                                                        "FBL"
                                                                                        "GraniteShares ETF Trust - GraniteShares 2x Long META Daily ETF")
                                                                                       (asset
                                                                                        "GGLL"
                                                                                        "Direxion Shares ETF Trust - Direxion Daily GOOGL Bull 2X Shares")
                                                                                       (asset
                                                                                        "AMZZ"
                                                                                        "GraniteShares ETF Trust - GraniteShares 2x Long AMZN Daily ETF")
                                                                                       (asset
                                                                                        "RGTI"
                                                                                        "Rigetti Computing Inc")
                                                                                       (asset
                                                                                        "PLTR"
                                                                                        "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                                                       (asset
                                                                                        "BABA"
                                                                                        "Alibaba Group Holding Ltd - ADR")
                                                                                       (asset
                                                                                        "CONL"
                                                                                        "GraniteShares ETF Trust - GraniteShares 2x Long COIN Daily ETF")])])]
                                                                                  [(weight-equal
                                                                                    [(asset
                                                                                      "TECS"
                                                                                      "Direxion Daily Technology Bear 3X Shares")
                                                                                     (asset
                                                                                      "SOXS"
                                                                                      "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                     (asset
                                                                                      "SQQQ"
                                                                                      "ProShares UltraPro Short QQQ")])])])])])])])])]
                                                                    [(group
                                                                      "Bear"
                                                                      [(weight-equal
                                                                        [(group
                                                                          "Feaver Bear Strat V1.1 (Bond Baller Mod)"
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
                                                                              [(weight-equal
                                                                                [(asset
                                                                                  "QQQ"
                                                                                  "Invesco QQQ Trust Series I")])]
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
                                                                                      (<
                                                                                       (rsi
                                                                                        "PSQ"
                                                                                        {:window
                                                                                         10})
                                                                                       35)
                                                                                      [(asset
                                                                                        "PSQ"
                                                                                        nil)]
                                                                                      [(group
                                                                                        "20d AGG vs 60d SH"
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (>
                                                                                             (rsi
                                                                                              "AGG"
                                                                                              {:window
                                                                                               20})
                                                                                             (rsi
                                                                                              "SH"
                                                                                              {:window
                                                                                               60}))
                                                                                            [(asset
                                                                                              "TQQQ"
                                                                                              "ProShares UltraPro QQQ")]
                                                                                            [(asset
                                                                                              "PSQ"
                                                                                              nil)])])])])])]
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
                                                                                        "PSQ"
                                                                                        nil)]
                                                                                      [(asset
                                                                                        "SQQQ"
                                                                                        "ProShares UltraPro Short QQQ")])])])])])
                                                                             (group
                                                                              "Feaver Bear"
                                                                              [(weight-equal
                                                                                [(if
                                                                                  (<
                                                                                   (cumulative-return
                                                                                    "QQQ"
                                                                                    {:window
                                                                                     60})
                                                                                   -12)
                                                                                  [(group
                                                                                    "BND vs QQQ"
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (rsi
                                                                                          "BND"
                                                                                          {:window
                                                                                           10})
                                                                                         (rsi
                                                                                          "QQQ"
                                                                                          {:window
                                                                                           10}))
                                                                                        [(asset
                                                                                          "QLD"
                                                                                          nil)]
                                                                                        [(asset
                                                                                          "BTAL"
                                                                                          nil)])])])]
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
                                                                                          (<
                                                                                           (rsi
                                                                                            "PSQ"
                                                                                            {:window
                                                                                             10})
                                                                                           35)
                                                                                          [(asset
                                                                                            "PSQ"
                                                                                            nil)]
                                                                                          [(group
                                                                                            "20d AGG vs 60d SH"
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (>
                                                                                                 (rsi
                                                                                                  "AGG"
                                                                                                  {:window
                                                                                                   20})
                                                                                                 (rsi
                                                                                                  "SH"
                                                                                                  {:window
                                                                                                   60}))
                                                                                                [(asset
                                                                                                  "TQQQ"
                                                                                                  nil)]
                                                                                                [(asset
                                                                                                  "PSQ"
                                                                                                  nil)])])])])])]
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
                                                                                            "PSQ"
                                                                                            nil)]
                                                                                          [(asset
                                                                                            "SQQQ"
                                                                                            nil)])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]
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
                                        (<
                                         (rsi "SQQQ" {:window 10})
                                         31)
                                        [(asset
                                          "SQQQ"
                                          "ProShares UltraPro Short QQQ")]
                                        [(weight-equal
                                          [(asset
                                            "TQQQ"
                                            "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])])])])])])])])])])])])])])]
            [(weight-equal
              [(if
                (<
                 (cumulative-return "TLT" {:window 95})
                 (cumulative-return "QQQ" {:window 35}))
                [(asset
                  "GDXD"
                  "Bank of Montreal - MicroSectors Gold Miners -3X Inverse Leveraged ETNs")]
                [(weight-equal
                  [(if
                    (>
                     (current-price "SPY")
                     (moving-average-price "SPY" {:window 200}))
                    [(weight-equal
                      [(if
                        (>
                         (moving-average-return "FAS" {:window 50})
                         (moving-average-return "FAS" {:window 200}))
                        [(weight-equal
                          [(filter
                            (moving-average-return {:window 20})
                            (select-top 3)
                            [(asset
                              "V"
                              "Visa Inc - Ordinary Shares - Class A")
                             (asset "SOFI" "SoFi Technologies Inc")
                             (asset
                              "MA"
                              "Mastercard Incorporated - Ordinary Shares - Class A")
                             (asset "BX" "Blackstone Inc")
                             (asset "SCHW" "Charles Schwab Corp.")
                             (asset "KKR" "KKR & Co. Inc")
                             (asset
                              "BN"
                              "Brookfield Corporation - Ordinary Shares - Class A")
                             (asset "WELL" "Welltower Inc.")
                             (asset "VTR" "Ventas Inc")
                             (asset
                              "BAM"
                              "Brookfield Asset Management Ltd - Ordinary Shares - Class A")
                             (asset
                              "HOOD"
                              "Robinhood Markets Inc - Ordinary Shares - Class A")
                             (asset
                              "IBKR"
                              "Interactive Brokers Group Inc - Ordinary Shares - Class A")
                             (weight-equal
                              [(if
                                (>
                                 (moving-average-return
                                  "FAS"
                                  {:window 10})
                                 (moving-average-return
                                  "QQQ"
                                  {:window 20}))
                                [(asset
                                  "FAS"
                                  "Direxion Shares ETF Trust - Direxion Daily Financial Bull 3x Shares")]
                                [(weight-equal
                                  [(filter
                                    (moving-average-return
                                     {:window 15})
                                    (select-top 1)
                                    [(asset
                                      "AAPX"
                                      "ETF Opportunities Trust - T-Rex 2X Long Apple Daily Target ETF")
                                     (asset
                                      "NVDL"
                                      "GraniteShares ETF Trust - GraniteShares 2x Long NVDA Daily ETF")
                                     (asset
                                      "BITX"
                                      "Volatility Shares Trust - 2x Bitcoin Strategy ETF")
                                     (asset
                                      "TSLR"
                                      "GraniteShares ETF Trust - GraniteShares 2x Long TSLA Daily ETF")
                                     (asset
                                      "FBL"
                                      "GraniteShares ETF Trust - GraniteShares 2x Long META Daily ETF")
                                     (asset
                                      "GGLL"
                                      "Direxion Shares ETF Trust - Direxion Daily GOOGL Bull 2X Shares")
                                     (asset
                                      "AMZZ"
                                      "GraniteShares ETF Trust - GraniteShares 2x Long AMZN Daily ETF")
                                     (asset
                                      "RGTI"
                                      "Rigetti Computing Inc")
                                     (asset
                                      "PLTR"
                                      "Palantir Technologies Inc - Ordinary Shares - Class A")
                                     (asset
                                      "BABA"
                                      "Alibaba Group Holding Ltd - ADR")
                                     (asset
                                      "CONL"
                                      "GraniteShares ETF Trust - GraniteShares 2x Long COIN Daily ETF")])])])])])])]
                        [(weight-equal
                          [(filter
                            (rsi {:window 10})
                            (select-bottom 3)
                            [(asset
                              "V"
                              "Visa Inc - Ordinary Shares - Class A")
                             (asset "SOFI" "SoFi Technologies Inc")
                             (asset
                              "MA"
                              "Mastercard Incorporated - Ordinary Shares - Class A")
                             (asset "BX" "Blackstone Inc")
                             (asset "SCHW" "Charles Schwab Corp.")
                             (asset "KKR" "KKR & Co. Inc")
                             (asset
                              "BN"
                              "Brookfield Corporation - Ordinary Shares - Class A")
                             (asset "WELL" "Welltower Inc.")
                             (asset "VTR" "Ventas Inc")
                             (asset
                              "BAM"
                              "Brookfield Asset Management Ltd - Ordinary Shares - Class A")
                             (asset
                              "HOOD"
                              "Robinhood Markets Inc - Ordinary Shares - Class A")
                             (asset
                              "IBKR"
                              "Interactive Brokers Group Inc - Ordinary Shares - Class A")])])])])]
                    [(weight-equal
                      [(if
                        (<
                         (current-price "FAS")
                         (moving-average-price "FAS" {:window 100}))
                        [(weight-equal
                          [(if
                            (> (rsi "FAS" {:window 10}) 31)
                            [(weight-equal
                              [(filter
                                (moving-average-return {:window 15})
                                (select-top 1)
                                [(asset
                                  "TMF"
                                  "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                 (asset
                                  "FAZ"
                                  "Direxion Shares ETF Trust - Direxion Daily Financial Bear 3x Shares")
                                 (weight-equal
                                  [(filter
                                    (moving-average-return
                                     {:window 15})
                                    (select-top 1)
                                    [(asset
                                      "AAPX"
                                      "ETF Opportunities Trust - T-Rex 2X Long Apple Daily Target ETF")
                                     (asset
                                      "NVDL"
                                      "GraniteShares ETF Trust - GraniteShares 2x Long NVDA Daily ETF")
                                     (asset
                                      "BITX"
                                      "Volatility Shares Trust - 2x Bitcoin Strategy ETF")
                                     (asset
                                      "TSLR"
                                      "GraniteShares ETF Trust - GraniteShares 2x Long TSLA Daily ETF")
                                     (asset
                                      "FBL"
                                      "GraniteShares ETF Trust - GraniteShares 2x Long META Daily ETF")
                                     (asset
                                      "GGLL"
                                      "Direxion Shares ETF Trust - Direxion Daily GOOGL Bull 2X Shares")
                                     (asset
                                      "AMZZ"
                                      "GraniteShares ETF Trust - GraniteShares 2x Long AMZN Daily ETF")
                                     (asset
                                      "RGTI"
                                      "Rigetti Computing Inc")
                                     (asset
                                      "PLTR"
                                      "Palantir Technologies Inc - Ordinary Shares - Class A")
                                     (asset
                                      "BABA"
                                      "Alibaba Group Holding Ltd - ADR")
                                     (asset
                                      "CONL"
                                      "GraniteShares ETF Trust - GraniteShares 2x Long COIN Daily ETF")])])])])]
                            [(weight-equal
                              [(filter
                                (rsi {:window 10})
                                (select-top 1)
                                [(asset
                                  "AGQ"
                                  "ProShares Trust - ProShares Ultra Silver 2x Shares")
                                 (asset
                                  "FAS"
                                  "Direxion Shares ETF Trust - Direxion Daily Financial Bull 3x Shares")])])])])]
                        [(asset
                          "FAS"
                          "Direxion Shares ETF Trust - Direxion Daily Financial Bull 3x Shares")])])])])])])])])])])])]))
