(defsymphony
 "Growth Blend v2.2 RL"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
    (<
     (moving-average-return "QQQ" {:window 20})
     (moving-average-return "TMF" {:window 20}))
    [(group
      "Blend Growth Amoeba"
      [(weight-equal
        [(weight-equal
          [(group
            "TQQQ FTLT w/Sideways Market Mods"
            [(weight-equal
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
                                  [(weight-equal
                                    [(filter
                                      (cumulative-return {:window 30})
                                      (select-top 3)
                                      [(asset
                                        "TQQQ"
                                        "ProShares UltraPro QQQ")
                                       (asset
                                        "SPXL"
                                        "Direxion Daily S&P 500 Bull 3x Shares")
                                       (asset
                                        "SOXL"
                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                       (asset
                                        "FNGU"
                                        "MicroSectors FANG+ Index 3X Leveraged ETN")
                                       (asset
                                        "TECL"
                                        "Direxion Daily Technology Bull 3x Shares")])])]
                                  [(weight-equal
                                    [(filter
                                      (rsi {:window 10})
                                      (select-top 1)
                                      [(asset
                                        "UVXY"
                                        "ProShares Ultra VIX Short-Term Futures ETF")
                                       (asset
                                        "SQQQ"
                                        "ProShares UltraPro Short QQQ")
                                       (asset
                                        "FNGD"
                                        "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")])])])])]
                              [(weight-equal
                                [(filter
                                  (cumulative-return {:window 30})
                                  (select-top 3)
                                  [(asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")
                                   (asset
                                    "SPXL"
                                    "Direxion Daily S&P 500 Bull 3x Shares")
                                   (asset
                                    "SOXL"
                                    "Direxion Daily Semiconductor Bull 3x Shares")
                                   (asset
                                    "FNGU"
                                    "MicroSectors FANG+ Index 3X Leveraged ETN")
                                   (asset
                                    "TECL"
                                    "Direxion Daily Technology Bull 3x Shares")])])])])])])])])]
                  [(weight-equal
                    [(if
                      (< (rsi "TQQQ" {:window 10}) 31)
                      [(asset
                        "TECL"
                        "Direxion Daily Technology Bull 3x Shares")]
                      [(weight-equal
                        [(if
                          (< (rsi "SMH" {:window 10}) 30)
                          [(weight-equal
                            [(filter
                              (cumulative-return {:window 30})
                              (select-top 3)
                              [(asset "TQQQ" "ProShares UltraPro QQQ")
                               (asset
                                "SPXL"
                                "Direxion Daily S&P 500 Bull 3x Shares")
                               (asset
                                "SOXL"
                                "Direxion Daily Semiconductor Bull 3x Shares")
                               (asset
                                "FNGU"
                                "MicroSectors FANG+ Index 3X Leveraged ETN")
                               (asset
                                "TECL"
                                "Direxion Daily Technology Bull 3x Shares")])])]
                          [(weight-equal
                            [(if
                              (< (rsi "DIA" {:window 10}) 27)
                              [(weight-equal
                                [(filter
                                  (cumulative-return {:window 30})
                                  (select-top 3)
                                  [(asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")
                                   (asset
                                    "SPXL"
                                    "Direxion Daily S&P 500 Bull 3x Shares")
                                   (asset
                                    "SOXL"
                                    "Direxion Daily Semiconductor Bull 3x Shares")
                                   (asset
                                    "FNGU"
                                    "MicroSectors FANG+ Index 3X Leveraged ETN")
                                   (asset
                                    "TECL"
                                    "Direxion Daily Technology Bull 3x Shares")])])]
                              [(weight-equal
                                [(if
                                  (< (rsi "SPY" {:window 14}) 28)
                                  [(weight-equal
                                    [(filter
                                      (cumulative-return {:window 30})
                                      (select-top 3)
                                      [(asset
                                        "TQQQ"
                                        "ProShares UltraPro QQQ")
                                       (asset
                                        "SPXL"
                                        "Direxion Daily S&P 500 Bull 3x Shares")
                                       (asset
                                        "SOXL"
                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                       (asset
                                        "FNGU"
                                        "MicroSectors FANG+ Index 3X Leveraged ETN")
                                       (asset
                                        "TECL"
                                        "Direxion Daily Technology Bull 3x Shares")])])]
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
                                                        {:window 10}))
                                                      [(weight-equal
                                                        [(filter
                                                          (cumulative-return
                                                           {:window
                                                            30})
                                                          (select-top
                                                           3)
                                                          [(asset
                                                            "TQQQ"
                                                            "ProShares UltraPro QQQ")
                                                           (asset
                                                            "SPXL"
                                                            "Direxion Daily S&P 500 Bull 3x Shares")
                                                           (asset
                                                            "SOXL"
                                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                                           (asset
                                                            "FNGU"
                                                            "MicroSectors FANG+ Index 3X Leveraged ETN")
                                                           (asset
                                                            "TECL"
                                                            "Direxion Daily Technology Bull 3x Shares")])])]
                                                      [(asset
                                                        "SQQQ"
                                                        "ProShares UltraPro Short QQQ")
                                                       (asset
                                                        "FNGD"
                                                        "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")])])])])]
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
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "TLT"
                                                  {:window 10})
                                                 (rsi
                                                  "SQQQ"
                                                  {:window 10}))
                                                [(weight-equal
                                                  [(filter
                                                    (cumulative-return
                                                     {:window 30})
                                                    (select-top 3)
                                                    [(asset
                                                      "TQQQ"
                                                      "ProShares UltraPro QQQ")
                                                     (asset
                                                      "SPXL"
                                                      "Direxion Daily S&P 500 Bull 3x Shares")
                                                     (asset
                                                      "SOXL"
                                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                                     (asset
                                                      "FNGU"
                                                      "MicroSectors FANG+ Index 3X Leveraged ETN")
                                                     (asset
                                                      "TECL"
                                                      "Direxion Daily Technology Bull 3x Shares")])])]
                                                [(asset
                                                  "SQQQ"
                                                  "ProShares UltraPro Short QQQ")
                                                 (asset
                                                  "FNGD"
                                                  "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")])])])]
                                          [(weight-equal
                                            [(if
                                              (<
                                               (rsi
                                                "SQQQ"
                                                {:window 10})
                                               31)
                                              [(asset
                                                "SQQQ"
                                                "ProShares UltraPro Short QQQ")
                                               (asset
                                                "FNGD"
                                                "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")]
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
                                                      (cumulative-return
                                                       {:window 30})
                                                      (select-top 3)
                                                      [(asset
                                                        "TQQQ"
                                                        "ProShares UltraPro QQQ")
                                                       (asset
                                                        "SPXL"
                                                        "Direxion Daily S&P 500 Bull 3x Shares")
                                                       (asset
                                                        "SOXL"
                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                       (asset
                                                        "FNGU"
                                                        "MicroSectors FANG+ Index 3X Leveraged ETN")
                                                       (asset
                                                        "TECL"
                                                        "Direxion Daily Technology Bull 3x Shares")])])])])])])])])])
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
                                               (rsi
                                                "SQQQ"
                                                {:window 10}))
                                              [(weight-equal
                                                [(filter
                                                  (cumulative-return
                                                   {:window 30})
                                                  (select-top 3)
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")
                                                   (asset
                                                    "SPXL"
                                                    "Direxion Daily S&P 500 Bull 3x Shares")
                                                   (asset
                                                    "SOXL"
                                                    "Direxion Daily Semiconductor Bull 3x Shares")
                                                   (asset
                                                    "FNGU"
                                                    "MicroSectors FANG+ Index 3X Leveraged ETN")
                                                   (asset
                                                    "TECL"
                                                    "Direxion Daily Technology Bull 3x Shares")])])]
                                              [(asset
                                                "SQQQ"
                                                "ProShares UltraPro Short QQQ")
                                               (asset
                                                "FNGD"
                                                "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")])])])])]
                                      [(weight-equal
                                        [(if
                                          (<
                                           (rsi "SQQQ" {:window 10})
                                           31)
                                          [(asset
                                            "SQQQ"
                                            "ProShares UltraPro Short QQQ")
                                           (asset
                                            "FNGD"
                                            "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")]
                                          [(weight-equal
                                            [(if
                                              (<
                                               (cumulative-return
                                                "QQQ"
                                                {:window 70})
                                               -15)
                                              [(weight-equal
                                                [(filter
                                                  (cumulative-return
                                                   {:window 30})
                                                  (select-top 3)
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")
                                                   (asset
                                                    "SPXL"
                                                    "Direxion Daily S&P 500 Bull 3x Shares")
                                                   (asset
                                                    "SOXL"
                                                    "Direxion Daily Semiconductor Bull 3x Shares")
                                                   (asset
                                                    "FNGU"
                                                    "MicroSectors FANG+ Index 3X Leveraged ETN")
                                                   (asset
                                                    "TECL"
                                                    "Direxion Daily Technology Bull 3x Shares")])])]
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
                                                    "Consumer Staples Select Sector SPDR Fund")])])])])])])])])])])])])])])])])])])])])
           (group
            "Proposal for V3.0.4.1b | ?? Beta Baller + TCCC ? | Deez, BrianE, HinnomTX, DereckN, Garen, DJKeyhole ????, comrade, WaywardSon, zyzz | 2012 Backtestable | Belcampo69 updated some of the modules > AR & < DD"
            [(weight-equal
              [(group
                ".V3.0.4 5/7 2012 | ?? Beta Baller + TCCC ?"
                [(weight-equal
                  [(if
                    (< (rsi "BIL" {:window 5}) (rsi "IEF" {:window 7}))
                    [(weight-equal
                      [(if
                        (> (rsi "SPY" {:window 6}) 75)
                        [(group
                          "Overbought S&P. Sell the rip. Buy volatility."
                          [(weight-equal
                            [(filter
                              (rsi {:window 13})
                              (select-bottom 1)
                              [(asset
                                "UVXY"
                                "ProShares Ultra VIX Short-Term Futures ETF")
                               (asset
                                "VIXY"
                                "ProShares VIX Short-Term Futures ETF")])])])]
                        [(weight-equal
                          [(if
                            (<= (rsi "SOXL" {:window 5}) 75)
                            [(asset
                              "SOXL"
                              "Direxion Daily Semiconductor Bull 3x Shares")]
                            [(asset
                              "SOXS"
                              "Direxion Daily Semiconductor Bear 3x Shares")])])])])]
                    [(weight-equal
                      [(if
                        (< (rsi "SPY" {:window 6}) 27)
                        [(group
                          "Extremely oversold S&P (low RSI). Double check with bond mkt before going long"
                          [(weight-equal
                            [(if
                              (<
                               (rsi "BSV" {:window 7})
                               (rsi "SPHB" {:window 7}))
                              [(weight-equal
                                [(filter
                                  (rsi {:window 7})
                                  (select-bottom 1)
                                  [(asset
                                    "SOXS"
                                    "Direxion Daily Semiconductor Bear 3x Shares")
                                   (asset
                                    "SQQQ"
                                    "ProShares UltraPro Short QQQ")])])]
                              [(weight-equal
                                [(filter
                                  (rsi {:window 7})
                                  (select-bottom 1)
                                  [(asset
                                    "SOXL"
                                    "Direxion Daily Semiconductor Bull 3x Shares")
                                   (asset
                                    "TECL"
                                    "Direxion Daily Technology Bull 3x Shares")])])])])])]
                        [(group
                          "V0.2.1 | TCCC Stop the Bleed ? | DJKeyhole ???? | 1/2 of Momentum Mean Reversion"
                          [(weight-equal
                            [(if
                              (< (rsi "SPY" {:window 10}) 30)
                              [(group
                                "V1.2 | Five and Below | DJKeyhole | No Low Volume LETFs"
                                [(weight-equal
                                  [(filter
                                    (moving-average-return {:window 5})
                                    (select-bottom 1)
                                    [(asset
                                      "TECL"
                                      "Direxion Daily Technology Bull 3x Shares")
                                     (asset
                                      "TQQQ"
                                      "ProShares UltraPro QQQ")
                                     (asset
                                      "SPXL"
                                      "Direxion Daily S&P 500 Bull 3x Shares")
                                     (asset
                                      "SOXL"
                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                     (asset
                                      "UPRO"
                                      "ProShares UltraPro S&P500")
                                     (asset
                                      "QLD"
                                      "ProShares Ultra QQQ")])])])]
                              [(weight-equal
                                [(if
                                  (> (rsi "UVXY" {:window 10}) 74)
                                  [(weight-equal
                                    [(if
                                      (> (rsi "UVXY" {:window 10}) 84)
                                      [(group
                                        "Bear Stock Market - High Inflation - [STRIPPED] V2.0.2b | A Better LETF Basket | DJKeyhole ???? | BIL and TMV"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (current-price "TLT")
                                             (moving-average-price
                                              "TLT"
                                              {:window 200}))
                                            [(group
                                              "A.B: Medium term TLT may be overbought*"
                                              [(weight-equal
                                                [(if
                                                  (<
                                                   (moving-average-return
                                                    "TLT"
                                                    {:window 20})
                                                   0)
                                                  [(group
                                                    "A.B.B.A: Risk Off, Rising Rates (TMV)*"
                                                    [(weight-equal
                                                      [(if
                                                        (<=
                                                         (exponential-moving-average-price
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-price
                                                          "SPY"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               10})
                                                             30)
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "TECL"
                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                 (asset
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>=
                                                                 (cumulative-return
                                                                  "SPXU"
                                                                  {:window
                                                                   6})
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   3}))
                                                                [(weight-equal
                                                                  [(filter
                                                                    (cumulative-return
                                                                     {:window
                                                                      5})
                                                                    (select-top
                                                                     1)
                                                                    [(asset
                                                                      "SQQQ"
                                                                      "ProShares UltraPro Short QQQ")
                                                                     (asset
                                                                      "EUO"
                                                                      "ProShares UltraShort Euro")
                                                                     (asset
                                                                      "YCS"
                                                                      "ProShares UltraShort Yen")])])]
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      5})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "TECL"
                                                                      "Direxion Daily Technology Bull 3x Shares")
                                                                     (asset
                                                                      "TQQQ"
                                                                      "ProShares UltraPro QQQ")
                                                                     (asset
                                                                      "SOXL"
                                                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                                                     (asset
                                                                      "CURE"
                                                                      "Direxion Daily Healthcare Bull 3x Shares")])])])])])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               11})
                                                             77)
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "TECL"
                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                 (asset
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])]
                                                  [(group
                                                    "A.B.B.B: Risk Off, Falling Rates (TMF)*"
                                                    [(weight-equal
                                                      [(if
                                                        (<=
                                                         (exponential-moving-average-price
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-price
                                                          "SPY"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               10})
                                                             30)
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "TECL"
                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                 (asset
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                                            [(weight-equal
                                                              [(if
                                                                (<=
                                                                 (cumulative-return
                                                                  "SPY"
                                                                  {:window
                                                                   2})
                                                                 -2)
                                                                [(weight-equal
                                                                  [(filter
                                                                    (cumulative-return
                                                                     {:window
                                                                      5})
                                                                    (select-top
                                                                     1)
                                                                    [(asset
                                                                      "TECS"
                                                                      "Direxion Daily Technology Bear 3X Shares")
                                                                     (asset
                                                                      "SOXS"
                                                                      "Direxion Daily Semiconductor Bear 3x Shares")
                                                                     (asset
                                                                      "SQQQ"
                                                                      "ProShares UltraPro Short QQQ")])])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>=
                                                                     (cumulative-return
                                                                      "SPXU"
                                                                      {:window
                                                                       6})
                                                                     (cumulative-return
                                                                      "UPRO"
                                                                      {:window
                                                                       3}))
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (cumulative-return
                                                                         {:window
                                                                          5})
                                                                        (select-top
                                                                         1)
                                                                        [(asset
                                                                          "ERX"
                                                                          "Direxion Daily Energy Bull 2x Shares")
                                                                         (asset
                                                                          "EUO"
                                                                          "ProShares UltraShort Euro")
                                                                         (asset
                                                                          "YCS"
                                                                          "ProShares UltraShort Yen")])])]
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          5})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "SOXL"
                                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                                         (asset
                                                                          "EWZ"
                                                                          "iShares MSCI Brazil ETF")
                                                                         (asset
                                                                          "MVV"
                                                                          "ProShares Ultra MidCap400")
                                                                         (asset
                                                                          "USD"
                                                                          "ProShares Ultra Semiconductors")])])])])])])])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (moving-average-return
                                                              "SPY"
                                                              {:window
                                                               210})
                                                             (moving-average-return
                                                              "DBC"
                                                              {:window
                                                               360}))
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "TQQQ"
                                                                  {:window
                                                                   11})
                                                                 77)
                                                                [(asset
                                                                  "UVXY"
                                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (cumulative-return
                                                                      "TQQQ"
                                                                      {:window
                                                                       6})
                                                                     -10)
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (cumulative-return
                                                                          "TQQQ"
                                                                          {:window
                                                                           1})
                                                                         5.5)
                                                                        [(weight-equal
                                                                          [(asset
                                                                            "UVXY"
                                                                            "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (<
                                                                             (rsi
                                                                              "BIL"
                                                                              {:window
                                                                               7})
                                                                             (rsi
                                                                              "IEF"
                                                                              {:window
                                                                               7}))
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (moving-average-return
                                                                                 {:window
                                                                                  5})
                                                                                (select-bottom
                                                                                 1)
                                                                                [(asset
                                                                                  "SOXL"
                                                                                  "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (cumulative-return
                                                                                 {:window
                                                                                  5})
                                                                                (select-top
                                                                                 1)
                                                                                [(asset
                                                                                  "EWZ"
                                                                                  "iShares MSCI Brazil ETF")
                                                                                 (asset
                                                                                  "UUP"
                                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                                 (asset
                                                                                  "TMF"
                                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                                 (asset
                                                                                  "UCO"
                                                                                  "ProShares Ultra Bloomberg Crude Oil")])])])])])])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "BIL"
                                                                          {:window
                                                                           7})
                                                                         (rsi
                                                                          "IEF"
                                                                          {:window
                                                                           7}))
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              5})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "TECL"
                                                                              "Direxion Daily Technology Bull 3x Shares")
                                                                             (asset
                                                                              "TQQQ"
                                                                              "ProShares UltraPro QQQ")
                                                                             (asset
                                                                              "SPXL"
                                                                              "Direxion Daily S&P 500 Bull 3x Shares")
                                                                             (asset
                                                                              "QLD"
                                                                              "ProShares Ultra QQQ")
                                                                             (asset
                                                                              "USD"
                                                                              "ProShares Ultra Semiconductors")])])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (cumulative-return
                                                                             {:window
                                                                              5})
                                                                            (select-top
                                                                             1)
                                                                            [(asset
                                                                              "EWZ"
                                                                              "iShares MSCI Brazil ETF")
                                                                             (asset
                                                                              "UUP"
                                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                                             (asset
                                                                              "TMF"
                                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])]
                                                            [(group
                                                              "Defense | Modified"
                                                              [(weight-equal
                                                                [(if
                                                                  (>
                                                                   (stdev-return
                                                                    "DBC"
                                                                    {:window
                                                                     20})
                                                                   (stdev-return
                                                                    "SPY"
                                                                    {:window
                                                                     20}))
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (rsi
                                                                       {:window
                                                                        5})
                                                                      (select-bottom
                                                                       1)
                                                                      [(asset
                                                                        "SHY"
                                                                        "iShares 1-3 Year Treasury Bond ETF")
                                                                       (asset
                                                                        "EWZ"
                                                                        "iShares MSCI Brazil ETF")
                                                                       (asset
                                                                        "GLD"
                                                                        "SPDR Gold Shares")
                                                                       (asset
                                                                        "SPXS"
                                                                        "Direxion Daily S&P 500 Bear 3x Shares")
                                                                       (asset
                                                                        "TECS"
                                                                        "Direxion Daily Technology Bear 3X Shares")
                                                                       (asset
                                                                        "SOXS"
                                                                        "Direxion Daily Semiconductor Bear 3x Shares")
                                                                       (asset
                                                                        "UCO"
                                                                        "ProShares Ultra Bloomberg Crude Oil")
                                                                       (asset
                                                                        "YCS"
                                                                        "ProShares UltraShort Yen")])])]
                                                                  [(weight-equal
                                                                    [(if
                                                                      (<
                                                                       (rsi
                                                                        "BIL"
                                                                        {:window
                                                                         7})
                                                                       (rsi
                                                                        "IEF"
                                                                        {:window
                                                                         7}))
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (moving-average-return
                                                                           {:window
                                                                            5})
                                                                          (select-bottom
                                                                           1)
                                                                          [(asset
                                                                            "SOXL"
                                                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                                                           (asset
                                                                            "USD"
                                                                            "ProShares Ultra Semiconductors")
                                                                           (asset
                                                                            "TMF"
                                                                            "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (cumulative-return
                                                                           {:window
                                                                            5})
                                                                          (select-top
                                                                           1)
                                                                          [(asset
                                                                            "EWZ"
                                                                            "iShares MSCI Brazil ETF")
                                                                           (asset
                                                                            "SPXS"
                                                                            "Direxion Daily S&P 500 Bear 3x Shares")
                                                                           (asset
                                                                            "SOXS"
                                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                                           (asset
                                                                            "UCO"
                                                                            "ProShares Ultra Bloomberg Crude Oil")
                                                                           (asset
                                                                            "YCS"
                                                                            "ProShares UltraShort Yen")])])])])])])])])])])])])])])])]
                                            [(group
                                              "B: If long term TLT is trending down, safety: Long Term, 2 Least Volatile*"
                                              [(weight-equal
                                                [(if
                                                  (<
                                                   (moving-average-return
                                                    "TLT"
                                                    {:window 20})
                                                   0)
                                                  [(group
                                                    "B.A.A: Risk Off, Rising Rates (TMV)* - LETF Basket^"
                                                    [(weight-equal
                                                      [(if
                                                        (<=
                                                         (exponential-moving-average-price
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-price
                                                          "SPY"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               10})
                                                             30)
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  5})
                                                                (select-top
                                                                 1)
                                                                [(asset
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(weight-equal
                                                              [(if
                                                                (<=
                                                                 (cumulative-return
                                                                  "SPY"
                                                                  {:window
                                                                   1})
                                                                 -2)
                                                                [(weight-equal
                                                                  [(filter
                                                                    (cumulative-return
                                                                     {:window
                                                                      5})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "SPXS"
                                                                      "Direxion Daily S&P 500 Bear 3x Shares")
                                                                     (asset
                                                                      "TECS"
                                                                      "Direxion Daily Technology Bear 3X Shares")
                                                                     (asset
                                                                      "SOXS"
                                                                      "Direxion Daily Semiconductor Bear 3x Shares")
                                                                     (asset
                                                                      "SQQQ"
                                                                      "ProShares UltraPro Short QQQ")
                                                                     (asset
                                                                      "ERX"
                                                                      "Direxion Daily Energy Bull 2x Shares")])])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>=
                                                                     (cumulative-return
                                                                      "SPXU"
                                                                      {:window
                                                                       5})
                                                                     (cumulative-return
                                                                      "UPRO"
                                                                      {:window
                                                                       4}))
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (cumulative-return
                                                                         {:window
                                                                          5})
                                                                        (select-top
                                                                         1)
                                                                        [(asset
                                                                          "SOXS"
                                                                          "Direxion Daily Semiconductor Bear 3x Shares")
                                                                         (asset
                                                                          "SQQQ"
                                                                          "ProShares UltraPro Short QQQ")
                                                                         (asset
                                                                          "EPI"
                                                                          "WisdomTree India Earnings Fund")])])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>=
                                                                         (cumulative-return
                                                                          "BIL"
                                                                          {:window
                                                                           3})
                                                                         (cumulative-return
                                                                          "TMV"
                                                                          {:window
                                                                           3}))
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (cumulative-return
                                                                             {:window
                                                                              30})
                                                                            (select-top
                                                                             3)
                                                                            [(asset
                                                                              "TQQQ"
                                                                              "ProShares UltraPro QQQ")
                                                                             (asset
                                                                              "SPXL"
                                                                              "Direxion Daily S&P 500 Bull 3x Shares")
                                                                             (asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "FNGU"
                                                                              "MicroSectors FANG+ Index 3X Leveraged ETN")
                                                                             (asset
                                                                              "TECL"
                                                                              "Direxion Daily Technology Bull 3x Shares")])])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              5})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "TECL"
                                                                              "Direxion Daily Technology Bull 3x Shares")
                                                                             (asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "TMV"
                                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (moving-average-return
                                                              "SPY"
                                                              {:window
                                                               210})
                                                             (moving-average-return
                                                              "DBC"
                                                              {:window
                                                               360}))
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "TQQQ"
                                                                  {:window
                                                                   11})
                                                                 77)
                                                                [(asset
                                                                  "UVXY"
                                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (cumulative-return
                                                                      "TQQQ"
                                                                      {:window
                                                                       6})
                                                                     -10)
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (cumulative-return
                                                                          "TQQQ"
                                                                          {:window
                                                                           1})
                                                                         5.5)
                                                                        [(weight-equal
                                                                          [(asset
                                                                            "UVXY"
                                                                            "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              5})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "TMV"
                                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "BIL"
                                                                          {:window
                                                                           7})
                                                                         (rsi
                                                                          "IEF"
                                                                          {:window
                                                                           7}))
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              5})
                                                                            (select-top
                                                                             1)
                                                                            [(asset
                                                                              "TQQQ"
                                                                              "ProShares UltraPro QQQ")
                                                                             (asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "UPRO"
                                                                              "ProShares UltraPro S&P500")
                                                                             (asset
                                                                              "TMV"
                                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                             (asset
                                                                              "TECL"
                                                                              "Direxion Daily Technology Bull 3x Shares")])])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              22})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "UPRO"
                                                                              "ProShares UltraPro S&P500")])])])])])])])])]
                                                            [(group
                                                              "Defense | Modified"
                                                              [(weight-equal
                                                                [(if
                                                                  (>
                                                                   (stdev-return
                                                                    "DBC"
                                                                    {:window
                                                                     20})
                                                                   (stdev-return
                                                                    "SPY"
                                                                    {:window
                                                                     20}))
                                                                  [(weight-equal
                                                                    [(if
                                                                      (>=
                                                                       (stdev-return
                                                                        "DBC"
                                                                        {:window
                                                                         10})
                                                                       3)
                                                                      [(weight-equal
                                                                        [(if
                                                                          (<=
                                                                           (stdev-return
                                                                            "TMV"
                                                                            {:window
                                                                             5})
                                                                           (stdev-return
                                                                            "DBC"
                                                                            {:window
                                                                             5}))
                                                                          [(asset
                                                                            "TMV"
                                                                            "Direxion Daily 20+ Year Treasury Bear 3x Shares")]
                                                                          [(asset
                                                                            "DBC"
                                                                            "Invesco DB Commodity Index Tracking Fund")])])]
                                                                      [(weight-equal
                                                                        [(if
                                                                          (<
                                                                           (rsi
                                                                            "BIL"
                                                                            {:window
                                                                             7})
                                                                           (rsi
                                                                            "IEF"
                                                                            {:window
                                                                             7}))
                                                                          [(weight-equal
                                                                            [(filter
                                                                              (moving-average-return
                                                                               {:window
                                                                                5})
                                                                              (select-top
                                                                               1)
                                                                              [(asset
                                                                                "TMV"
                                                                                "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                               (asset
                                                                                "SOXS"
                                                                                "Direxion Daily Semiconductor Bear 3x Shares")
                                                                               (asset
                                                                                "SPXU"
                                                                                "ProShares UltraPro Short S&P500")])])]
                                                                          [(weight-equal
                                                                            [(filter
                                                                              (cumulative-return
                                                                               {:window
                                                                                5})
                                                                              (select-bottom
                                                                               1)
                                                                              [(asset
                                                                                "EFA"
                                                                                "iShares MSCI EAFE ETF")
                                                                               (asset
                                                                                "EEM"
                                                                                "iShares MSCI Emerging Markets ETF")
                                                                               (asset
                                                                                "SPXS"
                                                                                "Direxion Daily S&P 500 Bear 3x Shares")
                                                                               (asset
                                                                                "SOXS"
                                                                                "Direxion Daily Semiconductor Bear 3x Shares")
                                                                               (asset
                                                                                "UCO"
                                                                                "ProShares Ultra Bloomberg Crude Oil")
                                                                               (asset
                                                                                "TMV"
                                                                                "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])]
                                                                  [(weight-equal
                                                                    [(if
                                                                      (<
                                                                       (rsi
                                                                        "BIL"
                                                                        {:window
                                                                         7})
                                                                       (rsi
                                                                        "IEF"
                                                                        {:window
                                                                         7}))
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (moving-average-return
                                                                           {:window
                                                                            5})
                                                                          (select-bottom
                                                                           1)
                                                                          [(asset
                                                                            "EPI"
                                                                            "WisdomTree India Earnings Fund")
                                                                           (asset
                                                                            "SOXL"
                                                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                                                           (asset
                                                                            "UPRO"
                                                                            "ProShares UltraPro S&P500")])])]
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (cumulative-return
                                                                           {:window
                                                                            5})
                                                                          (select-top
                                                                           1)
                                                                          [(asset
                                                                            "EWZ"
                                                                            "iShares MSCI Brazil ETF")
                                                                           (asset
                                                                            "TECS"
                                                                            "Direxion Daily Technology Bear 3X Shares")
                                                                           (asset
                                                                            "SOXS"
                                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                                           (asset
                                                                            "EUO"
                                                                            "ProShares UltraShort Euro")
                                                                           (asset
                                                                            "YCS"
                                                                            "ProShares UltraShort Yen")
                                                                           (asset
                                                                            "TMV"
                                                                            "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])])])]
                                                  [(group
                                                    "B.A.B: Risk Off, Falling Rates (TMF)* - LETF Basket"
                                                    [(weight-equal
                                                      [(if
                                                        (<=
                                                         (exponential-moving-average-price
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-price
                                                          "SPY"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (<=
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               2})
                                                             -2)
                                                            [(weight-equal
                                                              [(filter
                                                                (cumulative-return
                                                                 {:window
                                                                  5})
                                                                (select-top
                                                                 1)
                                                                [(asset
                                                                  "SPXS"
                                                                  "Direxion Daily S&P 500 Bear 3x Shares")
                                                                 (asset
                                                                  "TECS"
                                                                  "Direxion Daily Technology Bear 3X Shares")
                                                                 (asset
                                                                  "SOXS"
                                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                                 (asset
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ")])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>=
                                                                 (cumulative-return
                                                                  "SPXU"
                                                                  {:window
                                                                   6})
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   3}))
                                                                [(weight-equal
                                                                  [(filter
                                                                    (cumulative-return
                                                                     {:window
                                                                      5})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "BIL"
                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                     (asset
                                                                      "AGG"
                                                                      "iShares Core U.S. Aggregate Bond ETF")
                                                                     (asset
                                                                      "TMF"
                                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      5})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "TECL"
                                                                      "Direxion Daily Technology Bull 3x Shares")
                                                                     (asset
                                                                      "TQQQ"
                                                                      "ProShares UltraPro QQQ")
                                                                     (asset
                                                                      "SOXL"
                                                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                                                     (asset
                                                                      "EWZ"
                                                                      "iShares MSCI Brazil ETF")
                                                                     (asset
                                                                      "TMF"
                                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (moving-average-return
                                                              "SPY"
                                                              {:window
                                                               210})
                                                             (moving-average-return
                                                              "DBC"
                                                              {:window
                                                               360}))
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (exponential-moving-average-price
                                                                  "SPY"
                                                                  {:window
                                                                   210})
                                                                 (exponential-moving-average-price
                                                                  "SPY"
                                                                  {:window
                                                                   360}))
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "TQQQ"
                                                                      {:window
                                                                       11})
                                                                     77)
                                                                    [(asset
                                                                      "UVXY"
                                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (cumulative-return
                                                                          "TQQQ"
                                                                          {:window
                                                                           6})
                                                                         -10)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (cumulative-return
                                                                              "TQQQ"
                                                                              {:window
                                                                               1})
                                                                             5.5)
                                                                            [(weight-equal
                                                                              [(asset
                                                                                "UVXY"
                                                                                "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (moving-average-return
                                                                                 {:window
                                                                                  7})
                                                                                (select-bottom
                                                                                 1)
                                                                                [(asset
                                                                                  "TECL"
                                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                                 (asset
                                                                                  "TQQQ"
                                                                                  "ProShares UltraPro QQQ")
                                                                                 (asset
                                                                                  "SPXL"
                                                                                  "Direxion Daily S&P 500 Bull 3x Shares")
                                                                                 (asset
                                                                                  "EPI"
                                                                                  "WisdomTree India Earnings Fund")
                                                                                 (asset
                                                                                  "SOXL"
                                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                 (asset
                                                                                  "UPRO"
                                                                                  "ProShares UltraPro S&P500")
                                                                                 (asset
                                                                                  "QLD"
                                                                                  "ProShares Ultra QQQ")
                                                                                 (asset
                                                                                  "EWZ"
                                                                                  "iShares MSCI Brazil ETF")
                                                                                 (asset
                                                                                  "MVV"
                                                                                  "ProShares Ultra MidCap400")
                                                                                 (asset
                                                                                  "PUI"
                                                                                  "Invesco DWA Utilities Momentum ETF")
                                                                                 (asset
                                                                                  "USD"
                                                                                  "ProShares Ultra Semiconductors")
                                                                                 (asset
                                                                                  "TMF"
                                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (<
                                                                             (rsi
                                                                              "BIL"
                                                                              {:window
                                                                               7})
                                                                             (rsi
                                                                              "IEF"
                                                                              {:window
                                                                               7}))
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (moving-average-return
                                                                                 {:window
                                                                                  7})
                                                                                (select-bottom
                                                                                 1)
                                                                                [(asset
                                                                                  "TECL"
                                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                                 (asset
                                                                                  "SPXL"
                                                                                  "Direxion Daily S&P 500 Bull 3x Shares")
                                                                                 (asset
                                                                                  "EPI"
                                                                                  "WisdomTree India Earnings Fund")
                                                                                 (asset
                                                                                  "SOXL"
                                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                 (asset
                                                                                  "UPRO"
                                                                                  "ProShares UltraPro S&P500")
                                                                                 (asset
                                                                                  "MVV"
                                                                                  "ProShares Ultra MidCap400")])])]
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (cumulative-return
                                                                                 {:window
                                                                                  5})
                                                                                (select-top
                                                                                 1)
                                                                                [(asset
                                                                                  "SOXS"
                                                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                 (asset
                                                                                  "TMF"
                                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])]
                                                                [(weight-equal
                                                                  [(filter
                                                                    (rsi
                                                                     {:window
                                                                      5})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "SPXS"
                                                                      "Direxion Daily S&P 500 Bear 3x Shares")
                                                                     (asset
                                                                      "SQQQ"
                                                                      "ProShares UltraPro Short QQQ")
                                                                     (asset
                                                                      "TECS"
                                                                      "Direxion Daily Technology Bear 3X Shares")
                                                                     (asset
                                                                      "SOXS"
                                                                      "Direxion Daily Semiconductor Bear 3x Shares")])])])])]
                                                            [(group
                                                              "Defense | Modified"
                                                              [(weight-equal
                                                                [(if
                                                                  (>
                                                                   (stdev-return
                                                                    "DBC"
                                                                    {:window
                                                                     20})
                                                                   (stdev-return
                                                                    "SPY"
                                                                    {:window
                                                                     20}))
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (rsi
                                                                       {:window
                                                                        5})
                                                                      (select-bottom
                                                                       1)
                                                                      [(asset
                                                                        "SPXS"
                                                                        "Direxion Daily S&P 500 Bear 3x Shares")
                                                                       (asset
                                                                        "EPI"
                                                                        "WisdomTree India Earnings Fund")
                                                                       (asset
                                                                        "TECS"
                                                                        "Direxion Daily Technology Bear 3X Shares")
                                                                       (asset
                                                                        "SOXS"
                                                                        "Direxion Daily Semiconductor Bear 3x Shares")
                                                                       (asset
                                                                        "SQQQ"
                                                                        "ProShares UltraPro Short QQQ")])])]
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (moving-average-return
                                                                       {:window
                                                                        5})
                                                                      (select-top
                                                                       1)
                                                                      [(asset
                                                                        "TECL"
                                                                        "Direxion Daily Technology Bull 3x Shares")
                                                                       (asset
                                                                        "TQQQ"
                                                                        "ProShares UltraPro QQQ")
                                                                       (asset
                                                                        "SOXL"
                                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                                       (asset
                                                                        "TMF"
                                                                        "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])])])])])])])])])]
                                      [(asset
                                        "UVXY"
                                        "ProShares Ultra VIX Short-Term Futures ETF")])])]
                                  [(group
                                    "Bear Stock Market - High Inflation - [STRIPPED] V2.0.2b | A Better LETF Basket | DJKeyhole ???? | BIL and TMV"
                                    [(weight-equal
                                      [(if
                                        (>
                                         (current-price "TLT")
                                         (moving-average-price
                                          "TLT"
                                          {:window 200}))
                                        [(group
                                          "A.B: Medium term TLT may be overbought*"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (moving-average-return
                                                "TLT"
                                                {:window 20})
                                               0)
                                              [(group
                                                "A.B.B.A: Risk Off, Rising Rates (TMV)*"
                                                [(weight-equal
                                                  [(if
                                                    (<=
                                                     (exponential-moving-average-price
                                                      "SPY"
                                                      {:window 210})
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 360}))
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "TQQQ"
                                                          {:window 10})
                                                         30)
                                                        [(weight-equal
                                                          [(filter
                                                            (cumulative-return
                                                             {:window
                                                              30})
                                                            (select-top
                                                             3)
                                                            [(asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")
                                                             (asset
                                                              "SPXL"
                                                              "Direxion Daily S&P 500 Bull 3x Shares")
                                                             (asset
                                                              "SOXL"
                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                             (asset
                                                              "FNGU"
                                                              "MicroSectors FANG+ Index 3X Leveraged ETN")
                                                             (asset
                                                              "TECL"
                                                              "Direxion Daily Technology Bull 3x Shares")])])]
                                                        [(weight-equal
                                                          [(if
                                                            (<=
                                                             (cumulative-return
                                                              "SPXU"
                                                              {:window
                                                               6})
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               3}))
                                                            [(weight-equal
                                                              [(filter
                                                                (cumulative-return
                                                                 {:window
                                                                  5})
                                                                (select-top
                                                                 1)
                                                                [(asset
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ")
                                                                 (asset
                                                                  "EUO"
                                                                  "ProShares UltraShort Euro")
                                                                 (asset
                                                                  "YCS"
                                                                  "ProShares UltraShort Yen")])])]
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "TECL"
                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                 (asset
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "CURE"
                                                                  "Direxion Daily Healthcare Bull 3x Shares")])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "TQQQ"
                                                          {:window 11})
                                                         77)
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              5})
                                                            (select-bottom
                                                             1)
                                                            [(asset
                                                              "TECL"
                                                              "Direxion Daily Technology Bull 3x Shares")
                                                             (asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")
                                                             (asset
                                                              "SOXL"
                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                             (asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])]
                                              [(group
                                                "A.B.B.B: Risk Off, Falling Rates (TMF)*"
                                                [(weight-equal
                                                  [(if
                                                    (<=
                                                     (exponential-moving-average-price
                                                      "SPY"
                                                      {:window 210})
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 360}))
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "TQQQ"
                                                          {:window 10})
                                                         30)
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              5})
                                                            (select-bottom
                                                             1)
                                                            [(asset
                                                              "TECL"
                                                              "Direxion Daily Technology Bull 3x Shares")
                                                             (asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")
                                                             (asset
                                                              "SOXL"
                                                              "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>=
                                                             (cumulative-return
                                                              "UUP"
                                                              {:window
                                                               2})
                                                             1)
                                                            [(weight-equal
                                                              [(filter
                                                                (cumulative-return
                                                                 {:window
                                                                  5})
                                                                (select-top
                                                                 1)
                                                                [(asset
                                                                  "TECS"
                                                                  "Direxion Daily Technology Bear 3X Shares")
                                                                 (asset
                                                                  "SOXS"
                                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                                 (asset
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ")])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>=
                                                                 (moving-average-price
                                                                  "SPY"
                                                                  {:window
                                                                   1})
                                                                 -1)
                                                                [(weight-equal
                                                                  [(filter
                                                                    (cumulative-return
                                                                     {:window
                                                                      5})
                                                                    (select-top
                                                                     1)
                                                                    [(asset
                                                                      "ERX"
                                                                      "Direxion Daily Energy Bull 2x Shares")
                                                                     (asset
                                                                      "EUO"
                                                                      "ProShares UltraShort Euro")
                                                                     (asset
                                                                      "YCS"
                                                                      "ProShares UltraShort Yen")])])]
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      5})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "SOXL"
                                                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                                                     (asset
                                                                      "EWZ"
                                                                      "iShares MSCI Brazil ETF")
                                                                     (asset
                                                                      "MVV"
                                                                      "ProShares Ultra MidCap400")
                                                                     (asset
                                                                      "USD"
                                                                      "ProShares Ultra Semiconductors")])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (moving-average-return
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-return
                                                          "DBC"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               11})
                                                             77)
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (cumulative-return
                                                                  "TQQQ"
                                                                  {:window
                                                                   6})
                                                                 -10)
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (cumulative-return
                                                                      "TQQQ"
                                                                      {:window
                                                                       1})
                                                                     5.5)
                                                                    [(weight-equal
                                                                      [(asset
                                                                        "UVXY"
                                                                        "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "BIL"
                                                                          {:window
                                                                           7})
                                                                         (rsi
                                                                          "IEF"
                                                                          {:window
                                                                           7}))
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              5})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (cumulative-return
                                                                             {:window
                                                                              5})
                                                                            (select-top
                                                                             1)
                                                                            [(asset
                                                                              "EWZ"
                                                                              "iShares MSCI Brazil ETF")
                                                                             (asset
                                                                              "UUP"
                                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                                             (asset
                                                                              "TMF"
                                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                             (asset
                                                                              "UCO"
                                                                              "ProShares Ultra Bloomberg Crude Oil")])])])])])])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (rsi
                                                                      "BIL"
                                                                      {:window
                                                                       7})
                                                                     (rsi
                                                                      "IEF"
                                                                      {:window
                                                                       7}))
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          5})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "TECL"
                                                                          "Direxion Daily Technology Bull 3x Shares")
                                                                         (asset
                                                                          "TQQQ"
                                                                          "ProShares UltraPro QQQ")
                                                                         (asset
                                                                          "SPXL"
                                                                          "Direxion Daily S&P 500 Bull 3x Shares")
                                                                         (asset
                                                                          "QLD"
                                                                          "ProShares Ultra QQQ")
                                                                         (asset
                                                                          "USD"
                                                                          "ProShares Ultra Semiconductors")])])]
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (cumulative-return
                                                                         {:window
                                                                          5})
                                                                        (select-top
                                                                         1)
                                                                        [(asset
                                                                          "EWZ"
                                                                          "iShares MSCI Brazil ETF")
                                                                         (asset
                                                                          "UUP"
                                                                          "Invesco DB US Dollar Index Bullish Fund")
                                                                         (asset
                                                                          "TMF"
                                                                          "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])]
                                                        [(group
                                                          "Defense | Modified"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (stdev-return
                                                                "DBC"
                                                                {:window
                                                                 20})
                                                               (stdev-return
                                                                "SPY"
                                                                {:window
                                                                 20}))
                                                              [(weight-equal
                                                                [(filter
                                                                  (rsi
                                                                   {:window
                                                                    5})
                                                                  (select-bottom
                                                                   1)
                                                                  [(asset
                                                                    "SHY"
                                                                    "iShares 1-3 Year Treasury Bond ETF")
                                                                   (asset
                                                                    "EWZ"
                                                                    "iShares MSCI Brazil ETF")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "SPXS"
                                                                    "Direxion Daily S&P 500 Bear 3x Shares")
                                                                   (asset
                                                                    "TECS"
                                                                    "Direxion Daily Technology Bear 3X Shares")
                                                                   (asset
                                                                    "SOXS"
                                                                    "Direxion Daily Semiconductor Bear 3x Shares")
                                                                   (asset
                                                                    "UCO"
                                                                    "ProShares Ultra Bloomberg Crude Oil")
                                                                   (asset
                                                                    "YCS"
                                                                    "ProShares UltraShort Yen")])])]
                                                              [(weight-equal
                                                                [(if
                                                                  (<
                                                                   (rsi
                                                                    "BIL"
                                                                    {:window
                                                                     7})
                                                                   (rsi
                                                                    "IEF"
                                                                    {:window
                                                                     7}))
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (moving-average-return
                                                                       {:window
                                                                        5})
                                                                      (select-bottom
                                                                       1)
                                                                      [(asset
                                                                        "SOXL"
                                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                                       (asset
                                                                        "USD"
                                                                        "ProShares Ultra Semiconductors")
                                                                       (asset
                                                                        "TMF"
                                                                        "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (cumulative-return
                                                                       {:window
                                                                        5})
                                                                      (select-top
                                                                       1)
                                                                      [(asset
                                                                        "EWZ"
                                                                        "iShares MSCI Brazil ETF")
                                                                       (asset
                                                                        "SPXS"
                                                                        "Direxion Daily S&P 500 Bear 3x Shares")
                                                                       (asset
                                                                        "SOXS"
                                                                        "Direxion Daily Semiconductor Bear 3x Shares")
                                                                       (asset
                                                                        "UCO"
                                                                        "ProShares Ultra Bloomberg Crude Oil")
                                                                       (asset
                                                                        "YCS"
                                                                        "ProShares UltraShort Yen")])])])])])])])])])])])])])])])]
                                        [(group
                                          "B: If long term TLT is trending down, safety: Long Term, 2 Least Volatile*"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (moving-average-return
                                                "TLT"
                                                {:window 20})
                                               0)
                                              [(group
                                                "B.A.A: Risk Off, Rising Rates (TMV)* - LETF Basket^"
                                                [(weight-equal
                                                  [(if
                                                    (<=
                                                     (exponential-moving-average-price
                                                      "SPY"
                                                      {:window 210})
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 360}))
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "TQQQ"
                                                          {:window 10})
                                                         30)
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              5})
                                                            (select-top
                                                             1)
                                                            [(asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")
                                                             (asset
                                                              "SOXL"
                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                             (asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>=
                                                             (cumulative-return
                                                              "UUP"
                                                              {:window
                                                               2})
                                                             1)
                                                            [(weight-equal
                                                              [(filter
                                                                (cumulative-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "SPXS"
                                                                  "Direxion Daily S&P 500 Bear 3x Shares")
                                                                 (asset
                                                                  "TECS"
                                                                  "Direxion Daily Technology Bear 3X Shares")
                                                                 (asset
                                                                  "SOXS"
                                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                                 (asset
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ")
                                                                 (asset
                                                                  "ERX"
                                                                  "Direxion Daily Energy Bull 2x Shares")])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>=
                                                                 (cumulative-return
                                                                  "SPXU"
                                                                  {:window
                                                                   5})
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   4}))
                                                                [(weight-equal
                                                                  [(filter
                                                                    (cumulative-return
                                                                     {:window
                                                                      5})
                                                                    (select-top
                                                                     1)
                                                                    [(asset
                                                                      "SOXS"
                                                                      "Direxion Daily Semiconductor Bear 3x Shares")
                                                                     (asset
                                                                      "SQQQ"
                                                                      "ProShares UltraPro Short QQQ")
                                                                     (asset
                                                                      "EPI"
                                                                      "WisdomTree India Earnings Fund")])])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>=
                                                                     (cumulative-return
                                                                      "BIL"
                                                                      {:window
                                                                       3})
                                                                     (cumulative-return
                                                                      "TMV"
                                                                      {:window
                                                                       3}))
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          5})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "TECL"
                                                                          "Direxion Daily Technology Bull 3x Shares")
                                                                         (asset
                                                                          "SOXL"
                                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                                         (asset
                                                                          "TNA"
                                                                          "Direxion Daily Small Cap Bull 3x Shares")])])]
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
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
                                                                          "TMV"
                                                                          "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                         (asset
                                                                          "TQQQ"
                                                                          "ProShares UltraPro QQQ")])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (moving-average-return
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-return
                                                          "DBC"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               11})
                                                             77)
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (cumulative-return
                                                                  "TQQQ"
                                                                  {:window
                                                                   6})
                                                                 -10)
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (cumulative-return
                                                                      "TQQQ"
                                                                      {:window
                                                                       1})
                                                                     5.5)
                                                                    [(weight-equal
                                                                      [(asset
                                                                        "UVXY"
                                                                        "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          5})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "SOXL"
                                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                                         (asset
                                                                          "TMV"
                                                                          "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (rsi
                                                                      "BIL"
                                                                      {:window
                                                                       7})
                                                                     (rsi
                                                                      "IEF"
                                                                      {:window
                                                                       7}))
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          5})
                                                                        (select-top
                                                                         1)
                                                                        [(asset
                                                                          "TQQQ"
                                                                          "ProShares UltraPro QQQ")
                                                                         (asset
                                                                          "SOXL"
                                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                                         (asset
                                                                          "UPRO"
                                                                          "ProShares UltraPro S&P500")
                                                                         (asset
                                                                          "TMV"
                                                                          "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                         (asset
                                                                          "TECL"
                                                                          "Direxion Daily Technology Bull 3x Shares")])])]
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          22})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "SOXL"
                                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                                         (asset
                                                                          "UPRO"
                                                                          "ProShares UltraPro S&P500")])])])])])])])])]
                                                        [(group
                                                          "Defense | Modified"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (stdev-return
                                                                "DBC"
                                                                {:window
                                                                 20})
                                                               (stdev-return
                                                                "SPY"
                                                                {:window
                                                                 20}))
                                                              [(weight-equal
                                                                [(if
                                                                  (>=
                                                                   (stdev-return
                                                                    "DBC"
                                                                    {:window
                                                                     10})
                                                                   3)
                                                                  [(weight-equal
                                                                    [(if
                                                                      (<=
                                                                       (stdev-return
                                                                        "TMV"
                                                                        {:window
                                                                         5})
                                                                       (stdev-return
                                                                        "DBC"
                                                                        {:window
                                                                         5}))
                                                                      [(asset
                                                                        "TMV"
                                                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")]
                                                                      [(asset
                                                                        "DBC"
                                                                        "Invesco DB Commodity Index Tracking Fund")])])]
                                                                  [(weight-equal
                                                                    [(if
                                                                      (<
                                                                       (rsi
                                                                        "BIL"
                                                                        {:window
                                                                         7})
                                                                       (rsi
                                                                        "IEF"
                                                                        {:window
                                                                         7}))
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (moving-average-return
                                                                           {:window
                                                                            5})
                                                                          (select-top
                                                                           1)
                                                                          [(asset
                                                                            "TMV"
                                                                            "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                           (asset
                                                                            "SOXS"
                                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                                           (asset
                                                                            "SPXU"
                                                                            "ProShares UltraPro Short S&P500")])])]
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (cumulative-return
                                                                           {:window
                                                                            5})
                                                                          (select-bottom
                                                                           1)
                                                                          [(asset
                                                                            "EFA"
                                                                            "iShares MSCI EAFE ETF")
                                                                           (asset
                                                                            "EEM"
                                                                            "iShares MSCI Emerging Markets ETF")
                                                                           (asset
                                                                            "SPXS"
                                                                            "Direxion Daily S&P 500 Bear 3x Shares")
                                                                           (asset
                                                                            "SOXS"
                                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                                           (asset
                                                                            "UCO"
                                                                            "ProShares Ultra Bloomberg Crude Oil")
                                                                           (asset
                                                                            "TMV"
                                                                            "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])]
                                                              [(weight-equal
                                                                [(if
                                                                  (<
                                                                   (rsi
                                                                    "BIL"
                                                                    {:window
                                                                     7})
                                                                   (rsi
                                                                    "IEF"
                                                                    {:window
                                                                     7}))
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (moving-average-return
                                                                       {:window
                                                                        5})
                                                                      (select-bottom
                                                                       1)
                                                                      [(asset
                                                                        "EPI"
                                                                        "WisdomTree India Earnings Fund")
                                                                       (asset
                                                                        "SOXL"
                                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                                       (asset
                                                                        "UPRO"
                                                                        "ProShares UltraPro S&P500")])])]
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (cumulative-return
                                                                       {:window
                                                                        5})
                                                                      (select-top
                                                                       1)
                                                                      [(asset
                                                                        "EWZ"
                                                                        "iShares MSCI Brazil ETF")
                                                                       (asset
                                                                        "TECS"
                                                                        "Direxion Daily Technology Bear 3X Shares")
                                                                       (asset
                                                                        "SOXS"
                                                                        "Direxion Daily Semiconductor Bear 3x Shares")
                                                                       (asset
                                                                        "EUO"
                                                                        "ProShares UltraShort Euro")
                                                                       (asset
                                                                        "YCS"
                                                                        "ProShares UltraShort Yen")
                                                                       (asset
                                                                        "TMV"
                                                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])])])]
                                              [(group
                                                "B.A.B: Risk Off, Falling Rates (TMF)* - LETF Basket"
                                                [(weight-equal
                                                  [(if
                                                    (<=
                                                     (exponential-moving-average-price
                                                      "SPY"
                                                      {:window 210})
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 360}))
                                                    [(weight-equal
                                                      [(if
                                                        (<=
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 1})
                                                         -2)
                                                        [(weight-equal
                                                          [(filter
                                                            (cumulative-return
                                                             {:window
                                                              5})
                                                            (select-top
                                                             1)
                                                            [(asset
                                                              "SPXS"
                                                              "Direxion Daily S&P 500 Bear 3x Shares")
                                                             (asset
                                                              "TECS"
                                                              "Direxion Daily Technology Bear 3X Shares")
                                                             (asset
                                                              "SOXS"
                                                              "Direxion Daily Semiconductor Bear 3x Shares")
                                                             (asset
                                                              "SQQQ"
                                                              "ProShares UltraPro Short QQQ")])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>=
                                                             (cumulative-return
                                                              "SPXU"
                                                              {:window
                                                               6})
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               3}))
                                                            [(weight-equal
                                                              [(filter
                                                                (cumulative-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                 (asset
                                                                  "AGG"
                                                                  "iShares Core U.S. Aggregate Bond ETF")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "TECL"
                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                 (asset
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "EWZ"
                                                                  "iShares MSCI Brazil ETF")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (moving-average-return
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-return
                                                          "DBC"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (exponential-moving-average-price
                                                              "SPY"
                                                              {:window
                                                               210})
                                                             (exponential-moving-average-price
                                                              "SPY"
                                                              {:window
                                                               360}))
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "TQQQ"
                                                                  {:window
                                                                   11})
                                                                 77)
                                                                [(asset
                                                                  "UVXY"
                                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (cumulative-return
                                                                      "TQQQ"
                                                                      {:window
                                                                       6})
                                                                     -10)
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (cumulative-return
                                                                          "TQQQ"
                                                                          {:window
                                                                           1})
                                                                         5.5)
                                                                        [(weight-equal
                                                                          [(asset
                                                                            "UVXY"
                                                                            "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              7})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "TECL"
                                                                              "Direxion Daily Technology Bull 3x Shares")
                                                                             (asset
                                                                              "TQQQ"
                                                                              "ProShares UltraPro QQQ")
                                                                             (asset
                                                                              "SPXL"
                                                                              "Direxion Daily S&P 500 Bull 3x Shares")
                                                                             (asset
                                                                              "EPI"
                                                                              "WisdomTree India Earnings Fund")
                                                                             (asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "UPRO"
                                                                              "ProShares UltraPro S&P500")
                                                                             (asset
                                                                              "QLD"
                                                                              "ProShares Ultra QQQ")
                                                                             (asset
                                                                              "EWZ"
                                                                              "iShares MSCI Brazil ETF")
                                                                             (asset
                                                                              "MVV"
                                                                              "ProShares Ultra MidCap400")
                                                                             (asset
                                                                              "PUI"
                                                                              "Invesco DWA Utilities Momentum ETF")
                                                                             (asset
                                                                              "USD"
                                                                              "ProShares Ultra Semiconductors")
                                                                             (asset
                                                                              "TMF"
                                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "BIL"
                                                                          {:window
                                                                           7})
                                                                         (rsi
                                                                          "IEF"
                                                                          {:window
                                                                           7}))
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              7})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "TECL"
                                                                              "Direxion Daily Technology Bull 3x Shares")
                                                                             (asset
                                                                              "SPXL"
                                                                              "Direxion Daily S&P 500 Bull 3x Shares")
                                                                             (asset
                                                                              "EPI"
                                                                              "WisdomTree India Earnings Fund")
                                                                             (asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "UPRO"
                                                                              "ProShares UltraPro S&P500")
                                                                             (asset
                                                                              "MVV"
                                                                              "ProShares Ultra MidCap400")])])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (cumulative-return
                                                                             {:window
                                                                              5})
                                                                            (select-top
                                                                             1)
                                                                            [(asset
                                                                              "SOXS"
                                                                              "Direxion Daily Semiconductor Bear 3x Shares")
                                                                             (asset
                                                                              "TMF"
                                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])]
                                                            [(weight-equal
                                                              [(filter
                                                                (rsi
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "SPXS"
                                                                  "Direxion Daily S&P 500 Bear 3x Shares")
                                                                 (asset
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ")
                                                                 (asset
                                                                  "TECS"
                                                                  "Direxion Daily Technology Bear 3X Shares")
                                                                 (asset
                                                                  "SOXS"
                                                                  "Direxion Daily Semiconductor Bear 3x Shares")])])])])]
                                                        [(group
                                                          "Defense | Modified"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (stdev-return
                                                                "DBC"
                                                                {:window
                                                                 20})
                                                               (stdev-return
                                                                "SPY"
                                                                {:window
                                                                 20}))
                                                              [(weight-equal
                                                                [(filter
                                                                  (rsi
                                                                   {:window
                                                                    5})
                                                                  (select-bottom
                                                                   1)
                                                                  [(asset
                                                                    "SPXS"
                                                                    "Direxion Daily S&P 500 Bear 3x Shares")
                                                                   (asset
                                                                    "EPI"
                                                                    "WisdomTree India Earnings Fund")
                                                                   (asset
                                                                    "TECS"
                                                                    "Direxion Daily Technology Bear 3X Shares")
                                                                   (asset
                                                                    "SOXS"
                                                                    "Direxion Daily Semiconductor Bear 3x Shares")
                                                                   (asset
                                                                    "SQQQ"
                                                                    "ProShares UltraPro Short QQQ")])])]
                                                              [(weight-equal
                                                                [(filter
                                                                  (cumulative-return
                                                                   {:window
                                                                    30})
                                                                  (select-top
                                                                   3)
                                                                  [(asset
                                                                    "TQQQ"
                                                                    "ProShares UltraPro QQQ")
                                                                   (asset
                                                                    "SPXL"
                                                                    "Direxion Daily S&P 500 Bull 3x Shares")
                                                                   (asset
                                                                    "SOXL"
                                                                    "Direxion Daily Semiconductor Bull 3x Shares")
                                                                   (asset
                                                                    "FNGU"
                                                                    "MicroSectors FANG+ Index 3X Leveraged ETN")
                                                                   (asset
                                                                    "TECL"
                                                                    "Direxion Daily Technology Bull 3x Shares")])])])])])])])])])])])])])])])])])])])])])])])])])])
               (group
                ".V3.0.4 7/40 2012 | ?? Beta Baller + TCCC ?"
                [(weight-equal
                  [(if
                    (<
                     (rsi "BIL" {:window 7})
                     (rsi "IEF" {:window 40}))
                    [(weight-equal
                      [(if
                        (> (rsi "SPY" {:window 7}) 75)
                        [(group
                          "Overbought S&P. Sell the rip. Buy volatility."
                          [(weight-equal
                            [(filter
                              (rsi {:window 12})
                              (select-bottom 1)
                              [(asset
                                "UVXY"
                                "ProShares Ultra VIX Short-Term Futures ETF")
                               (asset
                                "VIXY"
                                "ProShares VIX Short-Term Futures ETF")])])])]
                        [(weight-equal
                          [(if
                            (>
                             (current-price "SOXL")
                             (moving-average-return
                              "SOXL"
                              {:window 2}))
                            [(weight-equal
                              [(filter
                                (moving-average-return {:window 12})
                                (select-top 1)
                                [(asset
                                  "SOXL"
                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                 (asset
                                  "TQQQ"
                                  "ProShares UltraPro QQQ")
                                 (asset
                                  "TECL"
                                  "Direxion Daily Technology Bull 3x Shares")
                                 (asset
                                  "FNGU"
                                  "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                            [(weight-equal
                              [(filter
                                (moving-average-return {:window 12})
                                (select-top 1)
                                [(asset
                                  "SOXS"
                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                 (asset
                                  "SQQQ"
                                  "ProShares UltraPro Short QQQ")])])])])])])]
                    [(weight-equal
                      [(if
                        (< (rsi "SPY" {:window 6}) 27)
                        [(group
                          "Extremely oversold S&P (low RSI). Double check with bond mkt before going long"
                          [(weight-equal
                            [(if
                              (<
                               (rsi "BSV" {:window 8})
                               (rsi "SPHB" {:window 8}))
                              [(weight-equal
                                [(filter
                                  (rsi {:window 7})
                                  (select-bottom 1)
                                  [(asset
                                    "SOXS"
                                    "Direxion Daily Semiconductor Bear 3x Shares")
                                   (asset
                                    "SQQQ"
                                    "ProShares UltraPro Short QQQ")])])]
                              [(weight-equal
                                [(filter
                                  (rsi {:window 18})
                                  (select-bottom 1)
                                  [(asset
                                    "SOXL"
                                    "Direxion Daily Semiconductor Bull 3x Shares")
                                   (asset
                                    "SPXL"
                                    "Direxion Daily S&P 500 Bull 3x Shares")
                                   (asset
                                    "TECL"
                                    "Direxion Daily Technology Bull 3x Shares")
                                   (asset
                                    "TMF"
                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                   (asset
                                    "UPRO"
                                    "ProShares UltraPro S&P500")
                                   (asset
                                    "USD"
                                    "ProShares Ultra Semiconductors")
                                   (asset
                                    "TQQQ"
                                    "ProShares UltraPro QQQ")
                                   (asset
                                    "FNGU"
                                    "MicroSectors FANG+ Index 3X Leveraged ETN")])])])])])]
                        [(group
                          "V0.2.1 | TCCC Stop the Bleed ? | DJKeyhole ???? | 1/2 of Momentum Mean Reversion"
                          [(weight-equal
                            [(if
                              (< (rsi "SPY" {:window 10}) 30)
                              [(group
                                "V1.2 | Five and Below | DJKeyhole | No Low Volume LETFs | Belcampo69 changed for > AR removed 1"
                                [(weight-equal
                                  [(filter
                                    (rsi {:window 17})
                                    (select-bottom 1)
                                    [(asset
                                      "SOXL"
                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                     (asset
                                      "TECL"
                                      "Direxion Daily Technology Bull 3x Shares")
                                     (asset
                                      "TMF"
                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                     (asset
                                      "UPRO"
                                      "ProShares UltraPro S&P500")
                                     (asset
                                      "FNGU"
                                      "MicroSectors FANG+ Index 3X Leveraged ETN")])])])]
                              [(weight-equal
                                [(if
                                  (> (rsi "UVXY" {:window 10}) 74)
                                  [(weight-equal
                                    [(if
                                      (> (rsi "UVXY" {:window 10}) 84)
                                      [(group
                                        "Bear Stock Market - High Inflation - [STRIPPED] V2.0.2b | A Better LETF Basket | DJKeyhole ???? | BIL and TMV"
                                        [(weight-equal
                                          [(if
                                            (>
                                             (current-price "TLT")
                                             (moving-average-price
                                              "TLT"
                                              {:window 200}))
                                            [(group
                                              "A.B: Medium term TLT may be overbought*"
                                              [(weight-equal
                                                [(if
                                                  (<
                                                   (moving-average-return
                                                    "TLT"
                                                    {:window 20})
                                                   0)
                                                  [(group
                                                    "A.B.B.A: Risk Off, Rising Rates (TMV)*"
                                                    [(weight-equal
                                                      [(if
                                                        (<=
                                                         (exponential-moving-average-price
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-price
                                                          "SPY"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               10})
                                                             30)
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "TECL"
                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                 (asset
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")
                                                                 (asset
                                                                  "FNGU"
                                                                  "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>=
                                                                 (cumulative-return
                                                                  "SPXU"
                                                                  {:window
                                                                   6})
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   3}))
                                                                [(weight-equal
                                                                  [(filter
                                                                    (cumulative-return
                                                                     {:window
                                                                      5})
                                                                    (select-top
                                                                     1)
                                                                    [(asset
                                                                      "SQQQ"
                                                                      "ProShares UltraPro Short QQQ")
                                                                     (asset
                                                                      "EUO"
                                                                      "ProShares UltraShort Euro")
                                                                     (asset
                                                                      "YCS"
                                                                      "ProShares UltraShort Yen")])])]
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      5})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "TECL"
                                                                      "Direxion Daily Technology Bull 3x Shares")
                                                                     (asset
                                                                      "TQQQ"
                                                                      "ProShares UltraPro QQQ")
                                                                     (asset
                                                                      "SOXL"
                                                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                                                     (asset
                                                                      "CURE"
                                                                      "Direxion Daily Healthcare Bull 3x Shares")
                                                                     (asset
                                                                      "FNGU"
                                                                      "MicroSectors FANG+ Index 3X Leveraged ETN")])])])])])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               11})
                                                             77)
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "TECL"
                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                 (asset
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                 (asset
                                                                  "FNGU"
                                                                  "MicroSectors FANG+ Index 3X Leveraged ETN")])])])])])])])]
                                                  [(group
                                                    "A.B.B.B: Risk Off, Falling Rates (TMF)*"
                                                    [(weight-equal
                                                      [(if
                                                        (<=
                                                         (exponential-moving-average-price
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-price
                                                          "SPY"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               10})
                                                             30)
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "TECL"
                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                 (asset
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "FNGU"
                                                                  "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                            [(weight-equal
                                                              [(if
                                                                (<=
                                                                 (cumulative-return
                                                                  "SPY"
                                                                  {:window
                                                                   2})
                                                                 -2)
                                                                [(weight-equal
                                                                  [(filter
                                                                    (cumulative-return
                                                                     {:window
                                                                      5})
                                                                    (select-top
                                                                     1)
                                                                    [(asset
                                                                      "TECS"
                                                                      "Direxion Daily Technology Bear 3X Shares")
                                                                     (asset
                                                                      "SOXS"
                                                                      "Direxion Daily Semiconductor Bear 3x Shares")
                                                                     (asset
                                                                      "SQQQ"
                                                                      "ProShares UltraPro Short QQQ")])])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>=
                                                                     (cumulative-return
                                                                      "SPXU"
                                                                      {:window
                                                                       6})
                                                                     (cumulative-return
                                                                      "UPRO"
                                                                      {:window
                                                                       3}))
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (cumulative-return
                                                                         {:window
                                                                          5})
                                                                        (select-top
                                                                         1)
                                                                        [(asset
                                                                          "ERX"
                                                                          "Direxion Daily Energy Bull 2x Shares")
                                                                         (asset
                                                                          "EUO"
                                                                          "ProShares UltraShort Euro")
                                                                         (asset
                                                                          "YCS"
                                                                          "ProShares UltraShort Yen")])])]
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          5})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "SOXL"
                                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                                         (asset
                                                                          "EWZ"
                                                                          "iShares MSCI Brazil ETF")
                                                                         (asset
                                                                          "MVV"
                                                                          "ProShares Ultra MidCap400")
                                                                         (asset
                                                                          "USD"
                                                                          "ProShares Ultra Semiconductors")
                                                                         (asset
                                                                          "FNGU"
                                                                          "MicroSectors FANG+ Index 3X Leveraged ETN")])])])])])])])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (moving-average-return
                                                              "SPY"
                                                              {:window
                                                               210})
                                                             (moving-average-return
                                                              "DBC"
                                                              {:window
                                                               360}))
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "TQQQ"
                                                                  {:window
                                                                   11})
                                                                 77)
                                                                [(asset
                                                                  "UVXY"
                                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (cumulative-return
                                                                      "TQQQ"
                                                                      {:window
                                                                       6})
                                                                     -10)
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (cumulative-return
                                                                          "TQQQ"
                                                                          {:window
                                                                           1})
                                                                         5.5)
                                                                        [(weight-equal
                                                                          [(asset
                                                                            "UVXY"
                                                                            "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (<
                                                                             (rsi
                                                                              "BIL"
                                                                              {:window
                                                                               7})
                                                                             (rsi
                                                                              "IEF"
                                                                              {:window
                                                                               7}))
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (moving-average-return
                                                                                 {:window
                                                                                  5})
                                                                                (select-bottom
                                                                                 1)
                                                                                [(asset
                                                                                  "SOXL"
                                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                 (asset
                                                                                  "FNGU"
                                                                                  "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (cumulative-return
                                                                                 {:window
                                                                                  5})
                                                                                (select-top
                                                                                 1)
                                                                                [(asset
                                                                                  "EWZ"
                                                                                  "iShares MSCI Brazil ETF")
                                                                                 (asset
                                                                                  "UUP"
                                                                                  "Invesco DB US Dollar Index Bullish Fund")
                                                                                 (asset
                                                                                  "TMF"
                                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                                 (asset
                                                                                  "UCO"
                                                                                  "ProShares Ultra Bloomberg Crude Oil")])])])])])])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "BIL"
                                                                          {:window
                                                                           7})
                                                                         (rsi
                                                                          "IEF"
                                                                          {:window
                                                                           7}))
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              5})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "TECL"
                                                                              "Direxion Daily Technology Bull 3x Shares")
                                                                             (asset
                                                                              "TQQQ"
                                                                              "ProShares UltraPro QQQ")
                                                                             (asset
                                                                              "SPXL"
                                                                              "Direxion Daily S&P 500 Bull 3x Shares")
                                                                             (asset
                                                                              "QLD"
                                                                              "ProShares Ultra QQQ")
                                                                             (asset
                                                                              "USD"
                                                                              "ProShares Ultra Semiconductors")
                                                                             (asset
                                                                              "FNGU"
                                                                              "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (cumulative-return
                                                                             {:window
                                                                              5})
                                                                            (select-top
                                                                             1)
                                                                            [(asset
                                                                              "EWZ"
                                                                              "iShares MSCI Brazil ETF")
                                                                             (asset
                                                                              "UUP"
                                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                                             (asset
                                                                              "TMF"
                                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])]
                                                            [(group
                                                              "Defense | Modified"
                                                              [(weight-equal
                                                                [(if
                                                                  (>
                                                                   (stdev-return
                                                                    "DBC"
                                                                    {:window
                                                                     20})
                                                                   (stdev-return
                                                                    "SPY"
                                                                    {:window
                                                                     20}))
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (rsi
                                                                       {:window
                                                                        5})
                                                                      (select-bottom
                                                                       1)
                                                                      [(asset
                                                                        "SHY"
                                                                        "iShares 1-3 Year Treasury Bond ETF")
                                                                       (asset
                                                                        "EWZ"
                                                                        "iShares MSCI Brazil ETF")
                                                                       (asset
                                                                        "GLD"
                                                                        "SPDR Gold Shares")
                                                                       (asset
                                                                        "SPXS"
                                                                        "Direxion Daily S&P 500 Bear 3x Shares")
                                                                       (asset
                                                                        "TECS"
                                                                        "Direxion Daily Technology Bear 3X Shares")
                                                                       (asset
                                                                        "SOXS"
                                                                        "Direxion Daily Semiconductor Bear 3x Shares")
                                                                       (asset
                                                                        "UCO"
                                                                        "ProShares Ultra Bloomberg Crude Oil")
                                                                       (asset
                                                                        "YCS"
                                                                        "ProShares UltraShort Yen")])])]
                                                                  [(weight-equal
                                                                    [(if
                                                                      (<
                                                                       (rsi
                                                                        "BIL"
                                                                        {:window
                                                                         7})
                                                                       (rsi
                                                                        "IEF"
                                                                        {:window
                                                                         7}))
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (moving-average-return
                                                                           {:window
                                                                            5})
                                                                          (select-bottom
                                                                           1)
                                                                          [(asset
                                                                            "SOXL"
                                                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                                                           (asset
                                                                            "USD"
                                                                            "ProShares Ultra Semiconductors")
                                                                           (asset
                                                                            "TMF"
                                                                            "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (cumulative-return
                                                                           {:window
                                                                            5})
                                                                          (select-top
                                                                           1)
                                                                          [(asset
                                                                            "EWZ"
                                                                            "iShares MSCI Brazil ETF")
                                                                           (asset
                                                                            "SPXS"
                                                                            "Direxion Daily S&P 500 Bear 3x Shares")
                                                                           (asset
                                                                            "SOXS"
                                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                                           (asset
                                                                            "UCO"
                                                                            "ProShares Ultra Bloomberg Crude Oil")
                                                                           (asset
                                                                            "YCS"
                                                                            "ProShares UltraShort Yen")])])])])])])])])])])])])])])])]
                                            [(group
                                              "B: If long term TLT is trending down, safety: Long Term, 2 Least Volatile*"
                                              [(weight-equal
                                                [(if
                                                  (<
                                                   (moving-average-return
                                                    "TLT"
                                                    {:window 20})
                                                   0)
                                                  [(group
                                                    "B.A.A: Risk Off, Rising Rates (TMV)* - LETF Basket^"
                                                    [(weight-equal
                                                      [(if
                                                        (<=
                                                         (exponential-moving-average-price
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-price
                                                          "SPY"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               10})
                                                             30)
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  5})
                                                                (select-top
                                                                 1)
                                                                [(asset
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "UPRO"
                                                                  "ProShares UltraPro S&P500")])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>=
                                                                 (cumulative-return
                                                                  "UUP"
                                                                  {:window
                                                                   2})
                                                                 1)
                                                                [(weight-equal
                                                                  [(filter
                                                                    (cumulative-return
                                                                     {:window
                                                                      5})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "SPXS"
                                                                      "Direxion Daily S&P 500 Bear 3x Shares")
                                                                     (asset
                                                                      "TECS"
                                                                      "Direxion Daily Technology Bear 3X Shares")
                                                                     (asset
                                                                      "SOXS"
                                                                      "Direxion Daily Semiconductor Bear 3x Shares")
                                                                     (asset
                                                                      "SQQQ"
                                                                      "ProShares UltraPro Short QQQ")
                                                                     (asset
                                                                      "ERX"
                                                                      "Direxion Daily Energy Bull 2x Shares")])])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>=
                                                                     (cumulative-return
                                                                      "SPXU"
                                                                      {:window
                                                                       5})
                                                                     (cumulative-return
                                                                      "UPRO"
                                                                      {:window
                                                                       4}))
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (cumulative-return
                                                                         {:window
                                                                          5})
                                                                        (select-top
                                                                         1)
                                                                        [(asset
                                                                          "SOXS"
                                                                          "Direxion Daily Semiconductor Bear 3x Shares")
                                                                         (asset
                                                                          "SQQQ"
                                                                          "ProShares UltraPro Short QQQ")
                                                                         (asset
                                                                          "EPI"
                                                                          "WisdomTree India Earnings Fund")])])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>=
                                                                         (cumulative-return
                                                                          "BIL"
                                                                          {:window
                                                                           3})
                                                                         (cumulative-return
                                                                          "TMV"
                                                                          {:window
                                                                           3}))
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              5})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "TECL"
                                                                              "Direxion Daily Technology Bull 3x Shares")
                                                                             (asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "TNA"
                                                                              "Direxion Daily Small Cap Bull 3x Shares")
                                                                             (asset
                                                                              "UPRO"
                                                                              "ProShares UltraPro S&P500")
                                                                             (asset
                                                                              "FNGU"
                                                                              "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              5})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "TECL"
                                                                              "Direxion Daily Technology Bull 3x Shares")
                                                                             (asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "TMV"
                                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (moving-average-return
                                                              "SPY"
                                                              {:window
                                                               210})
                                                             (moving-average-return
                                                              "DBC"
                                                              {:window
                                                               360}))
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "TQQQ"
                                                                  {:window
                                                                   11})
                                                                 77)
                                                                [(asset
                                                                  "UVXY"
                                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (cumulative-return
                                                                      "TQQQ"
                                                                      {:window
                                                                       6})
                                                                     -10)
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (cumulative-return
                                                                          "TQQQ"
                                                                          {:window
                                                                           1})
                                                                         5.5)
                                                                        [(weight-equal
                                                                          [(asset
                                                                            "UVXY"
                                                                            "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              5})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "FNGU"
                                                                              "MicroSectors FANG+ Index 3X Leveraged ETN")
                                                                             (asset
                                                                              "TMV"
                                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "BIL"
                                                                          {:window
                                                                           7})
                                                                         (rsi
                                                                          "IEF"
                                                                          {:window
                                                                           7}))
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              5})
                                                                            (select-top
                                                                             1)
                                                                            [(asset
                                                                              "TQQQ"
                                                                              "ProShares UltraPro QQQ")
                                                                             (asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "UPRO"
                                                                              "ProShares UltraPro S&P500")
                                                                             (asset
                                                                              "TMV"
                                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                             (asset
                                                                              "TECL"
                                                                              "Direxion Daily Technology Bull 3x Shares")
                                                                             (asset
                                                                              "FNGU"
                                                                              "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              22})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "UPRO"
                                                                              "ProShares UltraPro S&P500")
                                                                             (asset
                                                                              "FNGU"
                                                                              "MicroSectors FANG+ Index 3X Leveraged ETN")])])])])])])])])]
                                                            [(group
                                                              "Defense | Modified"
                                                              [(weight-equal
                                                                [(if
                                                                  (>
                                                                   (stdev-return
                                                                    "DBC"
                                                                    {:window
                                                                     20})
                                                                   (stdev-return
                                                                    "SPY"
                                                                    {:window
                                                                     20}))
                                                                  [(weight-equal
                                                                    [(if
                                                                      (>=
                                                                       (stdev-return
                                                                        "DBC"
                                                                        {:window
                                                                         10})
                                                                       3)
                                                                      [(weight-equal
                                                                        [(if
                                                                          (<=
                                                                           (stdev-return
                                                                            "TMV"
                                                                            {:window
                                                                             5})
                                                                           (stdev-return
                                                                            "DBC"
                                                                            {:window
                                                                             5}))
                                                                          [(asset
                                                                            "TMV"
                                                                            "Direxion Daily 20+ Year Treasury Bear 3x Shares")]
                                                                          [(asset
                                                                            "DBC"
                                                                            "Invesco DB Commodity Index Tracking Fund")])])]
                                                                      [(weight-equal
                                                                        [(if
                                                                          (<
                                                                           (rsi
                                                                            "BIL"
                                                                            {:window
                                                                             7})
                                                                           (rsi
                                                                            "IEF"
                                                                            {:window
                                                                             7}))
                                                                          [(weight-equal
                                                                            [(filter
                                                                              (moving-average-return
                                                                               {:window
                                                                                5})
                                                                              (select-top
                                                                               1)
                                                                              [(asset
                                                                                "TMV"
                                                                                "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                               (asset
                                                                                "SOXS"
                                                                                "Direxion Daily Semiconductor Bear 3x Shares")
                                                                               (asset
                                                                                "SPXU"
                                                                                "ProShares UltraPro Short S&P500")])])]
                                                                          [(weight-equal
                                                                            [(filter
                                                                              (cumulative-return
                                                                               {:window
                                                                                5})
                                                                              (select-bottom
                                                                               1)
                                                                              [(asset
                                                                                "EFA"
                                                                                "iShares MSCI EAFE ETF")
                                                                               (asset
                                                                                "EEM"
                                                                                "iShares MSCI Emerging Markets ETF")
                                                                               (asset
                                                                                "SPXS"
                                                                                "Direxion Daily S&P 500 Bear 3x Shares")
                                                                               (asset
                                                                                "SOXS"
                                                                                "Direxion Daily Semiconductor Bear 3x Shares")
                                                                               (asset
                                                                                "UCO"
                                                                                "ProShares Ultra Bloomberg Crude Oil")
                                                                               (asset
                                                                                "TMV"
                                                                                "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])]
                                                                  [(weight-equal
                                                                    [(if
                                                                      (<
                                                                       (rsi
                                                                        "BIL"
                                                                        {:window
                                                                         7})
                                                                       (rsi
                                                                        "IEF"
                                                                        {:window
                                                                         7}))
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (moving-average-return
                                                                           {:window
                                                                            5})
                                                                          (select-bottom
                                                                           1)
                                                                          [(asset
                                                                            "EPI"
                                                                            "WisdomTree India Earnings Fund")
                                                                           (asset
                                                                            "SOXL"
                                                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                                                           (asset
                                                                            "UPRO"
                                                                            "ProShares UltraPro S&P500")
                                                                           (asset
                                                                            "FNGU"
                                                                            "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (cumulative-return
                                                                           {:window
                                                                            5})
                                                                          (select-top
                                                                           1)
                                                                          [(asset
                                                                            "EWZ"
                                                                            "iShares MSCI Brazil ETF")
                                                                           (asset
                                                                            "TECS"
                                                                            "Direxion Daily Technology Bear 3X Shares")
                                                                           (asset
                                                                            "SOXS"
                                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                                           (asset
                                                                            "EUO"
                                                                            "ProShares UltraShort Euro")
                                                                           (asset
                                                                            "YCS"
                                                                            "ProShares UltraShort Yen")
                                                                           (asset
                                                                            "TMV"
                                                                            "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])])])]
                                                  [(group
                                                    "B.A.B: Risk Off, Falling Rates (TMF)* - LETF Basket"
                                                    [(weight-equal
                                                      [(if
                                                        (<=
                                                         (exponential-moving-average-price
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-price
                                                          "SPY"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (<=
                                                             (cumulative-return
                                                              "SPY"
                                                              {:window
                                                               2})
                                                             -2)
                                                            [(weight-equal
                                                              [(filter
                                                                (cumulative-return
                                                                 {:window
                                                                  5})
                                                                (select-top
                                                                 1)
                                                                [(asset
                                                                  "SPXS"
                                                                  "Direxion Daily S&P 500 Bear 3x Shares")
                                                                 (asset
                                                                  "TECS"
                                                                  "Direxion Daily Technology Bear 3X Shares")
                                                                 (asset
                                                                  "SOXS"
                                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                                 (asset
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ")])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>=
                                                                 (cumulative-return
                                                                  "SPXU"
                                                                  {:window
                                                                   6})
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   3}))
                                                                [(weight-equal
                                                                  [(filter
                                                                    (cumulative-return
                                                                     {:window
                                                                      5})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "BIL"
                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                     (asset
                                                                      "AGG"
                                                                      "iShares Core U.S. Aggregate Bond ETF")
                                                                     (asset
                                                                      "TMF"
                                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      5})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "TECL"
                                                                      "Direxion Daily Technology Bull 3x Shares")
                                                                     (asset
                                                                      "TQQQ"
                                                                      "ProShares UltraPro QQQ")
                                                                     (asset
                                                                      "SOXL"
                                                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                                                     (asset
                                                                      "EWZ"
                                                                      "iShares MSCI Brazil ETF")
                                                                     (asset
                                                                      "TMF"
                                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (moving-average-return
                                                              "SPY"
                                                              {:window
                                                               210})
                                                             (moving-average-return
                                                              "DBC"
                                                              {:window
                                                               360}))
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (exponential-moving-average-price
                                                                  "SPY"
                                                                  {:window
                                                                   210})
                                                                 (exponential-moving-average-price
                                                                  "SPY"
                                                                  {:window
                                                                   360}))
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "TQQQ"
                                                                      {:window
                                                                       11})
                                                                     77)
                                                                    [(asset
                                                                      "UVXY"
                                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (cumulative-return
                                                                          "TQQQ"
                                                                          {:window
                                                                           6})
                                                                         -10)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (cumulative-return
                                                                              "TQQQ"
                                                                              {:window
                                                                               1})
                                                                             5.5)
                                                                            [(weight-equal
                                                                              [(asset
                                                                                "UVXY"
                                                                                "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (moving-average-return
                                                                                 {:window
                                                                                  7})
                                                                                (select-bottom
                                                                                 1)
                                                                                [(asset
                                                                                  "TECL"
                                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                                 (asset
                                                                                  "TQQQ"
                                                                                  "ProShares UltraPro QQQ")
                                                                                 (asset
                                                                                  "SPXL"
                                                                                  "Direxion Daily S&P 500 Bull 3x Shares")
                                                                                 (asset
                                                                                  "EPI"
                                                                                  "WisdomTree India Earnings Fund")
                                                                                 (asset
                                                                                  "SOXL"
                                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                 (asset
                                                                                  "UPRO"
                                                                                  "ProShares UltraPro S&P500")
                                                                                 (asset
                                                                                  "QLD"
                                                                                  "ProShares Ultra QQQ")
                                                                                 (asset
                                                                                  "EWZ"
                                                                                  "iShares MSCI Brazil ETF")
                                                                                 (asset
                                                                                  "MVV"
                                                                                  "ProShares Ultra MidCap400")
                                                                                 (asset
                                                                                  "PUI"
                                                                                  "Invesco DWA Utilities Momentum ETF")
                                                                                 (asset
                                                                                  "USD"
                                                                                  "ProShares Ultra Semiconductors")
                                                                                 (asset
                                                                                  "TMF"
                                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (<
                                                                             (rsi
                                                                              "BIL"
                                                                              {:window
                                                                               7})
                                                                             (rsi
                                                                              "IEF"
                                                                              {:window
                                                                               7}))
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (moving-average-return
                                                                                 {:window
                                                                                  7})
                                                                                (select-bottom
                                                                                 1)
                                                                                [(asset
                                                                                  "TECL"
                                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                                 (asset
                                                                                  "SPXL"
                                                                                  "Direxion Daily S&P 500 Bull 3x Shares")
                                                                                 (asset
                                                                                  "EPI"
                                                                                  "WisdomTree India Earnings Fund")
                                                                                 (asset
                                                                                  "SOXL"
                                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                                 (asset
                                                                                  "UPRO"
                                                                                  "ProShares UltraPro S&P500")
                                                                                 (asset
                                                                                  "MVV"
                                                                                  "ProShares Ultra MidCap400")])])]
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (cumulative-return
                                                                                 {:window
                                                                                  5})
                                                                                (select-top
                                                                                 1)
                                                                                [(asset
                                                                                  "SOXS"
                                                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                 (asset
                                                                                  "TMF"
                                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])]
                                                                [(weight-equal
                                                                  [(filter
                                                                    (rsi
                                                                     {:window
                                                                      5})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "SPXS"
                                                                      "Direxion Daily S&P 500 Bear 3x Shares")
                                                                     (asset
                                                                      "SQQQ"
                                                                      "ProShares UltraPro Short QQQ")
                                                                     (asset
                                                                      "TECS"
                                                                      "Direxion Daily Technology Bear 3X Shares")
                                                                     (asset
                                                                      "SOXS"
                                                                      "Direxion Daily Semiconductor Bear 3x Shares")])])])])]
                                                            [(group
                                                              "Defense | Modified"
                                                              [(weight-equal
                                                                [(if
                                                                  (>
                                                                   (stdev-return
                                                                    "DBC"
                                                                    {:window
                                                                     20})
                                                                   (stdev-return
                                                                    "SPY"
                                                                    {:window
                                                                     20}))
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (rsi
                                                                       {:window
                                                                        5})
                                                                      (select-bottom
                                                                       1)
                                                                      [(asset
                                                                        "SPXS"
                                                                        "Direxion Daily S&P 500 Bear 3x Shares")
                                                                       (asset
                                                                        "EPI"
                                                                        "WisdomTree India Earnings Fund")
                                                                       (asset
                                                                        "TECS"
                                                                        "Direxion Daily Technology Bear 3X Shares")
                                                                       (asset
                                                                        "SOXS"
                                                                        "Direxion Daily Semiconductor Bear 3x Shares")
                                                                       (asset
                                                                        "SQQQ"
                                                                        "ProShares UltraPro Short QQQ")])])]
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (moving-average-return
                                                                       {:window
                                                                        5})
                                                                      (select-top
                                                                       1)
                                                                      [(asset
                                                                        "TECL"
                                                                        "Direxion Daily Technology Bull 3x Shares")
                                                                       (asset
                                                                        "TQQQ"
                                                                        "ProShares UltraPro QQQ")
                                                                       (asset
                                                                        "SOXL"
                                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                                       (asset
                                                                        "TMF"
                                                                        "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])])])])])])])])])]
                                      [(asset
                                        "UVXY"
                                        "ProShares Ultra VIX Short-Term Futures ETF")])])]
                                  [(group
                                    "Bear Stock Market - High Inflation - [STRIPPED] V2.0.2b | A Better LETF Basket | DJKeyhole ???? | BIL and TMV"
                                    [(weight-equal
                                      [(if
                                        (>
                                         (current-price "TLT")
                                         (moving-average-price
                                          "TLT"
                                          {:window 200}))
                                        [(group
                                          "A.B: Medium term TLT may be overbought*"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (moving-average-return
                                                "TLT"
                                                {:window 20})
                                               0)
                                              [(group
                                                "A.B.B.A: Risk Off, Rising Rates (TMV)*"
                                                [(weight-equal
                                                  [(if
                                                    (<=
                                                     (exponential-moving-average-price
                                                      "SPY"
                                                      {:window 210})
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 360}))
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "TQQQ"
                                                          {:window 10})
                                                         30)
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              5})
                                                            (select-bottom
                                                             1)
                                                            [(asset
                                                              "TECL"
                                                              "Direxion Daily Technology Bull 3x Shares")
                                                             (asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")
                                                             (asset
                                                              "SOXL"
                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                             (asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")
                                                             (asset
                                                              "FNGU"
                                                              "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                        [(weight-equal
                                                          [(if
                                                            (<=
                                                             (cumulative-return
                                                              "SPXU"
                                                              {:window
                                                               6})
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               3}))
                                                            [(weight-equal
                                                              [(filter
                                                                (cumulative-return
                                                                 {:window
                                                                  5})
                                                                (select-top
                                                                 1)
                                                                [(asset
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ")
                                                                 (asset
                                                                  "EUO"
                                                                  "ProShares UltraShort Euro")
                                                                 (asset
                                                                  "YCS"
                                                                  "ProShares UltraShort Yen")])])]
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "TECL"
                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                 (asset
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "CURE"
                                                                  "Direxion Daily Healthcare Bull 3x Shares")
                                                                 (asset
                                                                  "FNGU"
                                                                  "MicroSectors FANG+ Index 3X Leveraged ETN")])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "TQQQ"
                                                          {:window 11})
                                                         77)
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              5})
                                                            (select-bottom
                                                             1)
                                                            [(asset
                                                              "TECL"
                                                              "Direxion Daily Technology Bull 3x Shares")
                                                             (asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")
                                                             (asset
                                                              "SOXL"
                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                             (asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])]
                                              [(group
                                                "A.B.B.B: Risk Off, Falling Rates (TMF)*"
                                                [(weight-equal
                                                  [(if
                                                    (<=
                                                     (exponential-moving-average-price
                                                      "SPY"
                                                      {:window 210})
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 360}))
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "TQQQ"
                                                          {:window 10})
                                                         30)
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              5})
                                                            (select-bottom
                                                             1)
                                                            [(asset
                                                              "TECL"
                                                              "Direxion Daily Technology Bull 3x Shares")
                                                             (asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")
                                                             (asset
                                                              "SOXL"
                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                             (asset
                                                              "FNGU"
                                                              "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>=
                                                             (cumulative-return
                                                              "UUP"
                                                              {:window
                                                               2})
                                                             1)
                                                            [(weight-equal
                                                              [(filter
                                                                (cumulative-return
                                                                 {:window
                                                                  5})
                                                                (select-top
                                                                 1)
                                                                [(asset
                                                                  "TECS"
                                                                  "Direxion Daily Technology Bear 3X Shares")
                                                                 (asset
                                                                  "SOXS"
                                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                                 (asset
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ")])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>=
                                                                 (cumulative-return
                                                                  "SPXU"
                                                                  {:window
                                                                   5})
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   4}))
                                                                [(weight-equal
                                                                  [(filter
                                                                    (cumulative-return
                                                                     {:window
                                                                      5})
                                                                    (select-top
                                                                     1)
                                                                    [(asset
                                                                      "ERX"
                                                                      "Direxion Daily Energy Bull 2x Shares")
                                                                     (asset
                                                                      "EUO"
                                                                      "ProShares UltraShort Euro")
                                                                     (asset
                                                                      "YCS"
                                                                      "ProShares UltraShort Yen")])])]
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      5})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "SOXL"
                                                                      "Direxion Daily Semiconductor Bull 3x Shares")
                                                                     (asset
                                                                      "EWZ"
                                                                      "iShares MSCI Brazil ETF")
                                                                     (asset
                                                                      "MVV"
                                                                      "ProShares Ultra MidCap400")
                                                                     (asset
                                                                      "USD"
                                                                      "ProShares Ultra Semiconductors")])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (moving-average-return
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-return
                                                          "DBC"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               11})
                                                             77)
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (cumulative-return
                                                                  "TQQQ"
                                                                  {:window
                                                                   6})
                                                                 -10)
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (cumulative-return
                                                                      "TQQQ"
                                                                      {:window
                                                                       1})
                                                                     5.5)
                                                                    [(weight-equal
                                                                      [(asset
                                                                        "UVXY"
                                                                        "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "BIL"
                                                                          {:window
                                                                           7})
                                                                         (rsi
                                                                          "IEF"
                                                                          {:window
                                                                           7}))
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              5})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "FNGU"
                                                                              "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (cumulative-return
                                                                             {:window
                                                                              5})
                                                                            (select-top
                                                                             1)
                                                                            [(asset
                                                                              "EWZ"
                                                                              "iShares MSCI Brazil ETF")
                                                                             (asset
                                                                              "UUP"
                                                                              "Invesco DB US Dollar Index Bullish Fund")
                                                                             (asset
                                                                              "TMF"
                                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                             (asset
                                                                              "UCO"
                                                                              "ProShares Ultra Bloomberg Crude Oil")])])])])])])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (rsi
                                                                      "BIL"
                                                                      {:window
                                                                       7})
                                                                     (rsi
                                                                      "IEF"
                                                                      {:window
                                                                       7}))
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          5})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "TECL"
                                                                          "Direxion Daily Technology Bull 3x Shares")
                                                                         (asset
                                                                          "TQQQ"
                                                                          "ProShares UltraPro QQQ")
                                                                         (asset
                                                                          "SPXL"
                                                                          "Direxion Daily S&P 500 Bull 3x Shares")
                                                                         (asset
                                                                          "QLD"
                                                                          "ProShares Ultra QQQ")
                                                                         (asset
                                                                          "USD"
                                                                          "ProShares Ultra Semiconductors")
                                                                         (asset
                                                                          "FNGU"
                                                                          "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (cumulative-return
                                                                         {:window
                                                                          5})
                                                                        (select-top
                                                                         1)
                                                                        [(asset
                                                                          "EWZ"
                                                                          "iShares MSCI Brazil ETF")
                                                                         (asset
                                                                          "UUP"
                                                                          "Invesco DB US Dollar Index Bullish Fund")
                                                                         (asset
                                                                          "TMF"
                                                                          "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])]
                                                        [(group
                                                          "Defense | Modified"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (stdev-return
                                                                "DBC"
                                                                {:window
                                                                 20})
                                                               (stdev-return
                                                                "SPY"
                                                                {:window
                                                                 20}))
                                                              [(weight-equal
                                                                [(filter
                                                                  (rsi
                                                                   {:window
                                                                    5})
                                                                  (select-bottom
                                                                   1)
                                                                  [(asset
                                                                    "SHY"
                                                                    "iShares 1-3 Year Treasury Bond ETF")
                                                                   (asset
                                                                    "EWZ"
                                                                    "iShares MSCI Brazil ETF")
                                                                   (asset
                                                                    "GLD"
                                                                    "SPDR Gold Shares")
                                                                   (asset
                                                                    "SPXS"
                                                                    "Direxion Daily S&P 500 Bear 3x Shares")
                                                                   (asset
                                                                    "TECS"
                                                                    "Direxion Daily Technology Bear 3X Shares")
                                                                   (asset
                                                                    "SOXS"
                                                                    "Direxion Daily Semiconductor Bear 3x Shares")
                                                                   (asset
                                                                    "UCO"
                                                                    "ProShares Ultra Bloomberg Crude Oil")
                                                                   (asset
                                                                    "YCS"
                                                                    "ProShares UltraShort Yen")])])]
                                                              [(weight-equal
                                                                [(if
                                                                  (<
                                                                   (rsi
                                                                    "BIL"
                                                                    {:window
                                                                     7})
                                                                   (rsi
                                                                    "IEF"
                                                                    {:window
                                                                     7}))
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (moving-average-return
                                                                       {:window
                                                                        5})
                                                                      (select-bottom
                                                                       1)
                                                                      [(asset
                                                                        "SOXL"
                                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                                       (asset
                                                                        "USD"
                                                                        "ProShares Ultra Semiconductors")
                                                                       (asset
                                                                        "TMF"
                                                                        "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                       (asset
                                                                        "FNGU"
                                                                        "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (cumulative-return
                                                                       {:window
                                                                        5})
                                                                      (select-top
                                                                       1)
                                                                      [(asset
                                                                        "EWZ"
                                                                        "iShares MSCI Brazil ETF")
                                                                       (asset
                                                                        "SPXS"
                                                                        "Direxion Daily S&P 500 Bear 3x Shares")
                                                                       (asset
                                                                        "SOXS"
                                                                        "Direxion Daily Semiconductor Bear 3x Shares")
                                                                       (asset
                                                                        "UCO"
                                                                        "ProShares Ultra Bloomberg Crude Oil")
                                                                       (asset
                                                                        "YCS"
                                                                        "ProShares UltraShort Yen")])])])])])])])])])])])])])])])]
                                        [(group
                                          "B: If long term TLT is trending down, safety: Long Term, 2 Least Volatile*"
                                          [(weight-equal
                                            [(if
                                              (<
                                               (moving-average-return
                                                "TLT"
                                                {:window 20})
                                               0)
                                              [(group
                                                "B.A.A: Risk Off, Rising Rates (TMV)* - LETF Basket^"
                                                [(weight-equal
                                                  [(if
                                                    (<=
                                                     (exponential-moving-average-price
                                                      "SPY"
                                                      {:window 210})
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 360}))
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "TQQQ"
                                                          {:window 10})
                                                         30)
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              5})
                                                            (select-top
                                                             1)
                                                            [(asset
                                                              "TQQQ"
                                                              "ProShares UltraPro QQQ")
                                                             (asset
                                                              "SOXL"
                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                             (asset
                                                              "UPRO"
                                                              "ProShares UltraPro S&P500")
                                                             (asset
                                                              "FNGU"
                                                              "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>=
                                                             (cumulative-return
                                                              "UUP"
                                                              {:window
                                                               2})
                                                             1)
                                                            [(weight-equal
                                                              [(filter
                                                                (cumulative-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "SPXS"
                                                                  "Direxion Daily S&P 500 Bear 3x Shares")
                                                                 (asset
                                                                  "TECS"
                                                                  "Direxion Daily Technology Bear 3X Shares")
                                                                 (asset
                                                                  "SOXS"
                                                                  "Direxion Daily Semiconductor Bear 3x Shares")
                                                                 (asset
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ")
                                                                 (asset
                                                                  "ERX"
                                                                  "Direxion Daily Energy Bull 2x Shares")])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>=
                                                                 (cumulative-return
                                                                  "SPXU"
                                                                  {:window
                                                                   5})
                                                                 (cumulative-return
                                                                  "UPRO"
                                                                  {:window
                                                                   4}))
                                                                [(weight-equal
                                                                  [(filter
                                                                    (cumulative-return
                                                                     {:window
                                                                      5})
                                                                    (select-top
                                                                     1)
                                                                    [(asset
                                                                      "SOXS"
                                                                      "Direxion Daily Semiconductor Bear 3x Shares")
                                                                     (asset
                                                                      "SQQQ"
                                                                      "ProShares UltraPro Short QQQ")
                                                                     (asset
                                                                      "EPI"
                                                                      "WisdomTree India Earnings Fund")])])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>=
                                                                     (cumulative-return
                                                                      "BIL"
                                                                      {:window
                                                                       3})
                                                                     (cumulative-return
                                                                      "TMV"
                                                                      {:window
                                                                       3}))
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          5})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "TECL"
                                                                          "Direxion Daily Technology Bull 3x Shares")
                                                                         (asset
                                                                          "SOXL"
                                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                                         (asset
                                                                          "TNA"
                                                                          "Direxion Daily Small Cap Bull 3x Shares")])])]
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
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
                                                                          "TMV"
                                                                          "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                         (asset
                                                                          "TQQQ"
                                                                          "ProShares UltraPro QQQ")])])])])])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (moving-average-return
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-return
                                                          "DBC"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "TQQQ"
                                                              {:window
                                                               11})
                                                             77)
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (cumulative-return
                                                                  "TQQQ"
                                                                  {:window
                                                                   6})
                                                                 -10)
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (cumulative-return
                                                                      "TQQQ"
                                                                      {:window
                                                                       1})
                                                                     5.5)
                                                                    [(weight-equal
                                                                      [(asset
                                                                        "UVXY"
                                                                        "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          5})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "SOXL"
                                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                                         (asset
                                                                          "TMV"
                                                                          "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (rsi
                                                                      "BIL"
                                                                      {:window
                                                                       7})
                                                                     (rsi
                                                                      "IEF"
                                                                      {:window
                                                                       7}))
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          5})
                                                                        (select-top
                                                                         1)
                                                                        [(asset
                                                                          "TQQQ"
                                                                          "ProShares UltraPro QQQ")
                                                                         (asset
                                                                          "SOXL"
                                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                                         (asset
                                                                          "UPRO"
                                                                          "ProShares UltraPro S&P500")
                                                                         (asset
                                                                          "TMV"
                                                                          "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                         (asset
                                                                          "TECL"
                                                                          "Direxion Daily Technology Bull 3x Shares")
                                                                         (asset
                                                                          "FNGU"
                                                                          "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          22})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "SOXL"
                                                                          "Direxion Daily Semiconductor Bull 3x Shares")
                                                                         (asset
                                                                          "UPRO"
                                                                          "ProShares UltraPro S&P500")])])])])])])])])]
                                                        [(group
                                                          "Defense | Modified"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (stdev-return
                                                                "DBC"
                                                                {:window
                                                                 20})
                                                               (stdev-return
                                                                "SPY"
                                                                {:window
                                                                 20}))
                                                              [(weight-equal
                                                                [(if
                                                                  (>=
                                                                   (stdev-return
                                                                    "DBC"
                                                                    {:window
                                                                     10})
                                                                   3)
                                                                  [(weight-equal
                                                                    [(if
                                                                      (<=
                                                                       (stdev-return
                                                                        "TMV"
                                                                        {:window
                                                                         5})
                                                                       (stdev-return
                                                                        "DBC"
                                                                        {:window
                                                                         5}))
                                                                      [(asset
                                                                        "TMV"
                                                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")]
                                                                      [(asset
                                                                        "DBC"
                                                                        "Invesco DB Commodity Index Tracking Fund")])])]
                                                                  [(weight-equal
                                                                    [(if
                                                                      (<
                                                                       (rsi
                                                                        "BIL"
                                                                        {:window
                                                                         7})
                                                                       (rsi
                                                                        "IEF"
                                                                        {:window
                                                                         7}))
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (moving-average-return
                                                                           {:window
                                                                            5})
                                                                          (select-top
                                                                           1)
                                                                          [(asset
                                                                            "TMV"
                                                                            "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                           (asset
                                                                            "SOXS"
                                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                                           (asset
                                                                            "SPXU"
                                                                            "ProShares UltraPro Short S&P500")])])]
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (cumulative-return
                                                                           {:window
                                                                            5})
                                                                          (select-bottom
                                                                           1)
                                                                          [(asset
                                                                            "EFA"
                                                                            "iShares MSCI EAFE ETF")
                                                                           (asset
                                                                            "EEM"
                                                                            "iShares MSCI Emerging Markets ETF")
                                                                           (asset
                                                                            "SPXS"
                                                                            "Direxion Daily S&P 500 Bear 3x Shares")
                                                                           (asset
                                                                            "SOXS"
                                                                            "Direxion Daily Semiconductor Bear 3x Shares")
                                                                           (asset
                                                                            "UCO"
                                                                            "ProShares Ultra Bloomberg Crude Oil")
                                                                           (asset
                                                                            "TMV"
                                                                            "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])]
                                                              [(weight-equal
                                                                [(if
                                                                  (<
                                                                   (rsi
                                                                    "BIL"
                                                                    {:window
                                                                     7})
                                                                   (rsi
                                                                    "IEF"
                                                                    {:window
                                                                     7}))
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (moving-average-return
                                                                       {:window
                                                                        5})
                                                                      (select-bottom
                                                                       1)
                                                                      [(asset
                                                                        "EPI"
                                                                        "WisdomTree India Earnings Fund")
                                                                       (asset
                                                                        "SOXL"
                                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                                       (asset
                                                                        "UPRO"
                                                                        "ProShares UltraPro S&P500")])])]
                                                                  [(weight-equal
                                                                    [(filter
                                                                      (cumulative-return
                                                                       {:window
                                                                        5})
                                                                      (select-top
                                                                       1)
                                                                      [(asset
                                                                        "EWZ"
                                                                        "iShares MSCI Brazil ETF")
                                                                       (asset
                                                                        "TECS"
                                                                        "Direxion Daily Technology Bear 3X Shares")
                                                                       (asset
                                                                        "SOXS"
                                                                        "Direxion Daily Semiconductor Bear 3x Shares")
                                                                       (asset
                                                                        "EUO"
                                                                        "ProShares UltraShort Euro")
                                                                       (asset
                                                                        "YCS"
                                                                        "ProShares UltraShort Yen")
                                                                       (asset
                                                                        "TMV"
                                                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])])])]
                                              [(group
                                                "B.A.B: Risk Off, Falling Rates (TMF)* - LETF Basket"
                                                [(weight-equal
                                                  [(if
                                                    (<=
                                                     (exponential-moving-average-price
                                                      "SPY"
                                                      {:window 210})
                                                     (moving-average-price
                                                      "SPY"
                                                      {:window 360}))
                                                    [(weight-equal
                                                      [(if
                                                        (<=
                                                         (cumulative-return
                                                          "SPY"
                                                          {:window 1})
                                                         -2)
                                                        [(weight-equal
                                                          [(filter
                                                            (cumulative-return
                                                             {:window
                                                              5})
                                                            (select-top
                                                             1)
                                                            [(asset
                                                              "SPXS"
                                                              "Direxion Daily S&P 500 Bear 3x Shares")
                                                             (asset
                                                              "TECS"
                                                              "Direxion Daily Technology Bear 3X Shares")
                                                             (asset
                                                              "SOXS"
                                                              "Direxion Daily Semiconductor Bear 3x Shares")
                                                             (asset
                                                              "SQQQ"
                                                              "ProShares UltraPro Short QQQ")])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>=
                                                             (cumulative-return
                                                              "SPXU"
                                                              {:window
                                                               6})
                                                             (cumulative-return
                                                              "UPRO"
                                                              {:window
                                                               3}))
                                                            [(weight-equal
                                                              [(filter
                                                                (cumulative-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                 (asset
                                                                  "AGG"
                                                                  "iShares Core U.S. Aggregate Bond ETF")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "TECL"
                                                                  "Direxion Daily Technology Bull 3x Shares")
                                                                 (asset
                                                                  "TQQQ"
                                                                  "ProShares UltraPro QQQ")
                                                                 (asset
                                                                  "SOXL"
                                                                  "Direxion Daily Semiconductor Bull 3x Shares")
                                                                 (asset
                                                                  "EWZ"
                                                                  "iShares MSCI Brazil ETF")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                 (asset
                                                                  "FNGU"
                                                                  "MicroSectors FANG+ Index 3X Leveraged ETN")])])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (moving-average-return
                                                          "SPY"
                                                          {:window
                                                           210})
                                                         (moving-average-return
                                                          "DBC"
                                                          {:window
                                                           360}))
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (exponential-moving-average-price
                                                              "SPY"
                                                              {:window
                                                               210})
                                                             (exponential-moving-average-price
                                                              "SPY"
                                                              {:window
                                                               360}))
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "TQQQ"
                                                                  {:window
                                                                   11})
                                                                 77)
                                                                [(asset
                                                                  "UVXY"
                                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (cumulative-return
                                                                      "TQQQ"
                                                                      {:window
                                                                       6})
                                                                     -10)
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (cumulative-return
                                                                          "TQQQ"
                                                                          {:window
                                                                           1})
                                                                         5.5)
                                                                        [(weight-equal
                                                                          [(asset
                                                                            "UVXY"
                                                                            "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              7})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "TECL"
                                                                              "Direxion Daily Technology Bull 3x Shares")
                                                                             (asset
                                                                              "TQQQ"
                                                                              "ProShares UltraPro QQQ")
                                                                             (asset
                                                                              "SPXL"
                                                                              "Direxion Daily S&P 500 Bull 3x Shares")
                                                                             (asset
                                                                              "EPI"
                                                                              "WisdomTree India Earnings Fund")
                                                                             (asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "UPRO"
                                                                              "ProShares UltraPro S&P500")
                                                                             (asset
                                                                              "QLD"
                                                                              "ProShares Ultra QQQ")
                                                                             (asset
                                                                              "EWZ"
                                                                              "iShares MSCI Brazil ETF")
                                                                             (asset
                                                                              "MVV"
                                                                              "ProShares Ultra MidCap400")
                                                                             (asset
                                                                              "PUI"
                                                                              "Invesco DWA Utilities Momentum ETF")
                                                                             (asset
                                                                              "USD"
                                                                              "ProShares Ultra Semiconductors")
                                                                             (asset
                                                                              "TMF"
                                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                             (asset
                                                                              "FNGU"
                                                                              "MicroSectors FANG+ Index 3X Leveraged ETN")])])])])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "BIL"
                                                                          {:window
                                                                           7})
                                                                         (rsi
                                                                          "IEF"
                                                                          {:window
                                                                           7}))
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (moving-average-return
                                                                             {:window
                                                                              7})
                                                                            (select-bottom
                                                                             1)
                                                                            [(asset
                                                                              "TECL"
                                                                              "Direxion Daily Technology Bull 3x Shares")
                                                                             (asset
                                                                              "SPXL"
                                                                              "Direxion Daily S&P 500 Bull 3x Shares")
                                                                             (asset
                                                                              "EPI"
                                                                              "WisdomTree India Earnings Fund")
                                                                             (asset
                                                                              "SOXL"
                                                                              "Direxion Daily Semiconductor Bull 3x Shares")
                                                                             (asset
                                                                              "UPRO"
                                                                              "ProShares UltraPro S&P500")
                                                                             (asset
                                                                              "MVV"
                                                                              "ProShares Ultra MidCap400")
                                                                             (asset
                                                                              "FNGU"
                                                                              "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                                                        [(weight-equal
                                                                          [(filter
                                                                            (cumulative-return
                                                                             {:window
                                                                              5})
                                                                            (select-top
                                                                             1)
                                                                            [(asset
                                                                              "SOXS"
                                                                              "Direxion Daily Semiconductor Bear 3x Shares")
                                                                             (asset
                                                                              "TMF"
                                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])]
                                                            [(weight-equal
                                                              [(filter
                                                                (rsi
                                                                 {:window
                                                                  5})
                                                                (select-bottom
                                                                 1)
                                                                [(asset
                                                                  "SPXS"
                                                                  "Direxion Daily S&P 500 Bear 3x Shares")
                                                                 (asset
                                                                  "SQQQ"
                                                                  "ProShares UltraPro Short QQQ")
                                                                 (asset
                                                                  "TECS"
                                                                  "Direxion Daily Technology Bear 3X Shares")
                                                                 (asset
                                                                  "SOXS"
                                                                  "Direxion Daily Semiconductor Bear 3x Shares")])])])])]
                                                        [(group
                                                          "Defense | Modified"
                                                          [(weight-equal
                                                            [(if
                                                              (>
                                                               (stdev-return
                                                                "DBC"
                                                                {:window
                                                                 20})
                                                               (stdev-return
                                                                "SPY"
                                                                {:window
                                                                 20}))
                                                              [(weight-equal
                                                                [(filter
                                                                  (rsi
                                                                   {:window
                                                                    5})
                                                                  (select-bottom
                                                                   1)
                                                                  [(asset
                                                                    "SPXS"
                                                                    "Direxion Daily S&P 500 Bear 3x Shares")
                                                                   (asset
                                                                    "EPI"
                                                                    "WisdomTree India Earnings Fund")
                                                                   (asset
                                                                    "TECS"
                                                                    "Direxion Daily Technology Bear 3X Shares")
                                                                   (asset
                                                                    "SOXS"
                                                                    "Direxion Daily Semiconductor Bear 3x Shares")
                                                                   (asset
                                                                    "SQQQ"
                                                                    "ProShares UltraPro Short QQQ")])])]
                                                              [(weight-equal
                                                                [(filter
                                                                  (moving-average-return
                                                                   {:window
                                                                    5})
                                                                  (select-top
                                                                   1)
                                                                  [(asset
                                                                    "TECL"
                                                                    "Direxion Daily Technology Bull 3x Shares")
                                                                   (asset
                                                                    "TQQQ"
                                                                    "ProShares UltraPro QQQ")
                                                                   (asset
                                                                    "SOXL"
                                                                    "Direxion Daily Semiconductor Bull 3x Shares")
                                                                   (asset
                                                                    "TMF"
                                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                   (asset
                                                                    "FNGU"
                                                                    "MicroSectors FANG+ Index 3X Leveraged ETN")])])])])])])])])])])])])])])])])])])])])])])])])])])])])
           (group
            "Copy of  7e TQQQ FTLT V4.2.5a + Sideways Market Deleverage | No K-1"
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
                                        "ProShares UltraPro Short QQQ")
                                       (asset
                                        "FNGD"
                                        "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")]
                                      [(weight-equal
                                        [(if
                                          (>
                                           (rsi "TQQQ" {:window 10})
                                           20)
                                          [(asset
                                            "SQQQ"
                                            "ProShares UltraPro Short QQQ")
                                           (asset
                                            "FNGD"
                                            "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")]
                                          [(weight-equal
                                            [(filter
                                              (cumulative-return
                                               {:window 30})
                                              (select-top 3)
                                              [(asset
                                                "TQQQ"
                                                "ProShares UltraPro QQQ")
                                               (asset
                                                "SPXL"
                                                "Direxion Daily S&P 500 Bull 3x Shares")
                                               (asset
                                                "SOXL"
                                                "Direxion Daily Semiconductor Bull 3x Shares")
                                               (asset
                                                "FNGU"
                                                "MicroSectors FANG+ Index 3X Leveraged ETN")
                                               (asset
                                                "TECL"
                                                "Direxion Daily Technology Bull 3x Shares")])])])])])])]
                                  [(weight-specified
                                    1
                                    (if
                                     (> (rsi "QQQ" {:window 10}) 80)
                                     [(asset
                                       "SQQQ"
                                       "ProShares UltraPro Short QQQ")
                                      (asset
                                       "FNGD"
                                       "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")]
                                     [(weight-equal
                                       [(if
                                         (<
                                          (rsi "QQQ" {:window 10})
                                          31)
                                         [(asset
                                           "SOXL"
                                           "Direxion Daily Semiconductor Bull 3x Shares")]
                                         [(group
                                           "\"A Better QQQ\""
                                           [(weight-equal
                                             [(filter
                                               (moving-average-return
                                                {:window 20})
                                               (select-top 1)
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
                                                 "MicroSectors U.S. Big Oil Index 3X Leveraged ETN")])])])])])]))])])])])])])])]
                    [(weight-equal
                      [(if
                        (<= (cumulative-return "QQQ" {:window 60}) -20)
                        [(group
                          "Sideways Market Deleverage"
                          [(weight-equal
                            [(if
                              (>=
                               (cumulative-return "UUP" {:window 2})
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
                                        "MicroSectors U.S. Big Oil Index -3X Inverse Leveraged ETN")
                                       (asset
                                        "FNGD"
                                        "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")])])])])]
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
                                 (cumulative-return "TQQQ" {:window 2})
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
                                                    "ProShares UltraPro Short QQQ")
                                                   (asset
                                                    "FNGD"
                                                    "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")]
                                                  [(weight-equal
                                                    [(filter
                                                      (cumulative-return
                                                       {:window 30})
                                                      (select-top 3)
                                                      [(asset
                                                        "TQQQ"
                                                        "ProShares UltraPro QQQ")
                                                       (asset
                                                        "SPXL"
                                                        "Direxion Daily S&P 500 Bull 3x Shares")
                                                       (asset
                                                        "SOXL"
                                                        "Direxion Daily Semiconductor Bull 3x Shares")
                                                       (asset
                                                        "FNGU"
                                                        "MicroSectors FANG+ Index 3X Leveraged ETN")
                                                       (asset
                                                        "TECL"
                                                        "Direxion Daily Technology Bull 3x Shares")])])])])]
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
                                              "ProShares UltraPro Short QQQ")
                                             (asset
                                              "FNGD"
                                              "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")])])]
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
                                             (rsi "SQQQ" {:window 10})
                                             31)
                                            [(asset
                                              "SOXS"
                                              "Direxion Daily Semiconductor Bear 3x Shares")
                                             (asset
                                              "FNGD"
                                              "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")]
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
                                              "ProShares UltraPro Short QQQ")
                                             (asset
                                              "FNGD"
                                              "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")])])])])])])])])])])])])])])])])])
           (group
            " ? SOXX RSI Machine | Deez | 3YR-BT: AR 391.9% DD: 52.0% | 15NOV2022"
            [(weight-equal
              [(group
                "? SOXX RSI Machine | Deez | 15NOV2022"
                [(weight-equal
                  [(if
                    (> (rsi "SOXX" {:window 10}) 63)
                    [(weight-equal
                      [(asset
                        "SOXS"
                        "Direxion Daily Semiconductor Bear 3x Shares")])]
                    [(weight-equal
                      [(if
                        (< (rsi "SOXX" {:window 2}) 41)
                        [(weight-equal
                          [(if
                            (< (rsi "SOXL" {:window 10}) 57)
                            [(weight-equal
                              [(filter
                                (cumulative-return {:window 30})
                                (select-top 1)
                                [(asset
                                  "SOXL"
                                  "Direxion Daily Semiconductor Bull 3x Shares")])])]
                            [(asset
                              "SOXS"
                              "Direxion Daily Semiconductor Bear 3x Shares")
                             (asset
                              "FNGD"
                              "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")])])]
                        [(group
                          "V2a | ? Gain Train DGAF | Deez | (A: 0.30, B: 0.01, R^2: 0, R: 0.02) BT - 1JAN2015"
                          [(weight-equal
                            [(weight-specified
                              0.45
                              (if
                               (>
                                (exponential-moving-average-price
                                 "UUP"
                                 {:window 42})
                                (exponential-moving-average-price
                                 "UUP"
                                 {:window 100}))
                               [(weight-equal
                                 [(filter
                                   (rsi {:window 14})
                                   (select-bottom 1)
                                   [(asset
                                     "UUP"
                                     "Invesco DB US Dollar Index Bullish Fund")
                                    (asset
                                     "USDU"
                                     "WisdomTree Bloomberg US Dollar Bullish Fund")])])]
                               [(weight-equal
                                 [(filter
                                   (stdev-price {:window 14})
                                   (select-top 2)
                                   [(asset
                                     "BIL"
                                     "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                    (asset
                                     "SOXL"
                                     "Direxion Daily Semiconductor Bull 3x Shares")
                                    (asset
                                     "DBC"
                                     "Invesco DB Commodity Index Tracking Fund")])])])
                              0.45
                              (if
                               (<
                                (rsi "BIL" {:window 10})
                                (rsi "IEF" {:window 10}))
                               [(weight-equal
                                 [(if
                                   (> (rsi "SPY" {:window 7}) 76)
                                   [(group
                                     "Overbought S&P. Sell the rip. Buy volatility."
                                     [(weight-equal
                                       [(asset
                                         "UGL"
                                         "ProShares Ultra Gold")])])]
                                   [(weight-equal
                                     [(filter
                                       (max-drawdown {:window 6})
                                       (select-top 1)
                                       [(asset
                                         "SOXL"
                                         "Direxion Daily Semiconductor Bull 3x Shares")
                                        (asset
                                         "SMH"
                                         "VanEck Semiconductor ETF")])])])])]
                               [(weight-equal
                                 [(if
                                   (< (rsi "SPY" {:window 7}) 27)
                                   [(group
                                     "Extremely oversold S&P (low RSI). Double check with bond mkt before going long"
                                     [(weight-equal
                                       [(if
                                         (<
                                          (rsi "SHY" {:window 10})
                                          (rsi "VTI" {:window 10}))
                                         [(asset
                                           "SOXS"
                                           "Direxion Daily Semiconductor Bear 3x Shares")
                                          (asset
                                           "FNGD"
                                           "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")]
                                         [(weight-equal
                                           [(filter
                                             (cumulative-return
                                              {:window 30})
                                             (select-top 3)
                                             [(asset
                                               "TQQQ"
                                               "ProShares UltraPro QQQ")
                                              (asset
                                               "SPXL"
                                               "Direxion Daily S&P 500 Bull 3x Shares")
                                              (asset
                                               "SOXL"
                                               "Direxion Daily Semiconductor Bull 3x Shares")
                                              (asset
                                               "FNGU"
                                               "MicroSectors FANG+ Index 3X Leveraged ETN")
                                              (asset
                                               "TECL"
                                               "Direxion Daily Technology Bull 3x Shares")])])])])])]
                                   [(asset
                                     "UGL"
                                     "ProShares Ultra Gold")
                                    (asset
                                     "SH"
                                     "ProShares Short S&P500")
                                    (asset
                                     "PSQ"
                                     "ProShares Short QQQ")])])])
                              0.1
                              (group
                               "? Operation: Meat Shield | [Low Touch] | 3Y BT ~ AR: 31.7%, DD: 21.7%"
                               [(weight-specified
                                 0.2
                                 (if
                                  (< (rsi "COST" {:window 14}) 69)
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown "SPY" {:window 5})
                                       12)
                                      [(asset
                                        "BIL"
                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")]
                                      [(weight-equal
                                        [(filter
                                          (cumulative-return
                                           {:window 30})
                                          (select-bottom 1)
                                          [(asset
                                            "TQQQ"
                                            "ProShares UltraPro QQQ")
                                           (asset
                                            "SPXL"
                                            "Direxion Daily S&P 500 Bull 3x Shares")
                                           (asset
                                            "SOXL"
                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                           (asset
                                            "FNGU"
                                            "MicroSectors FANG+ Index 3X Leveraged ETN")
                                           (asset
                                            "TECL"
                                            "Direxion Daily Technology Bull 3x Shares")])])])])]
                                  [(asset
                                    "BIL"
                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")])
                                 0.8
                                 (if
                                  (< (rsi "UNH" {:window 14}) 79)
                                  [(weight-equal
                                    [(if
                                      (>
                                       (max-drawdown "SPY" {:window 5})
                                       12)
                                      [(asset
                                        "BIL"
                                        "SPDR Bloomberg 1-3 Month T-Bill ETF")]
                                      [(weight-equal
                                        [(filter
                                          (cumulative-return
                                           {:window 30})
                                          (select-bottom 1)
                                          [(asset
                                            "TQQQ"
                                            "ProShares UltraPro QQQ")
                                           (asset
                                            "SPXL"
                                            "Direxion Daily S&P 500 Bull 3x Shares")
                                           (asset
                                            "SOXL"
                                            "Direxion Daily Semiconductor Bull 3x Shares")
                                           (asset
                                            "FNGU"
                                            "MicroSectors FANG+ Index 3X Leveraged ETN")
                                           (asset
                                            "TECL"
                                            "Direxion Daily Technology Bull 3x Shares")])])])])]
                                  [(asset
                                    "BIL"
                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")]))]))])])])])])])])])])])])])]
    [(group
      "WAM + Colonel Sanders ETF Only"
      [(weight-equal
        [(if
          (> (rsi "SPY" {:window 20}) (rsi "TFLO" {:window 20}))
          [(group
            "Colonel Sanders 21 Spices ?"
            [(weight-specified
              0.15
              (group
               "V1.4 [RSI 4d TLH UPRO] | ? Colonel Sanders 21 Spices | slowloss1 performance replica | HTX"
               [(weight-equal
                 [(if
                   (> (rsi "TLH" {:window 4}) (rsi "UPRO" {:window 4}))
                   [(weight-equal
                     [(if
                       (<
                        (rsi "BND" {:window 15})
                        (rsi "TQQQ" {:window 15}))
                       [(weight-equal
                         [(filter
                           (moving-average-return {:window 20})
                           (select-top 1)
                           [(asset
                             "SQQQ"
                             "ProShares UltraPro Short QQQ")
                            (asset
                             "FNGD"
                             "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                            (asset
                             "HIBS"
                             "Direxion Daily S&P 500 High Beta Bear 3X Shares")])])]
                       [(weight-equal
                         [(filter
                           (moving-average-return {:window 20})
                           (select-top 1)
                           [(asset "TQQQ" "ProShares UltraPro QQQ")
                            (asset
                             "SPXL"
                             "Direxion Daily S&P 500 Bull 3x Shares")
                            (asset
                             "FNGU"
                             "MicroSectors FANG+ Index 3X Leveraged ETN")
                            (asset
                             "SOXL"
                             "Direxion Daily Semiconductor Bull 3x Shares")
                            (asset
                             "HIBL"
                             "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])])])]
                   [(weight-equal
                     [(if
                       (>
                        (cumulative-return "SPHB" {:window 3})
                        (stdev-return "SPHB" {:window 9}))
                       [(weight-equal
                         [(filter
                           (moving-average-return {:window 20})
                           (select-top 1)
                           [(asset
                             "SQQQ"
                             "ProShares UltraPro Short QQQ")
                            (asset
                             "FNGD"
                             "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                            (asset
                             "HIBS"
                             "Direxion Daily S&P 500 High Beta Bear 3X Shares")])])]
                       [(weight-equal
                         [(filter
                           (moving-average-return {:window 20})
                           (select-top 1)
                           [(asset "TQQQ" "ProShares UltraPro QQQ")
                            (asset
                             "SPXL"
                             "Direxion Daily S&P 500 Bull 3x Shares")
                            (asset
                             "FNGU"
                             "MicroSectors FANG+ Index 3X Leveraged ETN")
                            (asset
                             "HIBL"
                             "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])])])])])])
              0.2
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
                       [(weight-equal
                         [(filter
                           (moving-average-return {:window 20})
                           (select-top 1)
                           [(asset
                             "SQQQ"
                             "ProShares UltraPro Short QQQ")
                            (asset
                             "FNGD"
                             "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                            (asset
                             "HIBS"
                             "Direxion Daily S&P 500 High Beta Bear 3X Shares")])])]
                       [(weight-equal
                         [(filter
                           (moving-average-return {:window 20})
                           (select-top 1)
                           [(asset "TQQQ" "ProShares UltraPro QQQ")
                            (asset
                             "SPXL"
                             "Direxion Daily S&P 500 Bull 3x Shares")
                            (asset
                             "FNGU"
                             "MicroSectors FANG+ Index 3X Leveraged ETN")
                            (asset
                             "SOXL"
                             "Direxion Daily Semiconductor Bull 3x Shares")
                            (asset
                             "HIBL"
                             "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])])])]
                   [(weight-equal
                     [(if
                       (>
                        (cumulative-return "SPHB" {:window 3})
                        (stdev-return "SPHB" {:window 9}))
                       [(weight-equal
                         [(filter
                           (moving-average-return {:window 20})
                           (select-top 1)
                           [(asset
                             "SQQQ"
                             "ProShares UltraPro Short QQQ")
                            (asset
                             "FNGD"
                             "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                            (asset
                             "HIBS"
                             "Direxion Daily S&P 500 High Beta Bear 3X Shares")])])]
                       [(weight-equal
                         [(filter
                           (moving-average-return {:window 20})
                           (select-top 1)
                           [(asset
                             "HIBL"
                             "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])])])])])])
              0.25
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
                       [(weight-equal
                         [(filter
                           (moving-average-return {:window 20})
                           (select-top 1)
                           [(asset
                             "SQQQ"
                             "ProShares UltraPro Short QQQ")
                            (asset
                             "FNGD"
                             "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                            (asset
                             "HIBS"
                             "Direxion Daily S&P 500 High Beta Bear 3X Shares")])])]
                       [(weight-equal
                         [(filter
                           (moving-average-return {:window 20})
                           (select-top 1)
                           [(asset "TQQQ" "ProShares UltraPro QQQ")
                            (asset
                             "SPXL"
                             "Direxion Daily S&P 500 Bull 3x Shares")
                            (asset
                             "FNGU"
                             "MicroSectors FANG+ Index 3X Leveraged ETN")
                            (asset
                             "SOXL"
                             "Direxion Daily Semiconductor Bull 3x Shares")
                            (asset
                             "HIBL"
                             "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])])])]
                   [(weight-equal
                     [(if
                       (>
                        (cumulative-return "SPHB" {:window 3})
                        (stdev-return "SPHB" {:window 9}))
                       [(weight-equal
                         [(filter
                           (moving-average-return {:window 20})
                           (select-top 1)
                           [(asset
                             "SQQQ"
                             "ProShares UltraPro Short QQQ")
                            (asset
                             "FNGD"
                             "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                            (asset
                             "HIBS"
                             "Direxion Daily S&P 500 High Beta Bear 3X Shares")])])]
                       [(asset
                         "HIBL"
                         "Direxion Daily S&P 500 High Beta Bull 3X Shares")])])])])])
              0.4
              (group
               "Growth Blend Retired"
               [(weight-equal
                 [(if
                   (>= (max-drawdown "SOXL" {:window 59}) 50)
                   [(weight-equal
                     [(if
                       (<= (rsi "TQQQ" {:window 60}) 55)
                       [(weight-equal
                         [(if
                           (<= (stdev-return "TQQQ" {:window 100}) 2)
                           [(weight-equal
                             [(filter
                               (cumulative-return {:window 15})
                               (select-top 1)
                               [(asset "TQQQ" "ProShares UltraPro QQQ")
                                (asset
                                 "SPXL"
                                 "Direxion Daily S&P 500 Bull 3x Shares")
                                (asset
                                 "FNGU"
                                 "MicroSectors FANG+ Index 3X Leveraged ETN")
                                (asset
                                 "TECL"
                                 "Direxion Daily Technology Bull 3x Shares")])])]
                           [(weight-equal
                             [(if
                               (>= (rsi "TQQQ" {:window 30}) 50)
                               [(weight-equal
                                 [(if
                                   (>=
                                    (stdev-return "TQQQ" {:window 30})
                                    7)
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "QQQ"
                                         {:window 5})
                                        -4)
                                       [(weight-equal
                                         [(filter
                                           (cumulative-return
                                            {:window 14})
                                           (select-top 1)
                                           [(asset
                                             "SOXL"
                                             "Direxion Daily Semiconductor Bull 3x Shares")
                                            (asset
                                             "GUSH"
                                             "Direxion Daily S&P Oil & Gas Exp. & Prod. Bull 2X Shares")
                                            (asset
                                             "FNGU"
                                             "MicroSectors FANG+ Index 3X Leveraged ETN")
                                            (asset
                                             "TECL"
                                             "Direxion Daily Technology Bull 3x Shares")])])]
                                       [(weight-equal
                                         [(filter
                                           (stdev-return {:window 8})
                                           (select-top 1)
                                           [(asset
                                             "SOXS"
                                             "Direxion Daily Semiconductor Bear 3x Shares")
                                            (asset
                                             "FNGD"
                                             "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                            (asset
                                             "TECS"
                                             "Direxion Daily Technology Bear 3X Shares")
                                            (asset
                                             "DRIP"
                                             "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")
                                            (asset
                                             "FAS"
                                             "Direxion Daily Financial Bull 3x Shares")])])])])]
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (cumulative-return
                                         "SOXL"
                                         {:window 10})
                                        1)
                                       [(weight-equal
                                         [(filter
                                           (stdev-return {:window 8})
                                           (select-top 1)
                                           [(asset
                                             "SOXS"
                                             "Direxion Daily Semiconductor Bear 3x Shares")
                                            (asset
                                             "FNGD"
                                             "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                            (asset
                                             "TECS"
                                             "Direxion Daily Technology Bear 3X Shares")
                                            (asset
                                             "DRIP"
                                             "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")
                                            (asset
                                             "FAS"
                                             "Direxion Daily Financial Bull 3x Shares")])])]
                                       [(weight-equal
                                         [(filter
                                           (cumulative-return
                                            {:window 14})
                                           (select-top 1)
                                           [(asset
                                             "SOXL"
                                             "Direxion Daily Semiconductor Bull 3x Shares")
                                            (asset
                                             "GUSH"
                                             "Direxion Daily S&P Oil & Gas Exp. & Prod. Bull 2X Shares")
                                            (asset
                                             "FNGU"
                                             "MicroSectors FANG+ Index 3X Leveraged ETN")
                                            (asset
                                             "TECL"
                                             "Direxion Daily Technology Bull 3x Shares")])])])])])])]
                               [(weight-equal
                                 [(if
                                   (<=
                                    (cumulative-return
                                     "TQQQ"
                                     {:window 8})
                                    -20)
                                   [(weight-equal
                                     [(filter
                                       (stdev-return {:window 9})
                                       (select-top 1)
                                       [(asset
                                         "SOXL"
                                         "Direxion Daily Semiconductor Bull 3x Shares")
                                        (asset
                                         "TQQQ"
                                         "ProShares UltraPro QQQ")
                                        (asset
                                         "FNGU"
                                         "MicroSectors FANG+ Index 3X Leveraged ETN")
                                        (asset
                                         "TECL"
                                         "Direxion Daily Technology Bull 3x Shares")])])]
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (max-drawdown
                                         "TQQQ"
                                         {:window 200})
                                        68)
                                       [(weight-equal
                                         [(filter
                                           (cumulative-return
                                            {:window 10})
                                           (select-bottom 1)
                                           [(asset
                                             "SOXS"
                                             "Direxion Daily Semiconductor Bear 3x Shares")
                                            (asset
                                             "FNGD"
                                             "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                            (asset
                                             "TECS"
                                             "Direxion Daily Technology Bear 3X Shares")
                                            (asset
                                             "DRIP"
                                             "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")])])]
                                       [(weight-equal
                                         [(filter
                                           (stdev-return {:window 5})
                                           (select-bottom 1)
                                           [(asset
                                             "SOXL"
                                             "Direxion Daily Semiconductor Bull 3x Shares")
                                            (asset
                                             "GUSH"
                                             "Direxion Daily S&P Oil & Gas Exp. & Prod. Bull 2X Shares")
                                            (asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")
                                            (asset
                                             "FNGU"
                                             "MicroSectors FANG+ Index 3X Leveraged ETN")
                                            (asset
                                             "TECL"
                                             "Direxion Daily Technology Bull 3x Shares")])])])])])])])])])])]
                       [(weight-equal
                         [(if
                           (>= (rsi "TQQQ" {:window 30}) 50)
                           [(weight-equal
                             [(if
                               (<=
                                (cumulative-return "SOXL" {:window 5})
                                -1)
                               [(weight-equal
                                 [(if
                                   (<=
                                    (stdev-return "SOXL" {:window 15})
                                    8)
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (stdev-return
                                         "SOXL"
                                         {:window 30})
                                        8)
                                       [(weight-equal
                                         [(filter
                                           (cumulative-return
                                            {:window 62})
                                           (select-top 1)
                                           [(asset
                                             "SOXL"
                                             "Direxion Daily Semiconductor Bull 3x Shares")
                                            (asset
                                             "FNGU"
                                             "MicroSectors FANG+ Index 3X Leveraged ETN")
                                            (asset
                                             "TECL"
                                             "Direxion Daily Technology Bull 3x Shares")
                                            (asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")
                                            (asset
                                             "SPXL"
                                             "Direxion Daily S&P 500 Bull 3x Shares")])])]
                                       [(weight-equal
                                         [(filter
                                           (cumulative-return
                                            {:window 60})
                                           (select-bottom 1)
                                           [(asset
                                             "FNGD"
                                             "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                            (asset
                                             "DRIP"
                                             "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")])])])])]
                                   [(weight-equal
                                     [(filter
                                       (cumulative-return {:window 60})
                                       (select-top 1)
                                       [(asset
                                         "FNGD"
                                         "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                        (asset
                                         "DRIP"
                                         "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")
                                        (asset
                                         "SOXS"
                                         "Direxion Daily Semiconductor Bear 3x Shares")])])])])]
                               [(weight-equal
                                 [(if
                                   (<=
                                    (cumulative-return
                                     "QQQ"
                                     {:window 5})
                                    -1)
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (stdev-return
                                         "SOXL"
                                         {:window 15})
                                        8)
                                       [(weight-equal
                                         [(if
                                           (<=
                                            (stdev-return
                                             "SOXL"
                                             {:window 30})
                                            8)
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 62})
                                               (select-top 1)
                                               [(asset
                                                 "SOXL"
                                                 "Direxion Daily Semiconductor Bull 3x Shares")
                                                (asset
                                                 "FNGU"
                                                 "MicroSectors FANG+ Index 3X Leveraged ETN")
                                                (asset
                                                 "TECL"
                                                 "Direxion Daily Technology Bull 3x Shares")
                                                (asset
                                                 "TQQQ"
                                                 "ProShares UltraPro QQQ")
                                                (asset
                                                 "SPXL"
                                                 "Direxion Daily S&P 500 Bull 3x Shares")])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 60})
                                               (select-top 1)
                                               [(asset
                                                 "FNGD"
                                                 "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                                (asset
                                                 "DRIP"
                                                 "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")])])])])]
                                       [(weight-equal
                                         [(filter
                                           (stdev-return {:window 8})
                                           (select-top 1)
                                           [(asset
                                             "SOXS"
                                             "Direxion Daily Semiconductor Bear 3x Shares")
                                            (asset
                                             "FNGD"
                                             "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                            (asset
                                             "TECS"
                                             "Direxion Daily Technology Bear 3X Shares")
                                            (asset
                                             "DRIP"
                                             "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")
                                            (asset
                                             "FAS"
                                             "Direxion Daily Financial Bull 3x Shares")])])])])]
                                   [(weight-equal
                                     [(filter
                                       (stdev-return {:window 8})
                                       (select-top 1)
                                       [(asset
                                         "SOXS"
                                         "Direxion Daily Semiconductor Bear 3x Shares")
                                        (asset
                                         "FNGD"
                                         "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                        (asset
                                         "TECS"
                                         "Direxion Daily Technology Bear 3X Shares")
                                        (asset
                                         "DRIP"
                                         "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")
                                        (asset
                                         "FAS"
                                         "Direxion Daily Financial Bull 3x Shares")])])])])])])]
                           [(weight-equal
                             [(if
                               (<=
                                (cumulative-return "QQQ" {:window 10})
                                2)
                               [(weight-equal
                                 [(filter
                                   (stdev-return {:window 8})
                                   (select-bottom 1)
                                   [(asset
                                     "SOXS"
                                     "Direxion Daily Semiconductor Bear 3x Shares")
                                    (asset
                                     "FNGD"
                                     "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                    (asset
                                     "TECS"
                                     "Direxion Daily Technology Bear 3X Shares")
                                    (asset
                                     "DRIP"
                                     "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")
                                    (asset
                                     "FAS"
                                     "Direxion Daily Financial Bull 3x Shares")])])]
                               [(weight-equal
                                 [(if
                                   (<=
                                    (stdev-return "SOXL" {:window 15})
                                    8)
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (stdev-return
                                         "SOXL"
                                         {:window 30})
                                        8)
                                       [(weight-equal
                                         [(filter
                                           (cumulative-return
                                            {:window 62})
                                           (select-top 1)
                                           [(asset
                                             "SOXL"
                                             "Direxion Daily Semiconductor Bull 3x Shares")
                                            (asset
                                             "FNGU"
                                             "MicroSectors FANG+ Index 3X Leveraged ETN")
                                            (asset
                                             "TECL"
                                             "Direxion Daily Technology Bull 3x Shares")
                                            (asset
                                             "TQQQ"
                                             "ProShares UltraPro QQQ")
                                            (asset
                                             "SPXL"
                                             "Direxion Daily S&P 500 Bull 3x Shares")])])]
                                       [(weight-equal
                                         [(filter
                                           (stdev-return {:window 30})
                                           (select-bottom 1)
                                           [(asset
                                             "SOXS"
                                             "Direxion Daily Semiconductor Bear 3x Shares")
                                            (asset
                                             "FNGD"
                                             "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                            (asset
                                             "TECS"
                                             "Direxion Daily Technology Bear 3X Shares")
                                            (asset
                                             "DRIP"
                                             "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")
                                            (asset
                                             "FAS"
                                             "Direxion Daily Financial Bull 3x Shares")])])])])]
                                   [(weight-equal
                                     [(filter
                                       (stdev-return {:window 30})
                                       (select-top 1)
                                       [(asset
                                         "SOXS"
                                         "Direxion Daily Semiconductor Bear 3x Shares")
                                        (asset
                                         "FNGD"
                                         "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                        (asset
                                         "TECS"
                                         "Direxion Daily Technology Bear 3X Shares")
                                        (asset
                                         "DRIP"
                                         "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")
                                        (asset
                                         "FAS"
                                         "Direxion Daily Financial Bull 3x Shares")])])])])])])])])])])]
                   [(weight-equal
                     [(if
                       (<= (rsi "SOXL" {:window 32}) 62.1995)
                       [(weight-equal
                         [(if
                           (<=
                            (stdev-return "SOXL" {:window 105})
                            4.9226)
                           [(weight-equal
                             [(if
                               (<=
                                (cumulative-return "QQQ" {:window 10})
                                2)
                               [(weight-equal
                                 [(filter
                                   (cumulative-return {:window 14})
                                   (select-top 1)
                                   [(asset
                                     "SOXL"
                                     "Direxion Daily Semiconductor Bull 3x Shares")
                                    (asset
                                     "GUSH"
                                     "Direxion Daily S&P Oil & Gas Exp. & Prod. Bull 2X Shares")
                                    (asset
                                     "FNGU"
                                     "MicroSectors FANG+ Index 3X Leveraged ETN")
                                    (asset
                                     "TECL"
                                     "Direxion Daily Technology Bull 3x Shares")])])]
                               [(weight-equal
                                 [(filter
                                   (stdev-return {:window 8})
                                   (select-top 1)
                                   [(asset
                                     "SOXS"
                                     "Direxion Daily Semiconductor Bear 3x Shares")
                                    (asset
                                     "FNGD"
                                     "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                    (asset
                                     "TECS"
                                     "Direxion Daily Technology Bear 3X Shares")
                                    (asset
                                     "DRIP"
                                     "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")
                                    (asset
                                     "FAS"
                                     "Direxion Daily Financial Bull 3x Shares")])])])])]
                           [(weight-equal
                             [(if
                               (>= (rsi "SOXL" {:window 30}) 57.49)
                               [(weight-equal
                                 [(if
                                   (>=
                                    (stdev-return "SOXL" {:window 30})
                                    5.4135)
                                   [(weight-equal
                                     [(filter
                                       (stdev-return {:window 15})
                                       (select-bottom 1)
                                       [(asset
                                         "SOXS"
                                         "Direxion Daily Semiconductor Bear 3x Shares")
                                        (asset
                                         "FNGD"
                                         "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                        (asset
                                         "TECS"
                                         "Direxion Daily Technology Bear 3X Shares")
                                        (asset
                                         "DRIP"
                                         "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")])])]
                                   [(weight-equal
                                     [(filter
                                       (cumulative-return {:window 14})
                                       (select-top 1)
                                       [(asset
                                         "SOXL"
                                         "Direxion Daily Semiconductor Bull 3x Shares")
                                        (asset
                                         "FNGU"
                                         "MicroSectors FANG+ Index 3X Leveraged ETN")
                                        (asset
                                         "TECL"
                                         "Direxion Daily Technology Bull 3x Shares")])])])])]
                               [(weight-equal
                                 [(if
                                   (<=
                                    (cumulative-return
                                     "SOXL"
                                     {:window 32})
                                    -10)
                                   [(weight-equal
                                     [(filter
                                       (cumulative-return {:window 14})
                                       (select-bottom 1)
                                       [(asset
                                         "SOXL"
                                         "Direxion Daily Semiconductor Bull 3x Shares")
                                        (asset
                                         "FNGU"
                                         "MicroSectors FANG+ Index 3X Leveraged ETN")])])]
                                   [(weight-equal
                                     [(if
                                       (<=
                                        (max-drawdown
                                         "SOXL"
                                         {:window 250})
                                        72)
                                       [(weight-equal
                                         [(filter
                                           (cumulative-return
                                            {:window 11})
                                           (select-bottom 1)
                                           [(asset
                                             "FNGD"
                                             "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                            (asset
                                             "DRIP"
                                             "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")])])]
                                       [(weight-equal
                                         [(if
                                           (<=
                                            (stdev-return
                                             "SOXL"
                                             {:window 15})
                                            8)
                                           [(weight-equal
                                             [(if
                                               (<=
                                                (stdev-return
                                                 "SOXL"
                                                 {:window 30})
                                                8)
                                               [(weight-equal
                                                 [(filter
                                                   (cumulative-return
                                                    {:window 60})
                                                   (select-top 1)
                                                   [(asset
                                                     "SOXL"
                                                     "Direxion Daily Semiconductor Bull 3x Shares")
                                                    (asset
                                                     "FNGU"
                                                     "MicroSectors FANG+ Index 3X Leveraged ETN")
                                                    (asset
                                                     "TECL"
                                                     "Direxion Daily Technology Bull 3x Shares")
                                                    (asset
                                                     "TQQQ"
                                                     "ProShares UltraPro QQQ")
                                                    (asset
                                                     "SPXL"
                                                     "Direxion Daily S&P 500 Bull 3x Shares")])])]
                                               [(weight-equal
                                                 [(filter
                                                   (cumulative-return
                                                    {:window 60})
                                                   (select-top 1)
                                                   [(asset
                                                     "FNGD"
                                                     "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                                    (asset
                                                     "DRIP"
                                                     "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")])])])])]
                                           [(weight-equal
                                             [(filter
                                               (cumulative-return
                                                {:window 60})
                                               (select-top 1)
                                               [(asset
                                                 "FNGD"
                                                 "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                                (asset
                                                 "DRIP"
                                                 "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")
                                                (asset
                                                 "SOXS"
                                                 "Direxion Daily Semiconductor Bear 3x Shares")])])])])])])])])])])])])]
                       [(weight-equal
                         [(if
                           (>= (rsi "SOXL" {:window 32}) 50)
                           [(weight-equal
                             [(filter
                               (cumulative-return {:window 20})
                               (select-bottom 1)
                               [(asset
                                 "FNGD"
                                 "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")
                                (asset
                                 "DRIP"
                                 "Direxion Daily S&P Oil & Gas Exp. & Prod. Bear 2X Shares")
                                (asset
                                 "SPXS"
                                 "Direxion Daily S&P 500 Bear 3x Shares")
                                (asset
                                 "SOXS"
                                 "Direxion Daily Semiconductor Bear 3x Shares")])])]
                           [(weight-equal
                             [(filter
                               (cumulative-return {:window 14})
                               (select-top 1)
                               [(asset
                                 "SOXL"
                                 "Direxion Daily Semiconductor Bull 3x Shares")
                                (asset
                                 "GUSH"
                                 "Direxion Daily S&P Oil & Gas Exp. & Prod. Bull 2X Shares")
                                (asset
                                 "FNGU"
                                 "MicroSectors FANG+ Index 3X Leveraged ETN")
                                (asset
                                 "TECL"
                                 "Direxion Daily Technology Bull 3x Shares")])])])])])])])])]))])]
          [(group
            "Wooden ARKK Machine 2.2b no IEF no TYO [RSI 10d SCHZ URTY]"
            [(weight-equal
              [(if
                (> (rsi "SCHZ" {:window 10}) (rsi "URTY" {:window 10}))
                [(weight-equal
                  [(filter
                    (moving-average-return {:window 4})
                    (select-bottom 1)
                    [(asset
                      "TECL"
                      "Direxion Daily Technology Bull 3x Shares")
                     (asset "URTY" "ProShares UltraPro Russell2000")
                     (asset
                      "TMF"
                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                     (asset
                      "YINN"
                      "Direxion Daily FTSE China Bull 3X Shares")
                     (asset
                      "EDC"
                      "Direxion Daily MSCI Emerging Markets Bull 3x Shares")
                     (asset "SOXX" "iShares Semiconductor ETF")
                     (asset
                      "LABU"
                      "Direxion Daily S&P Biotech Bull 3X Shares")
                     (asset
                      "HIBL"
                      "Direxion Daily S&P 500 High Beta Bull 3X Shares")
                     (asset
                      "FNGU"
                      "MicroSectors FANG+ Index 3X Leveraged ETN")
                     (asset
                      "SOXL"
                      "Direxion Daily Semiconductor Bull 3x Shares")
                     (asset
                      "TNA"
                      "Direxion Daily Small Cap Bull 3x Shares")
                     (asset
                      "MIDU"
                      "Direxion Daily Mid Cap Bull 3x Shares")
                     (asset
                      "EURL"
                      "Direxion Daily FTSE Europe Bull 3X Shares")
                     (asset
                      "NAIL"
                      "Direxion Daily Homebuilders & Supplies Bull 3X Shares")
                     (asset
                      "DFEN"
                      "Direxion Daily Aerospace & Defense Bull 3X Shares")])])]
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
                     (asset "SH" "ProShares Short S&P500")
                     (asset
                      "TYO"
                      "Direxion Daily 7-10 Year Treasury Bear 3x Shares")])])])])])])])])])]))
