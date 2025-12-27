(defsymphony
 "(A) Sisyphus V0.1 (309,7.4,2022) - Avoid High Vol"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
    (> (rsi "UVXY" {:window 21}) 62)
    [(weight-equal
      [(if
        (> (rsi "UVXY" {:window 10}) 74)
        [(weight-equal
          [(if
            (< (rsi "UVXY" {:window 10}) 84)
            [(weight-equal
              [(if
                (< (cumulative-return "UVXY" {:window 2}) 4.5)
                [(asset
                  "BIL"
                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")]
                [(asset
                  "BIL"
                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")
                 (asset
                  "SHV"
                  "BlackRock Institutional Trust Company N.A. - iShares Short Treasury Bond ETF")
                 (asset
                  "VIXY"
                  "ProShares Trust - ProShares VIX Short-Term Futures ETF")
                 (asset
                  "UVXY"
                  "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")
                 (asset
                  "BIL"
                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")
                 (asset
                  "BIL"
                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
            [(asset "BIL" "SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
        [(asset "BIL" "SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
    [(weight-equal
      [(group
        "Hg Short Only V0.2 (57,19,2011)"
        [(weight-equal
          [(if
            (>
             (current-price "SPY")
             (moving-average-price "SPY" {:window 200}))
            [(weight-equal
              [(if
                (> (rsi "QQQ" {:window 10}) 79)
                [(weight-equal
                  [(asset
                    "UVXY"
                    "ProShares Ultra VIX Short-Term Futures ETF")])]
                [(weight-equal
                  [(if
                    (> (rsi "SPY" {:window 10}) 79)
                    [(weight-equal
                      [(asset
                        "UVXY"
                        "ProShares Ultra VIX Short-Term Futures ETF")])]
                    [(weight-equal
                      [(if
                        (< (rsi "TQQQ" {:window 10}) 31)
                        [(weight-equal
                          [(asset
                            "TQQQ"
                            "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])]
                        [(weight-equal
                          [(if
                            (< (rsi "UPRO" {:window 10}) 31)
                            [(weight-equal
                              [(asset
                                "UPRO"
                                "ProShares Trust - ProShares UltraPro S&P 500 ETF 3x Shares")])]
                            [(asset
                              "BOND"
                              "Pimco Exchange Traded Fund - PIMCO Active Bond ETF")])])])])])])])])]
            [(weight-equal
              [(if
                (< (rsi "TQQQ" {:window 10}) 31)
                [(weight-equal
                  [(asset
                    "BIL"
                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                [(weight-equal
                  [(if
                    (< (rsi "UPRO" {:window 10}) 31)
                    [(weight-equal
                      [(asset
                        "BIL"
                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])]
                    [(weight-equal
                      [(if
                        (< (cumulative-return "TQQQ" {:window 6}) -11)
                        [(group
                          "Buy the dips. Sell the rips. V2"
                          [(weight-equal
                            [(if
                              (>
                               (cumulative-return "TQQQ" {:window 1})
                               5.5)
                              [(weight-equal
                                [(asset
                                  "UVXY"
                                  "ProShares Ultra VIX Short-Term Futures ETF")])]
                              [(weight-equal
                                [(asset
                                  "BOND"
                                  "Pimco Exchange Traded Fund - PIMCO Active Bond ETF")])])])])]
                        [(weight-equal
                          [(if
                            (>
                             (current-price "QLD")
                             (moving-average-price "QLD" {:window 20}))
                            [(weight-equal
                              [(asset
                                "BOND"
                                "Pimco Exchange Traded Fund - PIMCO Active Bond ETF")])]
                            [(weight-equal
                              [(if
                                (>
                                 (moving-average-return
                                  "TLT"
                                  {:window 20})
                                 (moving-average-return
                                  "UDN"
                                  {:window 20}))
                                [(weight-equal
                                  [(asset
                                    "SQQQ"
                                    "ProShares UltraPro Short QQQ")])]
                                [(weight-equal
                                  [(filter
                                    (rsi {:window 10})
                                    (select-bottom 1)
                                    [(asset
                                      "UUP"
                                      "Invesco DB US Dollar Index Bullish Fund")
                                     (asset
                                      "SQQQ"
                                      "ProShares UltraPro Short QQQ")])])])])])])])])])])])])])])])
       (group
        "HWRT 3 (225,19,2022)"
        [(weight-equal
          [(if
            (> (rsi "UVXY" {:window 21}) 65)
            [(weight-equal
              [(group
                "BSC 1"
                [(weight-equal
                  [(if
                    (> (rsi "SPY" {:window 21}) 30)
                    [(asset
                      "VIXM"
                      "ProShares VIX Mid-Term Futures ETF")]
                    [(asset
                      "SPXL"
                      "Direxion Daily S&P 500 Bull 3x Shares")])])])
               (group
                "BSC 2"
                [(weight-equal
                  [(if
                    (> (rsi "UVXY" {:window 10}) 74)
                    [(weight-equal
                      [(if
                        (< (rsi "UVXY" {:window 10}) 84)
                        [(asset
                          "UVXY"
                          "ProShares Ultra VIX Short-Term Futures ETF")]
                        [(asset
                          "BIL"
                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(asset
                      "BIL"
                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
            [(weight-equal
              [(group
                "High Win Rates + Anansi's Scale-in"
                [(weight-equal
                  [(if
                    (> (rsi "IOO" {:window 10}) 80)
                    [(group
                      "Scale-In | VIX+ -> VIX++"
                      [(weight-equal
                        [(if
                          (> (rsi "IOO" {:window 10}) 82.5)
                          [(group
                            "VIX Blend++"
                            [(weight-equal [(asset "UVXY" nil)])])]
                          [(group
                            "VIX Blend+"
                            [(weight-equal
                              [(asset
                                "VIXY"
                                "ProShares Trust - ProShares VIX Short-Term Futures ETF")])])])])])]
                    [(weight-equal
                      [(if
                        (> (rsi "TQQQ" {:window 10}) 81)
                        [(weight-equal
                          [(if
                            (> (rsi "UVXY" {:window 60}) 40)
                            [(asset "UVXY" nil)]
                            [(weight-equal
                              [(if
                                (> (rsi "RETL" {:window 10}) 82)
                                [(group
                                  "Scale-In | BTAL -> VIX"
                                  [(weight-equal
                                    [(if
                                      (> (rsi "RETL" {:window 10}) 85)
                                      [(group
                                        "VIX Blend"
                                        [(weight-equal
                                          [(asset "UVXY" nil)])])]
                                      [(group
                                        "BTAL/BIL"
                                        [(weight-equal
                                          [(asset "BTAL" nil)
                                           (asset "SHV" nil)])])])])])]
                                [(weight-equal
                                  [(if
                                    (> (rsi "XLF" {:window 10}) 81)
                                    [(group
                                      "Scale-In | VIX -> VIX+"
                                      [(weight-equal
                                        [(if
                                          (>
                                           (rsi "XLF" {:window 10})
                                           85)
                                          [(group
                                            "VIX Blend+"
                                            [(weight-equal
                                              [(asset "UVXY" nil)])])]
                                          [(group
                                            "VIX Blend"
                                            [(weight-equal
                                              [(asset
                                                "VIXY"
                                                "ProShares Trust - ProShares VIX Short-Term Futures ETF")])])])])])]
                                    [(weight-equal
                                      [(asset "SHV" nil)])])])])])])])]
                        [(weight-equal
                          [(if
                            (> (rsi "SPY" {:window 10}) 80)
                            [(weight-equal
                              [(if
                                (> (rsi "UVXY" {:window 60}) 40)
                                [(asset "UVXY" nil)]
                                [(weight-equal
                                  [(if
                                    (> (rsi "RETL" {:window 10}) 82)
                                    [(group
                                      "Scale-In | BTAL -> VIX"
                                      [(weight-equal
                                        [(if
                                          (>
                                           (rsi "RETL" {:window 10})
                                           85)
                                          [(group
                                            "VIX Blend"
                                            [(weight-equal
                                              [(asset "UVXY" nil)])])]
                                          [(group
                                            "BTAL/BIL"
                                            [(weight-equal
                                              [(asset "BTAL" nil)
                                               (asset
                                                "SHV"
                                                nil)])])])])])]
                                    [(weight-equal
                                      [(if
                                        (> (rsi "XLF" {:window 10}) 81)
                                        [(group
                                          "Scale-In | VIX -> VIX+"
                                          [(weight-equal
                                            [(if
                                              (>
                                               (rsi "XLF" {:window 10})
                                               85)
                                              [(group
                                                "VIX Blend+"
                                                [(weight-equal
                                                  [(asset
                                                    "UVXY"
                                                    nil)])])]
                                              [(group
                                                "VIX Blend"
                                                [(weight-equal
                                                  [(asset
                                                    "VIXY"
                                                    "ProShares Trust - ProShares VIX Short-Term Futures ETF")])])])])])]
                                        [(weight-equal
                                          [(asset
                                            "SHV"
                                            nil)])])])])])])])]
                            [(weight-equal
                              [(if
                                (> (rsi "TQQQ" {:window 14}) 80)
                                [(asset
                                  "TECS"
                                  "Direxion Daily Technology Bear 3X Shares")]
                                [(weight-equal
                                  [(if
                                    (> (rsi "SOXL" {:window 14}) 80)
                                    [(asset
                                      "SOXS"
                                      "Direxion Daily Semiconductor Bear 3x Shares")]
                                    [(weight-equal
                                      [(if
                                        (> (rsi "TMV" {:window 14}) 80)
                                        [(asset "TMF" nil)]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "SMH" {:window 10})
                                             80)
                                            [(asset
                                              "SOXS"
                                              "Direxion Daily Semiconductor Bear 3x Shares")]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "RETL"
                                                  {:window 10})
                                                 82)
                                                [(group
                                                  "Scale-In | BTAL -> VIX"
                                                  [(weight-equal
                                                    [(if
                                                      (>
                                                       (rsi
                                                        "RETL"
                                                        {:window 10})
                                                       85)
                                                      [(group
                                                        "VIX Blend"
                                                        [(weight-equal
                                                          [(asset
                                                            "UVXY"
                                                            nil)])])]
                                                      [(group
                                                        "BTAL/BIL"
                                                        [(weight-equal
                                                          [(asset
                                                            "BTAL"
                                                            nil)
                                                           (asset
                                                            "SHV"
                                                            nil)])])])])])]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "XLF"
                                                      {:window 10})
                                                     81)
                                                    [(group
                                                      "Scale-In | VIX -> VIX+"
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (rsi
                                                            "XLF"
                                                            {:window
                                                             10})
                                                           85)
                                                          [(group
                                                            "VIX Blend+"
                                                            [(weight-equal
                                                              [(asset
                                                                "UVXY"
                                                                nil)])])]
                                                          [(group
                                                            "VIX Blend"
                                                            [(weight-equal
                                                              [(asset
                                                                "UVXY"
                                                                nil)])])])])])]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "SPY"
                                                          {:window 10})
                                                         80)
                                                        [(group
                                                          "VIX Blend++"
                                                          [(weight-equal
                                                            [(asset
                                                              "UVXY"
                                                              nil)])])]
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "IOO"
                                                              {:window
                                                               10})
                                                             80)
                                                            [(group
                                                              "Scale-In | VIX+ -> VIX++"
                                                              [(weight-equal
                                                                [(if
                                                                  (>
                                                                   (rsi
                                                                    "IOO"
                                                                    {:window
                                                                     10})
                                                                   82.5)
                                                                  [(group
                                                                    "VIX Blend++"
                                                                    [(weight-equal
                                                                      [(asset
                                                                        "UVXY"
                                                                        nil)])])]
                                                                  [(group
                                                                    "VIX Blend+"
                                                                    [(weight-equal
                                                                      [(asset
                                                                        "UVXY"
                                                                        nil)])])])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (>
                                                                 (rsi
                                                                  "QQQ"
                                                                  {:window
                                                                   10})
                                                                 79)
                                                                [(group
                                                                  "Scale-In | VIX+ -> VIX++"
                                                                  [(weight-equal
                                                                    [(if
                                                                      (>
                                                                       (rsi
                                                                        "QQQ"
                                                                        {:window
                                                                         10})
                                                                       82.5)
                                                                      [(group
                                                                        "VIX Blend++"
                                                                        [(weight-equal
                                                                          [(asset
                                                                            "UVXY"
                                                                            nil)])])]
                                                                      [(group
                                                                        "VIX Blend+"
                                                                        [(weight-equal
                                                                          [(asset
                                                                            "UVXY"
                                                                            nil)])])])])])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "VTV"
                                                                      {:window
                                                                       10})
                                                                     79)
                                                                    [(group
                                                                      "VIX Blend"
                                                                      [(weight-equal
                                                                        [(asset
                                                                          "UVXY"
                                                                          nil)])])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (rsi
                                                                          "XLP"
                                                                          {:window
                                                                           10})
                                                                         77)
                                                                        [(group
                                                                          "VIX Blend"
                                                                          [(weight-equal
                                                                            [(asset
                                                                              "UVXY"
                                                                              nil)])])]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (rsi
                                                                              "XLF"
                                                                              {:window
                                                                               10})
                                                                             81)
                                                                            [(group
                                                                              "VIX Blend"
                                                                              [(weight-equal
                                                                                [(asset
                                                                                  "UVXY"
                                                                                  nil)])])]
                                                                            [(weight-equal
                                                                              [(if
                                                                                (>
                                                                                 (rsi
                                                                                  "SPY"
                                                                                  {:window
                                                                                   70})
                                                                                 62)
                                                                                [(group
                                                                                  "Overbought"
                                                                                  [(weight-equal
                                                                                    [(group
                                                                                      "15/15"
                                                                                      [(weight-equal
                                                                                        [(if
                                                                                          (>
                                                                                           (rsi
                                                                                            "AGG"
                                                                                            {:window
                                                                                             15})
                                                                                           (rsi
                                                                                            "QQQ"
                                                                                            {:window
                                                                                             15}))
                                                                                          [(group
                                                                                            "Ticker Mixer"
                                                                                            [(weight-equal
                                                                                              [(group
                                                                                                "Pick Top 3"
                                                                                                [(weight-equal
                                                                                                  [(filter
                                                                                                    (moving-average-return
                                                                                                     {:window
                                                                                                      15})
                                                                                                    (select-top
                                                                                                     3)
                                                                                                    [(asset
                                                                                                      "SPXL"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "TQQQ"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "TECL"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "SOXL"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "FNGG"
                                                                                                      "Direxion Shares ETF Trust - Direxion Daily NYSE FANG+ Bull 2X Shares")])])])
                                                                                               (asset
                                                                                                "TQQQ"
                                                                                                nil)])])]
                                                                                          [(group
                                                                                            "GLD/SLV/DBC"
                                                                                            [(weight-specified
                                                                                              0.5
                                                                                              (asset
                                                                                               "GLD"
                                                                                               nil)
                                                                                              0.25
                                                                                              (asset
                                                                                               "SLV"
                                                                                               nil)
                                                                                              0.25
                                                                                              (asset
                                                                                               "DBC"
                                                                                               nil))])])])])
                                                                                     (group
                                                                                      "VIX Stuff"
                                                                                      [(weight-equal
                                                                                        [(if
                                                                                          (>
                                                                                           (rsi
                                                                                            "QQQ"
                                                                                            {:window
                                                                                             90})
                                                                                           60)
                                                                                          [(asset
                                                                                            "UVXY"
                                                                                            nil)]
                                                                                          [(weight-equal
                                                                                            [(if
                                                                                              (>
                                                                                               (rsi
                                                                                                "QQQ"
                                                                                                {:window
                                                                                                 14})
                                                                                               80)
                                                                                              [(asset
                                                                                                "UVXY"
                                                                                                nil)]
                                                                                              [(weight-equal
                                                                                                [(if
                                                                                                  (>
                                                                                                   (rsi
                                                                                                    "QQQ"
                                                                                                    {:window
                                                                                                     5})
                                                                                                   90)
                                                                                                  [(asset
                                                                                                    "UVXY"
                                                                                                    nil)]
                                                                                                  [(weight-equal
                                                                                                    [(if
                                                                                                      (>
                                                                                                       (rsi
                                                                                                        "QQQ"
                                                                                                        {:window
                                                                                                         3})
                                                                                                       95)
                                                                                                      [(asset
                                                                                                        "UVXY"
                                                                                                        nil)]
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
                                                                                                            "SVXY"
                                                                                                            nil)]
                                                                                                          [(asset
                                                                                                            "SLV"
                                                                                                            nil)])])])])])])])])])])])])])]
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (>
                                                                                     (cumulative-return
                                                                                      "VIXY"
                                                                                      {:window
                                                                                       9})
                                                                                     20)
                                                                                    [(group
                                                                                      "High VIX"
                                                                                      [(weight-equal
                                                                                        [(if
                                                                                          (>
                                                                                           (current-price
                                                                                            "SPY")
                                                                                           (moving-average-price
                                                                                            "SPY"
                                                                                            {:window
                                                                                             200}))
                                                                                          [(weight-equal
                                                                                            [(if
                                                                                              (>
                                                                                               (rsi
                                                                                                "UVXY"
                                                                                                {:window
                                                                                                 21})
                                                                                               65)
                                                                                              [(weight-equal
                                                                                                [(group
                                                                                                  "BSC 31 RSI"
                                                                                                  [(weight-equal
                                                                                                    [(if
                                                                                                      (>
                                                                                                       (rsi
                                                                                                        "SPY"
                                                                                                        {:window
                                                                                                         10})
                                                                                                       31)
                                                                                                      [(weight-equal
                                                                                                        [(if
                                                                                                          (>
                                                                                                           (max-drawdown
                                                                                                            "SVXY"
                                                                                                            {:window
                                                                                                             5})
                                                                                                           15)
                                                                                                          [(group
                                                                                                            "UVIX Volatility"
                                                                                                            [(weight-specified
                                                                                                              0.1
                                                                                                              (asset
                                                                                                               "UVIX"
                                                                                                               "2x Long VIX Futures ETF")
                                                                                                              0.9
                                                                                                              (asset
                                                                                                               "BTAL"
                                                                                                               "AGF U.S. Market Neutral Anti-Beta Fund"))])]
                                                                                                          [(group
                                                                                                            "UVXY Volatility"
                                                                                                            [(weight-specified
                                                                                                              0.1
                                                                                                              (asset
                                                                                                               "UVXY"
                                                                                                               "ProShares Ultra VIX Short-Term Futures ETF")
                                                                                                              0.3
                                                                                                              (group
                                                                                                               "VIX Mix"
                                                                                                               [(weight-equal
                                                                                                                 [(filter
                                                                                                                   (moving-average-return
                                                                                                                    {:window
                                                                                                                     10})
                                                                                                                   (select-bottom
                                                                                                                    2)
                                                                                                                   [(asset
                                                                                                                     "SOXS"
                                                                                                                     "Direxion Daily Semiconductor Bear 3x Shares")
                                                                                                                    (asset
                                                                                                                     "TECS"
                                                                                                                     "Direxion Daily Technology Bear 3X Shares")
                                                                                                                    (asset
                                                                                                                     "SQQQ"
                                                                                                                     "ProShares UltraPro Short QQQ")
                                                                                                                    (asset
                                                                                                                     "OILD"
                                                                                                                     "MicroSectors Oil & Gas Exp. & Prod. -3x Inverse Leveraged ETN")
                                                                                                                    (asset
                                                                                                                     "TMV"
                                                                                                                     "Direxion Daily 20+ Year Treasury Bear 3x Shares")
                                                                                                                    (asset
                                                                                                                     "FAZ"
                                                                                                                     "Direxion Daily Financial Bear 3X Shares")
                                                                                                                    (asset
                                                                                                                     "DRV"
                                                                                                                     "Direxion Daily Real Estate Bear 3X Shares")
                                                                                                                    (asset
                                                                                                                     "EDZ"
                                                                                                                     "Direxion Daily MSCI Emerging Markets Bear 3X Shares")
                                                                                                                    (asset
                                                                                                                     "DXD"
                                                                                                                     "ProShares UltraShort Dow30")
                                                                                                                    (asset
                                                                                                                     "SPXS"
                                                                                                                     "Direxion Daily S&P 500 Bear 3x Shares")
                                                                                                                    (asset
                                                                                                                     "SDOW"
                                                                                                                     "ProShares UltraPro Short Dow30")
                                                                                                                    (asset
                                                                                                                     "FNGD"
                                                                                                                     "MicroSectors FANG+ Index -3X Inverse Leveraged ETN")])])])
                                                                                                              0.6
                                                                                                              (asset
                                                                                                               "BTAL"
                                                                                                               "AGF U.S. Market Neutral Anti-Beta Fund"))])])])]
                                                                                                      [(group
                                                                                                        "SVXY"
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (>
                                                                                                             (max-drawdown
                                                                                                              "SVXY"
                                                                                                              {:window
                                                                                                               3})
                                                                                                             20)
                                                                                                            [(group
                                                                                                              "Volmageddon Protection"
                                                                                                              [(weight-equal
                                                                                                                [(asset
                                                                                                                  "BTAL"
                                                                                                                  "AGF U.S. Market Neutral Anti-Beta Fund")
                                                                                                                 (asset
                                                                                                                  "USMV"
                                                                                                                  "iShares MSCI USA Min Vol Factor ETF")
                                                                                                                 (group
                                                                                                                  "SVIX/SVXY"
                                                                                                                  [(weight-equal
                                                                                                                    [(if
                                                                                                                      (>
                                                                                                                       (cumulative-return
                                                                                                                        "SVXY"
                                                                                                                        {:window
                                                                                                                         1})
                                                                                                                       5)
                                                                                                                      [(asset
                                                                                                                        "SVIX"
                                                                                                                        "-1x Short VIX Futures ETF")]
                                                                                                                      [(asset
                                                                                                                        "SVXY"
                                                                                                                        "ProShares Short VIX Short-Term Futures ETF")])])])])])]
                                                                                                            [(weight-equal
                                                                                                              [(if
                                                                                                                (>
                                                                                                                 (cumulative-return
                                                                                                                  "VIXY"
                                                                                                                  {:window
                                                                                                                   5})
                                                                                                                 45)
                                                                                                                [(asset
                                                                                                                  "SVIX"
                                                                                                                  "-1x Short VIX Futures ETF")]
                                                                                                                [(asset
                                                                                                                  "SVXY"
                                                                                                                  nil)
                                                                                                                 (group
                                                                                                                  "Inverse VIX Mix"
                                                                                                                  [(weight-equal
                                                                                                                    [(filter
                                                                                                                      (moving-average-return
                                                                                                                       {:window
                                                                                                                        10})
                                                                                                                      (select-bottom
                                                                                                                       2)
                                                                                                                      [(asset
                                                                                                                        "QLD"
                                                                                                                        "ProShares Ultra QQQ")
                                                                                                                       (asset
                                                                                                                        "UYG"
                                                                                                                        "ProShares Ultra Financials")
                                                                                                                       (asset
                                                                                                                        "SAA"
                                                                                                                        "ProShares Ultra SmallCap600")
                                                                                                                       (asset
                                                                                                                        "EFO"
                                                                                                                        "ProShares Ultra MSCI EAFE")
                                                                                                                       (asset
                                                                                                                        "SSO"
                                                                                                                        "ProShares Ultra S&P 500")
                                                                                                                       (asset
                                                                                                                        "UDOW"
                                                                                                                        "ProShares UltraPro Dow30")
                                                                                                                       (asset
                                                                                                                        "UWM"
                                                                                                                        "ProShares Ultra Russell2000")
                                                                                                                       (asset
                                                                                                                        "ROM"
                                                                                                                        "ProShares Ultra Technology")
                                                                                                                       (asset
                                                                                                                        "ERX"
                                                                                                                        "Direxion Daily Energy Bull 2x Shares")])])])])])])])])])])])])]
                                                                                              [(weight-equal
                                                                                                [(group
                                                                                                  "SVXY"
                                                                                                  [(weight-equal
                                                                                                    [(if
                                                                                                      (>
                                                                                                       (max-drawdown
                                                                                                        "SVXY"
                                                                                                        {:window
                                                                                                         3})
                                                                                                       20)
                                                                                                      [(group
                                                                                                        "Volmageddon Protection"
                                                                                                        [(weight-equal
                                                                                                          [(asset
                                                                                                            "BTAL"
                                                                                                            "AGF U.S. Market Neutral Anti-Beta Fund")
                                                                                                           (asset
                                                                                                            "USMV"
                                                                                                            "iShares MSCI USA Min Vol Factor ETF")
                                                                                                           (group
                                                                                                            "SVIX/SVXY"
                                                                                                            [(weight-equal
                                                                                                              [(if
                                                                                                                (>
                                                                                                                 (cumulative-return
                                                                                                                  "SVXY"
                                                                                                                  {:window
                                                                                                                   1})
                                                                                                                 5)
                                                                                                                [(asset
                                                                                                                  "SVIX"
                                                                                                                  "-1x Short VIX Futures ETF")]
                                                                                                                [(asset
                                                                                                                  "SVXY"
                                                                                                                  "ProShares Short VIX Short-Term Futures ETF")])])])])])]
                                                                                                      [(weight-equal
                                                                                                        [(if
                                                                                                          (>
                                                                                                           (cumulative-return
                                                                                                            "VIXY"
                                                                                                            {:window
                                                                                                             5})
                                                                                                           45)
                                                                                                          [(asset
                                                                                                            "SVIX"
                                                                                                            "-1x Short VIX Futures ETF")]
                                                                                                          [(asset
                                                                                                            "SVXY"
                                                                                                            nil)
                                                                                                           (group
                                                                                                            "Inverse VIX Mix"
                                                                                                            [(weight-equal
                                                                                                              [(filter
                                                                                                                (moving-average-return
                                                                                                                 {:window
                                                                                                                  10})
                                                                                                                (select-bottom
                                                                                                                 2)
                                                                                                                [(asset
                                                                                                                  "QLD"
                                                                                                                  "ProShares Ultra QQQ")
                                                                                                                 (asset
                                                                                                                  "UYG"
                                                                                                                  "ProShares Ultra Financials")
                                                                                                                 (asset
                                                                                                                  "SAA"
                                                                                                                  "ProShares Ultra SmallCap600")
                                                                                                                 (asset
                                                                                                                  "EFO"
                                                                                                                  "ProShares Ultra MSCI EAFE")
                                                                                                                 (asset
                                                                                                                  "SSO"
                                                                                                                  "ProShares Ultra S&P 500")
                                                                                                                 (asset
                                                                                                                  "UDOW"
                                                                                                                  "ProShares UltraPro Dow30")
                                                                                                                 (asset
                                                                                                                  "UWM"
                                                                                                                  "ProShares Ultra Russell2000")
                                                                                                                 (asset
                                                                                                                  "ROM"
                                                                                                                  "ProShares Ultra Technology")
                                                                                                                 (asset
                                                                                                                  "ERX"
                                                                                                                  "Direxion Daily Energy Bull 2x Shares")])])])])])])])])])])])]
                                                                                          [(weight-equal
                                                                                            [(if
                                                                                              (<
                                                                                               (rsi
                                                                                                "TQQQ"
                                                                                                {:window
                                                                                                 10})
                                                                                               31)
                                                                                              [(group
                                                                                                "Pick Bottom 3 | 1.5x"
                                                                                                [(weight-equal
                                                                                                  [(filter
                                                                                                    (moving-average-return
                                                                                                     {:window
                                                                                                      10})
                                                                                                    (select-bottom
                                                                                                     3)
                                                                                                    [(asset
                                                                                                      "SPXL"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "TQQQ"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "TECL"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "SOXL"
                                                                                                      nil)])
                                                                                                   (filter
                                                                                                    (moving-average-return
                                                                                                     {:window
                                                                                                      10})
                                                                                                    (select-bottom
                                                                                                     3)
                                                                                                    [(asset
                                                                                                      "SPY"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "QQQ"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "XLK"
                                                                                                      nil)
                                                                                                     (asset
                                                                                                      "SOXX"
                                                                                                      nil)])])])]
                                                                                              [(weight-equal
                                                                                                [(if
                                                                                                  (>
                                                                                                   (cumulative-return
                                                                                                    "VIXY"
                                                                                                    {:window
                                                                                                     10})
                                                                                                   25)
                                                                                                  [(group
                                                                                                    "Volmageddon Protection"
                                                                                                    [(weight-equal
                                                                                                      [(asset
                                                                                                        "BTAL"
                                                                                                        "AGF U.S. Market Neutral Anti-Beta Fund")
                                                                                                       (asset
                                                                                                        "USMV"
                                                                                                        "iShares MSCI USA Min Vol Factor ETF")])])]
                                                                                                  [(group
                                                                                                    "Inverse VIX Mix"
                                                                                                    [(weight-equal
                                                                                                      [(filter
                                                                                                        (moving-average-return
                                                                                                         {:window
                                                                                                          10})
                                                                                                        (select-bottom
                                                                                                         2)
                                                                                                        [(asset
                                                                                                          "QLD"
                                                                                                          "ProShares Ultra QQQ")
                                                                                                         (asset
                                                                                                          "UYG"
                                                                                                          "ProShares Ultra Financials")
                                                                                                         (asset
                                                                                                          "SAA"
                                                                                                          "ProShares Ultra SmallCap600")
                                                                                                         (asset
                                                                                                          "EFO"
                                                                                                          "ProShares Ultra MSCI EAFE")
                                                                                                         (asset
                                                                                                          "SSO"
                                                                                                          "ProShares Ultra S&P 500")
                                                                                                         (asset
                                                                                                          "UDOW"
                                                                                                          "ProShares UltraPro Dow30")
                                                                                                         (asset
                                                                                                          "UWM"
                                                                                                          "ProShares Ultra Russell2000")
                                                                                                         (asset
                                                                                                          "ROM"
                                                                                                          "ProShares Ultra Technology")
                                                                                                         (asset
                                                                                                          "ERX"
                                                                                                          "Direxion Daily Energy Bull 2x Shares")])])])])])])])])])])]
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (current-price
                                                                                          "SPY")
                                                                                         (moving-average-price
                                                                                          "SPY"
                                                                                          {:window
                                                                                           200}))
                                                                                        [(weight-equal
                                                                                          [(if
                                                                                            (<
                                                                                             (rsi
                                                                                              "SOXL"
                                                                                              {:window
                                                                                               14})
                                                                                             30)
                                                                                            [(asset
                                                                                              "SOXL"
                                                                                              "Direxion Daily Semiconductor Bull 3x Shares")]
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (<
                                                                                                 (rsi
                                                                                                  "TECL"
                                                                                                  {:window
                                                                                                   14})
                                                                                                 30)
                                                                                                [(asset
                                                                                                  "TECL"
                                                                                                  "Direxion Daily Technology Bull 3x Shares")]
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (<
                                                                                                     (rsi
                                                                                                      "LABU"
                                                                                                      {:window
                                                                                                       10})
                                                                                                     22)
                                                                                                    [(weight-equal
                                                                                                      [(filter
                                                                                                        (cumulative-return
                                                                                                         {:window
                                                                                                          1})
                                                                                                        (select-bottom
                                                                                                         1)
                                                                                                        [(asset
                                                                                                          "LABU"
                                                                                                          "Direxion Daily S&P Biotech Bull 3X Shares")
                                                                                                         (asset
                                                                                                          "SOXL"
                                                                                                          "Direxion Daily Semiconductor Bull 3x Shares")])])]
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (<
                                                                                                         (rsi
                                                                                                          "QQQ"
                                                                                                          {:window
                                                                                                           14})
                                                                                                         30)
                                                                                                        [(asset
                                                                                                          "TECL"
                                                                                                          "Direxion Daily Technology Bull 3x Shares")]
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (<
                                                                                                             (rsi
                                                                                                              "SMH"
                                                                                                              {:window
                                                                                                               10})
                                                                                                             25)
                                                                                                            [(asset
                                                                                                              "SOXL"
                                                                                                              "Direxion Daily Semiconductor Bull 3x Shares")]
                                                                                                            [(weight-equal
                                                                                                              [(group
                                                                                                                "EM Emerging Markets V0.4 (114,69,2009)"
                                                                                                                [(weight-equal
                                                                                                                  [(if
                                                                                                                    (<
                                                                                                                     (rsi
                                                                                                                      "EEM"
                                                                                                                      {:window
                                                                                                                       15})
                                                                                                                     30)
                                                                                                                    [(asset
                                                                                                                      "EDC"
                                                                                                                      "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")]
                                                                                                                    [(weight-equal
                                                                                                                      [(if
                                                                                                                        (>
                                                                                                                         (current-price
                                                                                                                          "SHV")
                                                                                                                         (moving-average-price
                                                                                                                          "SHV"
                                                                                                                          {:window
                                                                                                                           50}))
                                                                                                                        [(weight-equal
                                                                                                                          [(if
                                                                                                                            (>
                                                                                                                             (current-price
                                                                                                                              "EEM")
                                                                                                                             (moving-average-price
                                                                                                                              "EEM"
                                                                                                                              {:window
                                                                                                                               200}))
                                                                                                                            [(group
                                                                                                                              "IEI vs IWM"
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (>
                                                                                                                                   (rsi
                                                                                                                                    "IEI"
                                                                                                                                    {:window
                                                                                                                                     10})
                                                                                                                                   (rsi
                                                                                                                                    "IWM"
                                                                                                                                    {:window
                                                                                                                                     15}))
                                                                                                                                  [(asset
                                                                                                                                    "EDC"
                                                                                                                                    "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")]
                                                                                                                                  [(asset
                                                                                                                                    "EDZ"
                                                                                                                                    "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")])])])]
                                                                                                                            [(group
                                                                                                                              "IGIB vs EEM"
                                                                                                                              [(weight-equal
                                                                                                                                [(if
                                                                                                                                  (>
                                                                                                                                   (rsi
                                                                                                                                    "IGIB"
                                                                                                                                    {:window
                                                                                                                                     15})
                                                                                                                                   (rsi
                                                                                                                                    "EEM"
                                                                                                                                    {:window
                                                                                                                                     15}))
                                                                                                                                  [(asset
                                                                                                                                    "EDC"
                                                                                                                                    "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")]
                                                                                                                                  [(asset
                                                                                                                                    "EDZ"
                                                                                                                                    "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")])])])])])]
                                                                                                                        [(group
                                                                                                                          "IGIB vs SPY"
                                                                                                                          [(weight-equal
                                                                                                                            [(if
                                                                                                                              (>
                                                                                                                               (rsi
                                                                                                                                "IGIB"
                                                                                                                                {:window
                                                                                                                                 10})
                                                                                                                               (rsi
                                                                                                                                "SPY"
                                                                                                                                {:window
                                                                                                                                 10}))
                                                                                                                              [(asset
                                                                                                                                "EEM"
                                                                                                                                nil)]
                                                                                                                              [(asset
                                                                                                                                "EDZ"
                                                                                                                                "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")])])])])])])])])
                                                                                                               (group
                                                                                                                "QQQ FTLT SMA V0.1 - (183,39,2011)"
                                                                                                                [(weight-equal
                                                                                                                  [(group
                                                                                                                    "QQQ FTLT SMA V0.1 - (183,39,2011)"
                                                                                                                    [(weight-equal
                                                                                                                      [(group
                                                                                                                        "Over bought"
                                                                                                                        [(weight-equal
                                                                                                                          [(if
                                                                                                                            (>
                                                                                                                             (rsi
                                                                                                                              "SPY"
                                                                                                                              {:window
                                                                                                                               10})
                                                                                                                             80)
                                                                                                                            [(asset
                                                                                                                              "UVXY"
                                                                                                                              nil)]
                                                                                                                            [(weight-equal
                                                                                                                              [(if
                                                                                                                                (>
                                                                                                                                 (rsi
                                                                                                                                  "QQQ"
                                                                                                                                  {:window
                                                                                                                                   10})
                                                                                                                                 79)
                                                                                                                                [(asset
                                                                                                                                  "UVXY"
                                                                                                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                                                                [(weight-equal
                                                                                                                                  [(if
                                                                                                                                    (>
                                                                                                                                     (rsi
                                                                                                                                      "VTV"
                                                                                                                                      {:window
                                                                                                                                       10})
                                                                                                                                     79)
                                                                                                                                    [(asset
                                                                                                                                      "UVXY"
                                                                                                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                                                                    [(weight-equal
                                                                                                                                      [(if
                                                                                                                                        (>
                                                                                                                                         (rsi
                                                                                                                                          "VOX"
                                                                                                                                          {:window
                                                                                                                                           10})
                                                                                                                                         79)
                                                                                                                                        [(asset
                                                                                                                                          "UVXY"
                                                                                                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                                                                        [(weight-equal
                                                                                                                                          [(if
                                                                                                                                            (>
                                                                                                                                             (rsi
                                                                                                                                              "XLK"
                                                                                                                                              {:window
                                                                                                                                               10})
                                                                                                                                             79)
                                                                                                                                            [(asset
                                                                                                                                              "UVXY"
                                                                                                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                                                                            [(weight-equal
                                                                                                                                              [(if
                                                                                                                                                (>
                                                                                                                                                 (rsi
                                                                                                                                                  "XLP"
                                                                                                                                                  {:window
                                                                                                                                                   10})
                                                                                                                                                 75)
                                                                                                                                                [(asset
                                                                                                                                                  "VIXY"
                                                                                                                                                  "ProShares VIX Short-Term Futures ETF")]
                                                                                                                                                [(weight-equal
                                                                                                                                                  [(if
                                                                                                                                                    (>
                                                                                                                                                     (rsi
                                                                                                                                                      "XLF"
                                                                                                                                                      {:window
                                                                                                                                                       10})
                                                                                                                                                     80)
                                                                                                                                                    [(asset
                                                                                                                                                      "UVXY"
                                                                                                                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                                                                                    [(group
                                                                                                                                                      "Vol Check"
                                                                                                                                                      [(weight-equal
                                                                                                                                                        [(if
                                                                                                                                                          (>
                                                                                                                                                           (rsi
                                                                                                                                                            "UVXY"
                                                                                                                                                            {:window
                                                                                                                                                             21})
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
                                                                                                                                                                  [(asset
                                                                                                                                                                    "VIXM"
                                                                                                                                                                    "ProShares VIX Mid-Term Futures ETF")]
                                                                                                                                                                  [(asset
                                                                                                                                                                    "SPXL"
                                                                                                                                                                    "Direxion Daily S&P 500 Bull 3x Shares")])])])])]
                                                                                                                                                          [(group
                                                                                                                                                            "Vix Low"
                                                                                                                                                            [(weight-equal
                                                                                                                                                              [(if
                                                                                                                                                                (<
                                                                                                                                                                 (rsi
                                                                                                                                                                  "SOXX"
                                                                                                                                                                  {:window
                                                                                                                                                                   10})
                                                                                                                                                                 30)
                                                                                                                                                                [(asset
                                                                                                                                                                  "SOXL"
                                                                                                                                                                  nil)]
                                                                                                                                                                [(weight-equal
                                                                                                                                                                  [(if
                                                                                                                                                                    (<
                                                                                                                                                                     (rsi
                                                                                                                                                                      "QQQ"
                                                                                                                                                                      {:window
                                                                                                                                                                       10})
                                                                                                                                                                     30)
                                                                                                                                                                    [(asset
                                                                                                                                                                      "TECL"
                                                                                                                                                                      nil)]
                                                                                                                                                                    [(weight-equal
                                                                                                                                                                      [(if
                                                                                                                                                                        (<
                                                                                                                                                                         (rsi
                                                                                                                                                                          "SPY"
                                                                                                                                                                          {:window
                                                                                                                                                                           10})
                                                                                                                                                                         30)
                                                                                                                                                                        [(asset
                                                                                                                                                                          "UPRO"
                                                                                                                                                                          nil)]
                                                                                                                                                                        [(weight-equal
                                                                                                                                                                          [(if
                                                                                                                                                                            (>
                                                                                                                                                                             (rsi
                                                                                                                                                                              "SPY"
                                                                                                                                                                              {:window
                                                                                                                                                                               70})
                                                                                                                                                                             60)
                                                                                                                                                                            [(weight-equal
                                                                                                                                                                              [(filter
                                                                                                                                                                                (rsi
                                                                                                                                                                                 {:window
                                                                                                                                                                                  10})
                                                                                                                                                                                (select-bottom
                                                                                                                                                                                 1)
                                                                                                                                                                                [(asset
                                                                                                                                                                                  "UGE"
                                                                                                                                                                                  "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                                                                                                                                 (asset
                                                                                                                                                                                  "BOND"
                                                                                                                                                                                  "Invesco Bond Fund")])])]
                                                                                                                                                                            [(weight-equal
                                                                                                                                                                              [(if
                                                                                                                                                                                (<
                                                                                                                                                                                 (cumulative-return
                                                                                                                                                                                  "QQQ"
                                                                                                                                                                                  {:window
                                                                                                                                                                                   5})
                                                                                                                                                                                 -5)
                                                                                                                                                                                [(group
                                                                                                                                                                                  "Oversold"
                                                                                                                                                                                  [(weight-equal
                                                                                                                                                                                    [(if
                                                                                                                                                                                      (<
                                                                                                                                                                                       (rsi
                                                                                                                                                                                        "SPY"
                                                                                                                                                                                        {:window
                                                                                                                                                                                         10})
                                                                                                                                                                                       35)
                                                                                                                                                                                      [(weight-equal
                                                                                                                                                                                        [(asset
                                                                                                                                                                                          "TQQQ"
                                                                                                                                                                                          "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])]
                                                                                                                                                                                      [(weight-equal
                                                                                                                                                                                        [(filter
                                                                                                                                                                                          (rsi
                                                                                                                                                                                           {:window
                                                                                                                                                                                            10})
                                                                                                                                                                                          (select-bottom
                                                                                                                                                                                           1)
                                                                                                                                                                                          [(asset
                                                                                                                                                                                            "UGE"
                                                                                                                                                                                            "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                                                                                                                                           (asset
                                                                                                                                                                                            "BOND"
                                                                                                                                                                                            "Invesco Bond Fund")])])])])])]
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
                                                                                                                                                                                           (current-price
                                                                                                                                                                                            "QQQ")
                                                                                                                                                                                           (moving-average-price
                                                                                                                                                                                            "QQQ"
                                                                                                                                                                                            {:window
                                                                                                                                                                                             30}))
                                                                                                                                                                                          [(weight-equal
                                                                                                                                                                                            [(asset
                                                                                                                                                                                              "TQQQ"
                                                                                                                                                                                              "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])]
                                                                                                                                                                                          [(weight-equal
                                                                                                                                                                                            [(if
                                                                                                                                                                                              (>
                                                                                                                                                                                               (cumulative-return
                                                                                                                                                                                                "QQQ"
                                                                                                                                                                                                {:window
                                                                                                                                                                                                 20})
                                                                                                                                                                                               (moving-average-return
                                                                                                                                                                                                "QQQ"
                                                                                                                                                                                                {:window
                                                                                                                                                                                                 10}))
                                                                                                                                                                                              [(weight-equal
                                                                                                                                                                                                [(filter
                                                                                                                                                                                                  (rsi
                                                                                                                                                                                                   {:window
                                                                                                                                                                                                    10})
                                                                                                                                                                                                  (select-bottom
                                                                                                                                                                                                   1)
                                                                                                                                                                                                  [(asset
                                                                                                                                                                                                    "UPRO"
                                                                                                                                                                                                    "ProShares Trust - ProShares UltraPro S&P 500 ETF 3x Shares")
                                                                                                                                                                                                   (asset
                                                                                                                                                                                                    "TQQQ"
                                                                                                                                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])]
                                                                                                                                                                                              [(weight-equal
                                                                                                                                                                                                [(filter
                                                                                                                                                                                                  (rsi
                                                                                                                                                                                                   {:window
                                                                                                                                                                                                    10})
                                                                                                                                                                                                  (select-bottom
                                                                                                                                                                                                   1)
                                                                                                                                                                                                  [(asset
                                                                                                                                                                                                    "UGE"
                                                                                                                                                                                                    "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                                                                                                                                                   (asset
                                                                                                                                                                                                    "BOND"
                                                                                                                                                                                                    "Invesco Bond Fund")])])])])])])])]
                                                                                                                                                                                    [(group
                                                                                                                                                                                      "Bear"
                                                                                                                                                                                      [(weight-equal
                                                                                                                                                                                        [(filter
                                                                                                                                                                                          (rsi
                                                                                                                                                                                           {:window
                                                                                                                                                                                            10})
                                                                                                                                                                                          (select-bottom
                                                                                                                                                                                           1)
                                                                                                                                                                                          [(asset
                                                                                                                                                                                            "UGE"
                                                                                                                                                                                            "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                                                                                                                                           (asset
                                                                                                                                                                                            "BOND"
                                                                                                                                                                                            "Invesco Bond Fund")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
                                                                                                               (group
                                                                                                                "QQQ FTLT Bonds - V0.5 - (237,33,2011)"
                                                                                                                [(weight-equal
                                                                                                                  [(if
                                                                                                                    (>
                                                                                                                     (rsi
                                                                                                                      "SPY"
                                                                                                                      {:window
                                                                                                                       10})
                                                                                                                     80)
                                                                                                                    [(asset
                                                                                                                      "UVXY"
                                                                                                                      nil)]
                                                                                                                    [(weight-equal
                                                                                                                      [(if
                                                                                                                        (>
                                                                                                                         (rsi
                                                                                                                          "QQQ"
                                                                                                                          {:window
                                                                                                                           10})
                                                                                                                         79)
                                                                                                                        [(asset
                                                                                                                          "UVXY"
                                                                                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                                                        [(weight-equal
                                                                                                                          [(if
                                                                                                                            (>
                                                                                                                             (rsi
                                                                                                                              "VTV"
                                                                                                                              {:window
                                                                                                                               10})
                                                                                                                             79)
                                                                                                                            [(asset
                                                                                                                              "UVXY"
                                                                                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                                                            [(weight-equal
                                                                                                                              [(if
                                                                                                                                (>
                                                                                                                                 (rsi
                                                                                                                                  "VOX"
                                                                                                                                  {:window
                                                                                                                                   10})
                                                                                                                                 79)
                                                                                                                                [(asset
                                                                                                                                  "UVXY"
                                                                                                                                  "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                                                                [(weight-equal
                                                                                                                                  [(if
                                                                                                                                    (>
                                                                                                                                     (rsi
                                                                                                                                      "XLK"
                                                                                                                                      {:window
                                                                                                                                       10})
                                                                                                                                     79)
                                                                                                                                    [(asset
                                                                                                                                      "UVXY"
                                                                                                                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                                                                    [(weight-equal
                                                                                                                                      [(if
                                                                                                                                        (>
                                                                                                                                         (rsi
                                                                                                                                          "XLP"
                                                                                                                                          {:window
                                                                                                                                           10})
                                                                                                                                         75)
                                                                                                                                        [(asset
                                                                                                                                          "VIXY"
                                                                                                                                          "ProShares VIX Short-Term Futures ETF")]
                                                                                                                                        [(weight-equal
                                                                                                                                          [(if
                                                                                                                                            (>
                                                                                                                                             (rsi
                                                                                                                                              "XLF"
                                                                                                                                              {:window
                                                                                                                                               10})
                                                                                                                                             80)
                                                                                                                                            [(asset
                                                                                                                                              "UVXY"
                                                                                                                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                                                                                            [(group
                                                                                                                                              "Vol Check"
                                                                                                                                              [(weight-equal
                                                                                                                                                [(if
                                                                                                                                                  (>
                                                                                                                                                   (rsi
                                                                                                                                                    "UVXY"
                                                                                                                                                    {:window
                                                                                                                                                     21})
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
                                                                                                                                                          [(asset
                                                                                                                                                            "VIXM"
                                                                                                                                                            "ProShares VIX Mid-Term Futures ETF")]
                                                                                                                                                          [(asset
                                                                                                                                                            "SPXL"
                                                                                                                                                            "Direxion Daily S&P 500 Bull 3x Shares")])])])])]
                                                                                                                                                  [(group
                                                                                                                                                    "Vix Low"
                                                                                                                                                    [(weight-equal
                                                                                                                                                      [(if
                                                                                                                                                        (<
                                                                                                                                                         (rsi
                                                                                                                                                          "SOXX"
                                                                                                                                                          {:window
                                                                                                                                                           10})
                                                                                                                                                         30)
                                                                                                                                                        [(asset
                                                                                                                                                          "SOXL"
                                                                                                                                                          nil)]
                                                                                                                                                        [(weight-equal
                                                                                                                                                          [(if
                                                                                                                                                            (<
                                                                                                                                                             (rsi
                                                                                                                                                              "QQQ"
                                                                                                                                                              {:window
                                                                                                                                                               10})
                                                                                                                                                             30)
                                                                                                                                                            [(asset
                                                                                                                                                              "TECL"
                                                                                                                                                              nil)]
                                                                                                                                                            [(weight-equal
                                                                                                                                                              [(if
                                                                                                                                                                (<
                                                                                                                                                                 (rsi
                                                                                                                                                                  "SPY"
                                                                                                                                                                  {:window
                                                                                                                                                                   10})
                                                                                                                                                                 30)
                                                                                                                                                                [(asset
                                                                                                                                                                  "UPRO"
                                                                                                                                                                  nil)]
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
                                                                                                                                                                          [(weight-equal
                                                                                                                                                                            [(if
                                                                                                                                                                              (>
                                                                                                                                                                               (moving-average-return
                                                                                                                                                                                "SPY"
                                                                                                                                                                                {:window
                                                                                                                                                                                 15})
                                                                                                                                                                               (moving-average-return
                                                                                                                                                                                "SPY"
                                                                                                                                                                                {:window
                                                                                                                                                                                 30}))
                                                                                                                                                                              [(asset
                                                                                                                                                                                "TQQQ"
                                                                                                                                                                                "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                                                                                                                                              [(weight-equal
                                                                                                                                                                                [(filter
                                                                                                                                                                                  (rsi
                                                                                                                                                                                   {:window
                                                                                                                                                                                    10})
                                                                                                                                                                                  (select-bottom
                                                                                                                                                                                   1)
                                                                                                                                                                                  [(asset
                                                                                                                                                                                    "UGE"
                                                                                                                                                                                    "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                                                                                                                                   (asset
                                                                                                                                                                                    "BOND"
                                                                                                                                                                                    "Invesco Bond Fund")])])])])]
                                                                                                                                                                          [(asset
                                                                                                                                                                            "PSQ"
                                                                                                                                                                            "ProShares Trust - ProShares Short QQQ -1x Shares")])])])]
                                                                                                                                                                    [(weight-equal
                                                                                                                                                                      [(if
                                                                                                                                                                        (<
                                                                                                                                                                         (cumulative-return
                                                                                                                                                                          "QQQ"
                                                                                                                                                                          {:window
                                                                                                                                                                           60})
                                                                                                                                                                         -12)
                                                                                                                                                                        [(weight-equal
                                                                                                                                                                          [(filter
                                                                                                                                                                            (rsi
                                                                                                                                                                             {:window
                                                                                                                                                                              10})
                                                                                                                                                                            (select-bottom
                                                                                                                                                                             1)
                                                                                                                                                                            [(asset
                                                                                                                                                                              "UGE"
                                                                                                                                                                              "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                                                                                                                             (asset
                                                                                                                                                                              "BOND"
                                                                                                                                                                              "Invesco Bond Fund")])])]
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
                                                                                                                                                                                      [(weight-equal
                                                                                                                                                                                        [(if
                                                                                                                                                                                          (>
                                                                                                                                                                                           (moving-average-return
                                                                                                                                                                                            "SPY"
                                                                                                                                                                                            {:window
                                                                                                                                                                                             15})
                                                                                                                                                                                           (moving-average-return
                                                                                                                                                                                            "SPY"
                                                                                                                                                                                            {:window
                                                                                                                                                                                             30}))
                                                                                                                                                                                          [(asset
                                                                                                                                                                                            "TQQQ"
                                                                                                                                                                                            "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                                                                                                                                                          [(weight-equal
                                                                                                                                                                                            [(filter
                                                                                                                                                                                              (rsi
                                                                                                                                                                                               {:window
                                                                                                                                                                                                10})
                                                                                                                                                                                              (select-bottom
                                                                                                                                                                                               1)
                                                                                                                                                                                              [(asset
                                                                                                                                                                                                "UGE"
                                                                                                                                                                                                "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                                                                                                                                               (asset
                                                                                                                                                                                                "BOND"
                                                                                                                                                                                                "Invesco Bond Fund")])])])])]
                                                                                                                                                                                      [(weight-equal
                                                                                                                                                                                        [(filter
                                                                                                                                                                                          (rsi
                                                                                                                                                                                           {:window
                                                                                                                                                                                            10})
                                                                                                                                                                                          (select-bottom
                                                                                                                                                                                           1)
                                                                                                                                                                                          [(asset
                                                                                                                                                                                            "UGE"
                                                                                                                                                                                            "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                                                                                                                                           (asset
                                                                                                                                                                                            "BOND"
                                                                                                                                                                                            "Invesco Bond Fund")])])])])])])])]
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
                                                                                                                                                                                  "ProShares Short QQQ")]
                                                                                                                                                                                [(asset
                                                                                                                                                                                  "SQQQ"
                                                                                                                                                                                  nil)])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])]
                                                                                        [(weight-equal
                                                                                          [(group
                                                                                            "Gold - V0.0 - (33,50,2009)"
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (>
                                                                                                 (moving-average-price
                                                                                                  "UGL"
                                                                                                  {:window
                                                                                                   50})
                                                                                                 (moving-average-price
                                                                                                  "UGL"
                                                                                                  {:window
                                                                                                   200}))
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (>
                                                                                                     (rsi
                                                                                                      "UGL"
                                                                                                      {:window
                                                                                                       20})
                                                                                                     80)
                                                                                                    [(asset
                                                                                                      "GLL"
                                                                                                      "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (>
                                                                                                         (rsi
                                                                                                          "UGL"
                                                                                                          {:window
                                                                                                           10})
                                                                                                         90)
                                                                                                        [(asset
                                                                                                          "GLL"
                                                                                                          "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (>
                                                                                                             (rsi
                                                                                                              "UGL"
                                                                                                              {:window
                                                                                                               2})
                                                                                                             99.9)
                                                                                                            [(asset
                                                                                                              "GLL"
                                                                                                              "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                                                                                                            [(asset
                                                                                                              "UGL"
                                                                                                              "ProShares Trust - ProShares Ultra Gold 2x Shares")])])])])])])]
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (>
                                                                                                     (moving-average-price
                                                                                                      "UGL"
                                                                                                      {:window
                                                                                                       20})
                                                                                                     (moving-average-price
                                                                                                      "UGL"
                                                                                                      {:window
                                                                                                       50}))
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (>
                                                                                                         (rsi
                                                                                                          "UGL"
                                                                                                          {:window
                                                                                                           20})
                                                                                                         75)
                                                                                                        [(asset
                                                                                                          "GLL"
                                                                                                          "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (>
                                                                                                             (rsi
                                                                                                              "UGL"
                                                                                                              {:window
                                                                                                               2})
                                                                                                             99.9)
                                                                                                            [(asset
                                                                                                              "GLL"
                                                                                                              "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                                                                                                            [(asset
                                                                                                              "UGL"
                                                                                                              "ProShares Trust - ProShares Ultra Gold 2x Shares")])])])])]
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (>
                                                                                                         (moving-average-price
                                                                                                          "UGL"
                                                                                                          {:window
                                                                                                           5})
                                                                                                         (moving-average-price
                                                                                                          "UGL"
                                                                                                          {:window
                                                                                                           10}))
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (>
                                                                                                             (rsi
                                                                                                              "UGL"
                                                                                                              {:window
                                                                                                               10})
                                                                                                             60)
                                                                                                            [(asset
                                                                                                              "GLL"
                                                                                                              "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                                                                                                            [(asset
                                                                                                              "UGL"
                                                                                                              "ProShares Trust - ProShares Ultra Gold 2x Shares")])])]
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (<
                                                                                                             (rsi
                                                                                                              "UGL"
                                                                                                              {:window
                                                                                                               20})
                                                                                                             30)
                                                                                                            [(asset
                                                                                                              "UGL"
                                                                                                              "ProShares Trust - ProShares Ultra Gold 2x Shares")]
                                                                                                            [(asset
                                                                                                              "GLL"
                                                                                                              "ProShares Trust - ProShares UltraShort Gold -2x Shares")])])])])])])])])])
                                                                                           (group
                                                                                            "Bonds Zoop V0.0 (144,38,2011)"
                                                                                            [(weight-equal
                                                                                              [(weight-equal
                                                                                                [(if
                                                                                                  (>
                                                                                                   (current-price
                                                                                                    "TLT")
                                                                                                   (moving-average-price
                                                                                                    "TLT"
                                                                                                    {:window
                                                                                                     200}))
                                                                                                  [(weight-equal
                                                                                                    [(if
                                                                                                      (>
                                                                                                       (rsi
                                                                                                        "QLD"
                                                                                                        {:window
                                                                                                         10})
                                                                                                       79)
                                                                                                      [(asset
                                                                                                        "UVXY"
                                                                                                        "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
                                                                                                      [(weight-equal
                                                                                                        [(if
                                                                                                          (<
                                                                                                           (rsi
                                                                                                            "TMF"
                                                                                                            {:window
                                                                                                             10})
                                                                                                           32)
                                                                                                          [(asset
                                                                                                            "TMF"
                                                                                                            "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                                                                                                          [(weight-equal
                                                                                                            [(if
                                                                                                              (<
                                                                                                               (rsi
                                                                                                                "BIL"
                                                                                                                {:window
                                                                                                                 30})
                                                                                                               (rsi
                                                                                                                "TLT"
                                                                                                                {:window
                                                                                                                 20}))
                                                                                                              [(weight-equal
                                                                                                                [(if
                                                                                                                  (<
                                                                                                                   (exponential-moving-average-price
                                                                                                                    "TMF"
                                                                                                                    {:window
                                                                                                                     8})
                                                                                                                   (moving-average-price
                                                                                                                    "TMF"
                                                                                                                    {:window
                                                                                                                     10}))
                                                                                                                  [(asset
                                                                                                                    "TMF"
                                                                                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                                                                                                                  [(asset
                                                                                                                    "TQQQ"
                                                                                                                    "ProShares UltraPro QQQ")])])]
                                                                                                              [(weight-equal
                                                                                                                [(if
                                                                                                                  (<
                                                                                                                   (rsi
                                                                                                                    "QLD"
                                                                                                                    {:window
                                                                                                                     10})
                                                                                                                   31)
                                                                                                                  [(asset
                                                                                                                    "TQQQ"
                                                                                                                    "ProShares UltraPro QQQ")]
                                                                                                                  [(asset
                                                                                                                    "BIL"
                                                                                                                    "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])]
                                                                                                  [(weight-equal
                                                                                                    [(if
                                                                                                      (<
                                                                                                       (rsi
                                                                                                        "TMF"
                                                                                                        {:window
                                                                                                         10})
                                                                                                       32)
                                                                                                      [(asset
                                                                                                        "TMF"
                                                                                                        "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                                                                                                      [(weight-equal
                                                                                                        [(if
                                                                                                          (>
                                                                                                           (moving-average-price
                                                                                                            "TMV"
                                                                                                            {:window
                                                                                                             15})
                                                                                                           (moving-average-price
                                                                                                            "TMV"
                                                                                                            {:window
                                                                                                             50}))
                                                                                                          [(weight-equal
                                                                                                            [(if
                                                                                                              (>
                                                                                                               (current-price
                                                                                                                "TMV")
                                                                                                               (moving-average-price
                                                                                                                "TMV"
                                                                                                                {:window
                                                                                                                 135}))
                                                                                                              [(weight-equal
                                                                                                                [(if
                                                                                                                  (>
                                                                                                                   (rsi
                                                                                                                    "TMV"
                                                                                                                    {:window
                                                                                                                     10})
                                                                                                                   65)
                                                                                                                  [(asset
                                                                                                                    "TMV"
                                                                                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")]
                                                                                                                  [(weight-equal
                                                                                                                    [(if
                                                                                                                      (>
                                                                                                                       (rsi
                                                                                                                        "TMV"
                                                                                                                        {:window
                                                                                                                         60})
                                                                                                                       59)
                                                                                                                      [(asset
                                                                                                                        "TMF"
                                                                                                                        "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                                                                                                                      [(asset
                                                                                                                        "TMV"
                                                                                                                        "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                                                                                                              [(asset
                                                                                                                "TMF"
                                                                                                                "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                                                                                                          [(asset
                                                                                                            "TMF"
                                                                                                            "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])
                                                                                           (group
                                                                                            "Hg Short Only V0.2 (57,19,2011)"
                                                                                            [(weight-equal
                                                                                              [(if
                                                                                                (>
                                                                                                 (current-price
                                                                                                  "SPY")
                                                                                                 (moving-average-price
                                                                                                  "SPY"
                                                                                                  {:window
                                                                                                   200}))
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (>
                                                                                                     (rsi
                                                                                                      "QQQ"
                                                                                                      {:window
                                                                                                       10})
                                                                                                     79)
                                                                                                    [(weight-equal
                                                                                                      [(asset
                                                                                                        "UVXY"
                                                                                                        "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (>
                                                                                                         (rsi
                                                                                                          "SPY"
                                                                                                          {:window
                                                                                                           10})
                                                                                                         79)
                                                                                                        [(weight-equal
                                                                                                          [(asset
                                                                                                            "UVXY"
                                                                                                            "ProShares Ultra VIX Short-Term Futures ETF")])]
                                                                                                        [(weight-equal
                                                                                                          [(asset
                                                                                                            "BOND"
                                                                                                            "Pimco Exchange Traded Fund - PIMCO Active Bond ETF")])])])])])]
                                                                                                [(weight-equal
                                                                                                  [(if
                                                                                                    (<
                                                                                                     (rsi
                                                                                                      "TQQQ"
                                                                                                      {:window
                                                                                                       10})
                                                                                                     31)
                                                                                                    [(weight-equal
                                                                                                      [(asset
                                                                                                        "BOND"
                                                                                                        "Pimco Exchange Traded Fund - PIMCO Active Bond ETF")])]
                                                                                                    [(weight-equal
                                                                                                      [(if
                                                                                                        (<
                                                                                                         (rsi
                                                                                                          "UPRO"
                                                                                                          {:window
                                                                                                           10})
                                                                                                         31)
                                                                                                        [(weight-equal
                                                                                                          [(asset
                                                                                                            "BOND"
                                                                                                            "Pimco Exchange Traded Fund - PIMCO Active Bond ETF")])]
                                                                                                        [(weight-equal
                                                                                                          [(if
                                                                                                            (<
                                                                                                             (cumulative-return
                                                                                                              "TQQQ"
                                                                                                              {:window
                                                                                                               6})
                                                                                                             -11)
                                                                                                            [(group
                                                                                                              "Buy the dips. Sell the rips. V2"
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
                                                                                                                    [(asset
                                                                                                                      "BOND"
                                                                                                                      "Pimco Exchange Traded Fund - PIMCO Active Bond ETF")])])])])]
                                                                                                            [(weight-equal
                                                                                                              [(if
                                                                                                                (>
                                                                                                                 (current-price
                                                                                                                  "QLD")
                                                                                                                 (moving-average-price
                                                                                                                  "QLD"
                                                                                                                  {:window
                                                                                                                   20}))
                                                                                                                [(weight-equal
                                                                                                                  [(asset
                                                                                                                    "BOND"
                                                                                                                    "Pimco Exchange Traded Fund - PIMCO Active Bond ETF")])]
                                                                                                                [(weight-equal
                                                                                                                  [(if
                                                                                                                    (>
                                                                                                                     (moving-average-return
                                                                                                                      "TLT"
                                                                                                                      {:window
                                                                                                                       20})
                                                                                                                     (moving-average-return
                                                                                                                      "UDN"
                                                                                                                      {:window
                                                                                                                       20}))
                                                                                                                    [(weight-equal
                                                                                                                      [(asset
                                                                                                                        "SQQQ"
                                                                                                                        "ProShares UltraPro Short QQQ")])]
                                                                                                                    [(weight-equal
                                                                                                                      [(filter
                                                                                                                        (rsi
                                                                                                                         {:window
                                                                                                                          10})
                                                                                                                        (select-bottom
                                                                                                                         1)
                                                                                                                        [(asset
                                                                                                                          "UUP"
                                                                                                                          "Invesco DB US Dollar Index Bullish Fund")
                                                                                                                         (asset
                                                                                                                          "SQQQ"
                                                                                                                          "ProShares UltraPro Short QQQ")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
       (group
        "Four Corners (66,35,2011)"
        [(weight-equal
          [(if
            (> (rsi "FAS" {:window 10}) 79.5)
            [(group
              "UVXY  ->  UVIX"
              [(weight-equal
                [(if
                  (< (rsi "UVXY" {:window 10}) 40)
                  [(asset "UVIX" "2x Long VIX Futures ETF")]
                  [(asset
                    "UVXY"
                    "ProShares Ultra VIX Short-Term Futures ETF")])])])]
            [(weight-equal
              [(if
                (> (rsi "IOO" {:window 10}) 80)
                [(group
                  "UVXY  ->  UVIX"
                  [(weight-equal
                    [(if
                      (< (rsi "UVXY" {:window 10}) 40)
                      [(asset "UVIX" "2x Long VIX Futures ETF")]
                      [(asset
                        "UVXY"
                        "ProShares Ultra VIX Short-Term Futures ETF")])])])]
                [(weight-equal
                  [(if
                    (> (rsi "SPY" {:window 10}) 80)
                    [(group
                      "Scale-In | VIX+ -> VIX++"
                      [(weight-equal
                        [(if
                          (> (rsi "SPY" {:window 10}) 82.5)
                          [(asset "UVIX" "2x Long VIX Futures ETF")]
                          [(group
                            "UVXY  ->  UVIX"
                            [(weight-equal
                              [(if
                                (< (rsi "UVXY" {:window 10}) 40)
                                [(asset
                                  "UVIX"
                                  "2x Long VIX Futures ETF")]
                                [(asset
                                  "UVXY"
                                  "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                    [(weight-equal
                      [(if
                        (> (rsi "QQQ" {:window 10}) 79)
                        [(group
                          "Scale-In | VIX+ -> VIX++"
                          [(weight-equal
                            [(if
                              (> (rsi "QQQ" {:window 10}) 82.5)
                              [(asset
                                "UVIX"
                                "2x Long VIX Futures ETF")]
                              [(group
                                "UVXY  ->  UVIX"
                                [(weight-equal
                                  [(if
                                    (< (rsi "UVXY" {:window 10}) 40)
                                    [(asset
                                      "UVIX"
                                      "2x Long VIX Futures ETF")]
                                    [(asset
                                      "UVXY"
                                      "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                        [(weight-equal
                          [(if
                            (> (rsi "XLP" {:window 10}) 77)
                            [(group
                              "Scale-In | VIX -> VIX+"
                              [(weight-equal
                                [(if
                                  (> (rsi "XLP" {:window 10}) 85)
                                  [(asset
                                    "UVIX"
                                    "2x Long VIX Futures ETF")]
                                  [(group
                                    "UVXY  ->  UVIX"
                                    [(weight-equal
                                      [(if
                                        (<
                                         (rsi "UVXY" {:window 10})
                                         40)
                                        [(asset
                                          "UVIX"
                                          "2x Long VIX Futures ETF")]
                                        [(asset
                                          "UVXY"
                                          "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                            [(weight-equal
                              [(if
                                (> (rsi "VTV" {:window 10}) 79)
                                [(group
                                  "Scale-In | VIX -> VIX+"
                                  [(weight-equal
                                    [(if
                                      (> (rsi "VTV" {:window 10}) 85)
                                      [(asset
                                        "UVIX"
                                        "2x Long VIX Futures ETF")]
                                      [(group
                                        "UVXY  ->  UVIX"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (rsi "UVXY" {:window 10})
                                             40)
                                            [(asset
                                              "UVIX"
                                              "2x Long VIX Futures ETF")]
                                            [(asset
                                              "UVXY"
                                              "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                                [(weight-equal
                                  [(if
                                    (> (rsi "XLF" {:window 10}) 81)
                                    [(group
                                      "Scale-In | VIX -> VIX+"
                                      [(weight-equal
                                        [(if
                                          (>
                                           (rsi "XLF" {:window 10})
                                           85)
                                          [(group
                                            "UVXY  ->  UVIX"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (rsi
                                                  "UVXY"
                                                  {:window 10})
                                                 40)
                                                [(asset
                                                  "UVIX"
                                                  "2x Long VIX Futures ETF")]
                                                [(asset
                                                  "UVXY"
                                                  "ProShares Ultra VIX Short-Term Futures ETF")])])])]
                                          [(group
                                            "UVXY  ->  UVIX"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (rsi
                                                  "UVXY"
                                                  {:window 10})
                                                 40)
                                                [(asset
                                                  "UVIX"
                                                  "2x Long VIX Futures ETF")]
                                                [(asset
                                                  "UVXY"
                                                  "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                                    [(weight-equal
                                      [(if
                                        (> (rsi "VOX" {:window 10}) 79)
                                        [(group
                                          "Scale-In | BTAL -> VIX"
                                          [(weight-equal
                                            [(if
                                              (>
                                               (rsi "VOX" {:window 10})
                                               85)
                                              [(asset
                                                "UVIX"
                                                "2x Long VIX Futures ETF")]
                                              [(group
                                                "UVXY  ->  UVIX"
                                                [(weight-equal
                                                  [(if
                                                    (<
                                                     (rsi
                                                      "UVXY"
                                                      {:window 10})
                                                     40)
                                                    [(asset
                                                      "UVIX"
                                                      "2x Long VIX Futures ETF")]
                                                    [(asset
                                                      "UVXY"
                                                      "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "CURE" {:window 10})
                                             82)
                                            [(group
                                              "Scale-In | BTAL -> VIX"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (rsi
                                                    "CURE"
                                                    {:window 10})
                                                   85)
                                                  [(group
                                                    "UVXY  ->  UVIX"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "UVXY"
                                                          {:window 10})
                                                         40)
                                                        [(asset
                                                          "UVIX"
                                                          "2x Long VIX Futures ETF")]
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")])])])]
                                                  [(group
                                                    "UVXY  ->  UVIX"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "UVXY"
                                                          {:window 10})
                                                         40)
                                                        [(asset
                                                          "UVIX"
                                                          "2x Long VIX Futures ETF")]
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "RETL"
                                                  {:window 10})
                                                 82)
                                                [(group
                                                  "Scale-In | BTAL -> VIX"
                                                  [(weight-equal
                                                    [(if
                                                      (>
                                                       (rsi
                                                        "RETL"
                                                        {:window 10})
                                                       85)
                                                      [(group
                                                        "UVXY  ->  UVIX"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "UVXY"
                                                              {:window
                                                               10})
                                                             40)
                                                            [(asset
                                                              "UVIX"
                                                              "2x Long VIX Futures ETF")]
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")])])])]
                                                      [(group
                                                        "UVXY  ->  UVIX"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "UVXY"
                                                              {:window
                                                               10})
                                                             40)
                                                            [(asset
                                                              "UVIX"
                                                              "2x Long VIX Futures ETF")]
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "XLY"
                                                      {:window 10})
                                                     82)
                                                    [(group
                                                      "UVXY  ->  UVIX"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (rsi
                                                            "UVXY"
                                                            {:window
                                                             10})
                                                           40)
                                                          [(asset
                                                            "UVIX"
                                                            "2x Long VIX Futures ETF")]
                                                          [(asset
                                                            "UVXY"
                                                            "ProShares Ultra VIX Short-Term Futures ETF")])])])]
                                                    [(group
                                                      "Vol Check"
                                                      [(weight-equal
                                                        [(if
                                                          (>
                                                           (rsi
                                                            "UVXY"
                                                            {:window
                                                             21})
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
                                                                  [(asset
                                                                    "VIXM"
                                                                    "ProShares VIX Mid-Term Futures ETF")]
                                                                  [(asset
                                                                    "SPXL"
                                                                    "Direxion Daily S&P 500 Bull 3x Shares")])])])])]
                                                          [(group
                                                            "Oversold Checks "
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (rsi
                                                                  "SOXL"
                                                                  {:window
                                                                   10})
                                                                 25)
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (current-price
                                                                      "SPY")
                                                                     (moving-average-price
                                                                      "SPY"
                                                                      {:window
                                                                       200}))
                                                                    [(asset
                                                                      "SOXL"
                                                                      "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")]
                                                                    [(asset
                                                                      "BIL"
                                                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                                                [(weight-equal
                                                                  [(if
                                                                    (<
                                                                     (rsi
                                                                      "TQQQ"
                                                                      {:window
                                                                       10})
                                                                     25)
                                                                    [(weight-equal
                                                                      [(if
                                                                        (>
                                                                         (current-price
                                                                          "SPY")
                                                                         (moving-average-price
                                                                          "SPY"
                                                                          {:window
                                                                           200}))
                                                                        [(asset
                                                                          "TQQQ"
                                                                          nil)]
                                                                        [(asset
                                                                          "BIL"
                                                                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "TQQQ"
                                                                          {:window
                                                                           10})
                                                                         28)
                                                                        [(weight-equal
                                                                          [(if
                                                                            (>
                                                                             (current-price
                                                                              "SPY")
                                                                             (moving-average-price
                                                                              "SPY"
                                                                              {:window
                                                                               200}))
                                                                            [(weight-equal
                                                                              [(filter
                                                                                (rsi
                                                                                 {:window
                                                                                  10})
                                                                                (select-bottom
                                                                                 2)
                                                                                [(asset
                                                                                  "SOXL"
                                                                                  nil)
                                                                                 (asset
                                                                                  "TECL"
                                                                                  nil)
                                                                                 (asset
                                                                                  "TQQQ"
                                                                                  nil)
                                                                                 (asset
                                                                                  "TQQQ"
                                                                                  nil)])])]
                                                                            [(asset
                                                                              "BIL"
                                                                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                                                        [(weight-equal
                                                                          [(if
                                                                            (<
                                                                             (rsi
                                                                              "TECL"
                                                                              {:window
                                                                               14})
                                                                             25)
                                                                            [(weight-equal
                                                                              [(if
                                                                                (>
                                                                                 (current-price
                                                                                  "SPY")
                                                                                 (moving-average-price
                                                                                  "SPY"
                                                                                  {:window
                                                                                   200}))
                                                                                [(asset
                                                                                  "TECL"
                                                                                  nil)]
                                                                                [(asset
                                                                                  "BIL"
                                                                                  "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                                                            [(weight-equal
                                                                              [(if
                                                                                (<
                                                                                 (rsi
                                                                                  "UPRO"
                                                                                  {:window
                                                                                   10})
                                                                                 25)
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (>
                                                                                     (current-price
                                                                                      "SPY")
                                                                                     (moving-average-price
                                                                                      "SPY"
                                                                                      {:window
                                                                                       200}))
                                                                                    [(asset
                                                                                      "UPRO"
                                                                                      "ProShares Trust - ProShares UltraPro S&P 500 ETF 3x Shares")]
                                                                                    [(asset
                                                                                      "BIL"
                                                                                      "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                                                                [(weight-equal
                                                                                  [(if
                                                                                    (>
                                                                                     (rsi
                                                                                      "QQQ"
                                                                                      {:window
                                                                                       120})
                                                                                     (rsi
                                                                                      "VPU"
                                                                                      {:window
                                                                                       120}))
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (cumulative-return
                                                                                          "CORP"
                                                                                          {:window
                                                                                           60})
                                                                                         (cumulative-return
                                                                                          "BIL"
                                                                                          {:window
                                                                                           60}))
                                                                                        [(group
                                                                                          "Bull"
                                                                                          [(weight-equal
                                                                                            [(asset
                                                                                              "TQQQ"
                                                                                              "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])]
                                                                                        [(group
                                                                                          "Mild Bull"
                                                                                          [(weight-equal
                                                                                            [(group
                                                                                              "QQQ or PSQ"
                                                                                              [(weight-equal
                                                                                                [(if
                                                                                                  (>
                                                                                                   (rsi
                                                                                                    "IEF"
                                                                                                    {:window
                                                                                                     7})
                                                                                                   (rsi
                                                                                                    "PSQ"
                                                                                                    {:window
                                                                                                     20}))
                                                                                                  [(asset
                                                                                                    "TQQQ"
                                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                                                                  [(asset
                                                                                                    "PSQ"
                                                                                                    nil)])])])
                                                                                             (asset
                                                                                              "BIL"
                                                                                              nil)])])])])]
                                                                                    [(weight-equal
                                                                                      [(if
                                                                                        (>
                                                                                         (cumulative-return
                                                                                          "CORP"
                                                                                          {:window
                                                                                           60})
                                                                                         (cumulative-return
                                                                                          "BIL"
                                                                                          {:window
                                                                                           60}))
                                                                                        [(group
                                                                                          "Mild Bear"
                                                                                          [(weight-equal
                                                                                            [(group
                                                                                              "QQQ or TLT"
                                                                                              [(weight-equal
                                                                                                [(if
                                                                                                  (>
                                                                                                   (rsi
                                                                                                    "XLK"
                                                                                                    {:window
                                                                                                     7})
                                                                                                   (rsi
                                                                                                    "WTMF"
                                                                                                    {:window
                                                                                                     20}))
                                                                                                  [(asset
                                                                                                    "TQQQ"
                                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                                                                  [(asset
                                                                                                    "TLT"
                                                                                                    nil)])])])])])]
                                                                                        [(group
                                                                                          "Bear"
                                                                                          [(weight-equal
                                                                                            [(group
                                                                                              "TLT or PSQ"
                                                                                              [(weight-equal
                                                                                                [(if
                                                                                                  (>
                                                                                                   (rsi
                                                                                                    "IEF"
                                                                                                    {:window
                                                                                                     7})
                                                                                                   (rsi
                                                                                                    "PSQ"
                                                                                                    {:window
                                                                                                     20}))
                                                                                                  [(asset
                                                                                                    "TLT"
                                                                                                    nil)]
                                                                                                  [(asset
                                                                                                    "PSQ"
                                                                                                    nil)])])])
                                                                                             (group
                                                                                              "Utilities vs Gold"
                                                                                              [(weight-equal
                                                                                                [(filter
                                                                                                  (rsi
                                                                                                   {:window
                                                                                                    60})
                                                                                                  (select-bottom
                                                                                                   1)
                                                                                                  [(asset
                                                                                                    "XLU"
                                                                                                    nil)
                                                                                                   (asset
                                                                                                    "GLD"
                                                                                                    nil)])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
       (group
        "Better KMLM (1042,35,2022)"
        [(weight-equal
          [(if
            (> (rsi "FAS" {:window 10}) 79.5)
            [(group
              "UVXY  ->  UVIX"
              [(weight-equal
                [(if
                  (< (rsi "UVXY" {:window 10}) 40)
                  [(asset "UVIX" "2x Long VIX Futures ETF")]
                  [(asset
                    "UVXY"
                    "ProShares Ultra VIX Short-Term Futures ETF")])])])]
            [(weight-equal
              [(if
                (> (rsi "IOO" {:window 10}) 80)
                [(group
                  "UVXY  ->  UVIX"
                  [(weight-equal
                    [(if
                      (< (rsi "UVXY" {:window 10}) 40)
                      [(asset "UVIX" "2x Long VIX Futures ETF")]
                      [(asset
                        "UVXY"
                        "ProShares Ultra VIX Short-Term Futures ETF")])])])]
                [(weight-equal
                  [(if
                    (> (rsi "SPY" {:window 10}) 80)
                    [(group
                      "Scale-In | VIX+ -> VIX++"
                      [(weight-equal
                        [(if
                          (> (rsi "SPY" {:window 10}) 82.5)
                          [(asset "UVIX" "2x Long VIX Futures ETF")]
                          [(group
                            "UVXY  ->  UVIX"
                            [(weight-equal
                              [(if
                                (< (rsi "UVXY" {:window 10}) 40)
                                [(asset
                                  "UVIX"
                                  "2x Long VIX Futures ETF")]
                                [(asset
                                  "UVXY"
                                  "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                    [(weight-equal
                      [(if
                        (> (rsi "QQQ" {:window 10}) 79)
                        [(group
                          "Scale-In | VIX+ -> VIX++"
                          [(weight-equal
                            [(if
                              (> (rsi "QQQ" {:window 10}) 82.5)
                              [(asset
                                "UVIX"
                                "2x Long VIX Futures ETF")]
                              [(group
                                "UVXY  ->  UVIX"
                                [(weight-equal
                                  [(if
                                    (< (rsi "UVXY" {:window 10}) 40)
                                    [(asset
                                      "UVIX"
                                      "2x Long VIX Futures ETF")]
                                    [(asset
                                      "UVXY"
                                      "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                        [(weight-equal
                          [(if
                            (> (rsi "XLP" {:window 10}) 77)
                            [(group
                              "Scale-In | VIX -> VIX+"
                              [(weight-equal
                                [(if
                                  (> (rsi "XLP" {:window 10}) 85)
                                  [(asset
                                    "UVIX"
                                    "2x Long VIX Futures ETF")]
                                  [(group
                                    "UVXY  ->  UVIX"
                                    [(weight-equal
                                      [(if
                                        (<
                                         (rsi "UVXY" {:window 10})
                                         40)
                                        [(asset
                                          "UVIX"
                                          "2x Long VIX Futures ETF")]
                                        [(asset
                                          "UVXY"
                                          "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                            [(weight-equal
                              [(if
                                (> (rsi "VTV" {:window 10}) 79)
                                [(group
                                  "Scale-In | VIX -> VIX+"
                                  [(weight-equal
                                    [(if
                                      (> (rsi "VTV" {:window 10}) 85)
                                      [(asset
                                        "UVIX"
                                        "2x Long VIX Futures ETF")]
                                      [(group
                                        "UVXY  ->  UVIX"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (rsi "UVXY" {:window 10})
                                             40)
                                            [(asset
                                              "UVIX"
                                              "2x Long VIX Futures ETF")]
                                            [(asset
                                              "UVXY"
                                              "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                                [(weight-equal
                                  [(if
                                    (> (rsi "XLF" {:window 10}) 81)
                                    [(group
                                      "Scale-In | VIX -> VIX+"
                                      [(weight-equal
                                        [(if
                                          (>
                                           (rsi "XLF" {:window 10})
                                           85)
                                          [(group
                                            "UVXY  ->  UVIX"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (rsi
                                                  "UVXY"
                                                  {:window 10})
                                                 40)
                                                [(asset
                                                  "UVIX"
                                                  "2x Long VIX Futures ETF")]
                                                [(asset
                                                  "UVXY"
                                                  "ProShares Ultra VIX Short-Term Futures ETF")])])])]
                                          [(group
                                            "UVXY  ->  UVIX"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (rsi
                                                  "UVXY"
                                                  {:window 10})
                                                 40)
                                                [(asset
                                                  "UVIX"
                                                  "2x Long VIX Futures ETF")]
                                                [(asset
                                                  "UVXY"
                                                  "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                                    [(weight-equal
                                      [(if
                                        (> (rsi "VOX" {:window 10}) 79)
                                        [(group
                                          "Scale-In | BTAL -> VIX"
                                          [(weight-equal
                                            [(if
                                              (>
                                               (rsi "VOX" {:window 10})
                                               85)
                                              [(asset
                                                "UVIX"
                                                "2x Long VIX Futures ETF")]
                                              [(group
                                                "UVXY  ->  UVIX"
                                                [(weight-equal
                                                  [(if
                                                    (<
                                                     (rsi
                                                      "UVXY"
                                                      {:window 10})
                                                     40)
                                                    [(asset
                                                      "UVIX"
                                                      "2x Long VIX Futures ETF")]
                                                    [(asset
                                                      "UVXY"
                                                      "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "CURE" {:window 10})
                                             82)
                                            [(group
                                              "Scale-In | BTAL -> VIX"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (rsi
                                                    "CURE"
                                                    {:window 10})
                                                   85)
                                                  [(group
                                                    "UVXY  ->  UVIX"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "UVXY"
                                                          {:window 10})
                                                         40)
                                                        [(asset
                                                          "UVIX"
                                                          "2x Long VIX Futures ETF")]
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")])])])]
                                                  [(group
                                                    "UVXY  ->  UVIX"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "UVXY"
                                                          {:window 10})
                                                         40)
                                                        [(asset
                                                          "UVIX"
                                                          "2x Long VIX Futures ETF")]
                                                        [(asset
                                                          "UVXY"
                                                          "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "RETL"
                                                  {:window 10})
                                                 82)
                                                [(group
                                                  "Scale-In | BTAL -> VIX"
                                                  [(weight-equal
                                                    [(if
                                                      (>
                                                       (rsi
                                                        "RETL"
                                                        {:window 10})
                                                       85)
                                                      [(group
                                                        "UVXY  ->  UVIX"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "UVXY"
                                                              {:window
                                                               10})
                                                             40)
                                                            [(asset
                                                              "UVIX"
                                                              "2x Long VIX Futures ETF")]
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")])])])]
                                                      [(group
                                                        "UVXY  ->  UVIX"
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "UVXY"
                                                              {:window
                                                               10})
                                                             40)
                                                            [(asset
                                                              "UVIX"
                                                              "2x Long VIX Futures ETF")]
                                                            [(asset
                                                              "UVXY"
                                                              "ProShares Ultra VIX Short-Term Futures ETF")])])])])])])]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "XLY"
                                                      {:window 10})
                                                     82)
                                                    [(group
                                                      "UVXY  ->  UVIX"
                                                      [(weight-equal
                                                        [(if
                                                          (<
                                                           (rsi
                                                            "UVXY"
                                                            {:window
                                                             10})
                                                           40)
                                                          [(asset
                                                            "UVIX"
                                                            "2x Long VIX Futures ETF")]
                                                          [(asset
                                                            "UVXY"
                                                            "ProShares Ultra VIX Short-Term Futures ETF")])])])]
                                                    [(weight-equal
                                                      [(group
                                                        "BSC"
                                                        [(weight-equal
                                                          [(if
                                                            (>
                                                             (rsi
                                                              "UVXY"
                                                              {:window
                                                               21})
                                                             65)
                                                            [(weight-equal
                                                              [(group
                                                                "BSC 1"
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "SPY"
                                                                      {:window
                                                                       21})
                                                                     30)
                                                                    [(asset
                                                                      "VIXM"
                                                                      "ProShares VIX Mid-Term Futures ETF")]
                                                                    [(asset
                                                                      "SPXL"
                                                                      "Direxion Daily S&P 500 Bull 3x Shares")])])])
                                                               (group
                                                                "BSC 2"
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "UVXY"
                                                                      {:window
                                                                       10})
                                                                     74)
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (rsi
                                                                          "UVXY"
                                                                          {:window
                                                                           10})
                                                                         84)
                                                                        [(asset
                                                                          "UVXY"
                                                                          "ProShares Ultra VIX Short-Term Futures ETF")]
                                                                        [(asset
                                                                          "BIL"
                                                                          "SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                                                                    [(asset
                                                                      "BIL"
                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])]
                                                            [(weight-equal
                                                              [(group
                                                                "Oversold Checks"
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (current-price
                                                                      "SPY")
                                                                     (moving-average-price
                                                                      "SPY"
                                                                      {:window
                                                                       200}))
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
                                                                                  "SPXL"
                                                                                  "Direxion Daily S&P 500 Bull 3x Shares")]
                                                                                [(weight-equal
                                                                                  [(group
                                                                                    "Copypasta YOLO GainZs Here"
                                                                                    [(weight-equal
                                                                                      [(group
                                                                                        "KMLM Switch"
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
                                                                                            [(group
                                                                                              "Ticker Mixer"
                                                                                              [(weight-equal
                                                                                                [(group
                                                                                                  "Pick Top 3"
                                                                                                  [(weight-equal
                                                                                                    [(filter
                                                                                                      (moving-average-return
                                                                                                       {:window
                                                                                                        15})
                                                                                                      (select-top
                                                                                                       3)
                                                                                                      [(asset
                                                                                                        "SPXL"
                                                                                                        nil)
                                                                                                       (asset
                                                                                                        "TQQQ"
                                                                                                        nil)
                                                                                                       (asset
                                                                                                        "TECL"
                                                                                                        nil)
                                                                                                       (asset
                                                                                                        "SOXL"
                                                                                                        nil)
                                                                                                       (asset
                                                                                                        "FNGG"
                                                                                                        "Direxion Shares ETF Trust - Direxion Daily NYSE FANG+ Bull 2X Shares")])])])
                                                                                                 (asset
                                                                                                  "TQQQ"
                                                                                                  nil)])])]
                                                                                            [(group
                                                                                              "Ticker Mixer - Short"
                                                                                              [(weight-equal
                                                                                                [(group
                                                                                                  "Pick Bottom 3"
                                                                                                  [(weight-equal
                                                                                                    [(filter
                                                                                                      (moving-average-return
                                                                                                       {:window
                                                                                                        15})
                                                                                                      (select-bottom
                                                                                                       3)
                                                                                                      [(asset
                                                                                                        "SPXU"
                                                                                                        nil)
                                                                                                       (asset
                                                                                                        "SQQQ"
                                                                                                        nil)
                                                                                                       (asset
                                                                                                        "TECS"
                                                                                                        nil)
                                                                                                       (asset
                                                                                                        "SOXS"
                                                                                                        nil)
                                                                                                       (asset
                                                                                                        "FNGD"
                                                                                                        nil)
                                                                                                       (asset
                                                                                                        "SRTY"
                                                                                                        nil)])])])
                                                                                                 (asset
                                                                                                  "QID"
                                                                                                  nil)])])])])])])])])])])])])])])]
                                                                    [(group
                                                                      "KMLM Switch"
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
                                                                          [(group
                                                                            "Ticker Mixer"
                                                                            [(weight-equal
                                                                              [(group
                                                                                "Pick Top 3"
                                                                                [(weight-equal
                                                                                  [(filter
                                                                                    (moving-average-return
                                                                                     {:window
                                                                                      15})
                                                                                    (select-top
                                                                                     3)
                                                                                    [(asset
                                                                                      "SPXL"
                                                                                      nil)
                                                                                     (asset
                                                                                      "TQQQ"
                                                                                      nil)
                                                                                     (asset
                                                                                      "TECL"
                                                                                      nil)
                                                                                     (asset
                                                                                      "SOXL"
                                                                                      nil)
                                                                                     (asset
                                                                                      "FNGG"
                                                                                      "Direxion Shares ETF Trust - Direxion Daily NYSE FANG+ Bull 2X Shares")])])])
                                                                               (asset
                                                                                "TQQQ"
                                                                                nil)])])]
                                                                          [(group
                                                                            "Ticker Mixer - Short"
                                                                            [(weight-equal
                                                                              [(group
                                                                                "Pick Bottom 3"
                                                                                [(weight-equal
                                                                                  [(filter
                                                                                    (moving-average-return
                                                                                     {:window
                                                                                      15})
                                                                                    (select-bottom
                                                                                     3)
                                                                                    [(asset
                                                                                      "SPXU"
                                                                                      nil)
                                                                                     (asset
                                                                                      "SQQQ"
                                                                                      nil)
                                                                                     (asset
                                                                                      "TECS"
                                                                                      nil)
                                                                                     (asset
                                                                                      "SOXS"
                                                                                      nil)
                                                                                     (asset
                                                                                      "FNGD"
                                                                                      nil)
                                                                                     (asset
                                                                                      "SRTY"
                                                                                      nil)])])])
                                                                               (asset
                                                                                "QID"
                                                                                nil)])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
       (group
        "EM ftlt (148,72,2007)"
        [(weight-equal
          [(if
            (< (rsi "EEM" {:window 14}) 30)
            [(asset "EDC" nil)]
            [(weight-equal
              [(if
                (>
                 (current-price "SHV")
                 (moving-average-price "SHV" {:window 50}))
                [(weight-equal
                  [(if
                    (>
                     (current-price "EEM")
                     (moving-average-price "EEM" {:window 200}))
                    [(group
                      "IEI vs IWM"
                      [(weight-equal
                        [(if
                          (>
                           (rsi "IEI" {:window 10})
                           (rsi "IWM" {:window 15}))
                          [(asset "EDC" nil)]
                          [(asset "EDZ" nil)])])])]
                    [(group
                      "IGIB vs EEM"
                      [(weight-equal
                        [(if
                          (>
                           (rsi "IGIB" {:window 15})
                           (rsi "EEM" {:window 15}))
                          [(asset "EDC" nil)]
                          [(asset "EDZ" nil)])])])
                     (group
                      "IGIB vs SPY"
                      [(weight-equal
                        [(if
                          (>
                           (rsi "IGIB" {:window 10})
                           (rsi "SPY" {:window 10}))
                          [(asset "EDC" nil)]
                          [(asset "EDZ" nil)])])])])])]
                [(group
                  "IGIB vs SPY"
                  [(weight-equal
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "SPY" {:window 10}))
                      [(asset "EDC" nil)]
                      [(asset "EDZ" nil)])])])])])])])])
       (group
        "QQQ FTLT Bonds - V0.5 - (237,33,2011)"
        [(weight-equal
          [(if
            (> (rsi "SPY" {:window 10}) 80)
            [(asset "UVXY" nil)]
            [(weight-equal
              [(if
                (> (rsi "QQQ" {:window 10}) 79)
                [(asset
                  "UVXY"
                  "ProShares Ultra VIX Short-Term Futures ETF")]
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
                            (> (rsi "XLK" {:window 10}) 79)
                            [(asset
                              "UVXY"
                              "ProShares Ultra VIX Short-Term Futures ETF")]
                            [(weight-equal
                              [(if
                                (> (rsi "XLP" {:window 10}) 75)
                                [(asset
                                  "VIXY"
                                  "ProShares VIX Short-Term Futures ETF")]
                                [(weight-equal
                                  [(if
                                    (> (rsi "XLF" {:window 10}) 80)
                                    [(asset
                                      "UVXY"
                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                    [(group
                                      "Vol Check"
                                      [(weight-equal
                                        [(if
                                          (>
                                           (rsi "UVXY" {:window 21})
                                           65)
                                          [(weight-equal
                                            [(group
                                              "BSC"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (rsi
                                                    "SPY"
                                                    {:window 21})
                                                   30)
                                                  [(asset
                                                    "VIXM"
                                                    "ProShares VIX Mid-Term Futures ETF")]
                                                  [(asset
                                                    "SPXL"
                                                    "Direxion Daily S&P 500 Bull 3x Shares")])])])])]
                                          [(group
                                            "Vix Low"
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (rsi
                                                  "SOXX"
                                                  {:window 10})
                                                 30)
                                                [(asset "SOXL" nil)]
                                                [(weight-equal
                                                  [(if
                                                    (<
                                                     (rsi
                                                      "QQQ"
                                                      {:window 10})
                                                     30)
                                                    [(asset
                                                      "TECL"
                                                      nil)]
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "SPY"
                                                          {:window 10})
                                                         30)
                                                        [(asset
                                                          "UPRO"
                                                          nil)]
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
                                                                  [(weight-equal
                                                                    [(if
                                                                      (>
                                                                       (moving-average-return
                                                                        "SPY"
                                                                        {:window
                                                                         15})
                                                                       (moving-average-return
                                                                        "SPY"
                                                                        {:window
                                                                         30}))
                                                                      [(asset
                                                                        "TQQQ"
                                                                        "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                                      [(weight-equal
                                                                        [(filter
                                                                          (rsi
                                                                           {:window
                                                                            10})
                                                                          (select-bottom
                                                                           1)
                                                                          [(asset
                                                                            "UGE"
                                                                            "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                           (asset
                                                                            "BOND"
                                                                            "Invesco Bond Fund")])])])])]
                                                                  [(asset
                                                                    "PSQ"
                                                                    "ProShares Trust - ProShares Short QQQ -1x Shares")])])])]
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (cumulative-return
                                                                  "QQQ"
                                                                  {:window
                                                                   60})
                                                                 -12)
                                                                [(weight-equal
                                                                  [(filter
                                                                    (rsi
                                                                     {:window
                                                                      10})
                                                                    (select-bottom
                                                                     1)
                                                                    [(asset
                                                                      "UGE"
                                                                      "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                     (asset
                                                                      "BOND"
                                                                      "Invesco Bond Fund")])])]
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
                                                                              [(weight-equal
                                                                                [(if
                                                                                  (>
                                                                                   (moving-average-return
                                                                                    "SPY"
                                                                                    {:window
                                                                                     15})
                                                                                   (moving-average-return
                                                                                    "SPY"
                                                                                    {:window
                                                                                     30}))
                                                                                  [(asset
                                                                                    "TQQQ"
                                                                                    "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                                                                  [(weight-equal
                                                                                    [(filter
                                                                                      (rsi
                                                                                       {:window
                                                                                        10})
                                                                                      (select-bottom
                                                                                       1)
                                                                                      [(asset
                                                                                        "UGE"
                                                                                        "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                                       (asset
                                                                                        "BOND"
                                                                                        "Invesco Bond Fund")])])])])]
                                                                              [(weight-equal
                                                                                [(filter
                                                                                  (rsi
                                                                                   {:window
                                                                                    10})
                                                                                  (select-bottom
                                                                                   1)
                                                                                  [(asset
                                                                                    "UGE"
                                                                                    "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                                   (asset
                                                                                    "BOND"
                                                                                    "Invesco Bond Fund")])])])])])])])]
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
                                                                          "ProShares Short QQQ")]
                                                                        [(asset
                                                                          "SQQQ"
                                                                          nil)])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
       (group
        "QQQ FTLT SMA V0.1 - (183,39,2011)"
        [(weight-equal
          [(group
            "QQQ FTLT SMA V0.1 - (183,39,2011)"
            [(weight-equal
              [(group
                "Over bought"
                [(weight-equal
                  [(if
                    (> (rsi "SPY" {:window 10}) 80)
                    [(asset "UVXY" nil)]
                    [(weight-equal
                      [(if
                        (> (rsi "QQQ" {:window 10}) 79)
                        [(asset
                          "UVXY"
                          "ProShares Ultra VIX Short-Term Futures ETF")]
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
                                    (> (rsi "XLK" {:window 10}) 79)
                                    [(asset
                                      "UVXY"
                                      "ProShares Ultra VIX Short-Term Futures ETF")]
                                    [(weight-equal
                                      [(if
                                        (> (rsi "XLP" {:window 10}) 75)
                                        [(asset
                                          "VIXY"
                                          "ProShares VIX Short-Term Futures ETF")]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (rsi "XLF" {:window 10})
                                             80)
                                            [(asset
                                              "UVXY"
                                              "ProShares Ultra VIX Short-Term Futures ETF")]
                                            [(group
                                              "Vol Check"
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
                                                          [(asset
                                                            "VIXM"
                                                            "ProShares VIX Mid-Term Futures ETF")]
                                                          [(asset
                                                            "SPXL"
                                                            "Direxion Daily S&P 500 Bull 3x Shares")])])])])]
                                                  [(group
                                                    "Vix Low"
                                                    [(weight-equal
                                                      [(if
                                                        (<
                                                         (rsi
                                                          "SOXX"
                                                          {:window 10})
                                                         30)
                                                        [(asset
                                                          "SOXL"
                                                          nil)]
                                                        [(weight-equal
                                                          [(if
                                                            (<
                                                             (rsi
                                                              "QQQ"
                                                              {:window
                                                               10})
                                                             30)
                                                            [(asset
                                                              "TECL"
                                                              nil)]
                                                            [(weight-equal
                                                              [(if
                                                                (<
                                                                 (rsi
                                                                  "SPY"
                                                                  {:window
                                                                   10})
                                                                 30)
                                                                [(asset
                                                                  "UPRO"
                                                                  nil)]
                                                                [(weight-equal
                                                                  [(if
                                                                    (>
                                                                     (rsi
                                                                      "SPY"
                                                                      {:window
                                                                       70})
                                                                     60)
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (rsi
                                                                         {:window
                                                                          10})
                                                                        (select-bottom
                                                                         1)
                                                                        [(asset
                                                                          "UGE"
                                                                          "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                         (asset
                                                                          "BOND"
                                                                          "Invesco Bond Fund")])])]
                                                                    [(weight-equal
                                                                      [(if
                                                                        (<
                                                                         (cumulative-return
                                                                          "QQQ"
                                                                          {:window
                                                                           5})
                                                                         -5)
                                                                        [(group
                                                                          "Oversold"
                                                                          [(weight-equal
                                                                            [(if
                                                                              (<
                                                                               (rsi
                                                                                "SPY"
                                                                                {:window
                                                                                 10})
                                                                               35)
                                                                              [(weight-equal
                                                                                [(asset
                                                                                  "TQQQ"
                                                                                  "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])]
                                                                              [(weight-equal
                                                                                [(filter
                                                                                  (rsi
                                                                                   {:window
                                                                                    10})
                                                                                  (select-bottom
                                                                                   1)
                                                                                  [(asset
                                                                                    "UGE"
                                                                                    "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                                   (asset
                                                                                    "BOND"
                                                                                    "Invesco Bond Fund")])])])])])]
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
                                                                                   (current-price
                                                                                    "QQQ")
                                                                                   (moving-average-price
                                                                                    "QQQ"
                                                                                    {:window
                                                                                     30}))
                                                                                  [(weight-equal
                                                                                    [(asset
                                                                                      "TQQQ"
                                                                                      "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])]
                                                                                  [(weight-equal
                                                                                    [(if
                                                                                      (>
                                                                                       (cumulative-return
                                                                                        "QQQ"
                                                                                        {:window
                                                                                         20})
                                                                                       (moving-average-return
                                                                                        "QQQ"
                                                                                        {:window
                                                                                         10}))
                                                                                      [(weight-equal
                                                                                        [(filter
                                                                                          (rsi
                                                                                           {:window
                                                                                            10})
                                                                                          (select-bottom
                                                                                           1)
                                                                                          [(asset
                                                                                            "UPRO"
                                                                                            "ProShares Trust - ProShares UltraPro S&P 500 ETF 3x Shares")
                                                                                           (asset
                                                                                            "TQQQ"
                                                                                            "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])]
                                                                                      [(weight-equal
                                                                                        [(filter
                                                                                          (rsi
                                                                                           {:window
                                                                                            10})
                                                                                          (select-bottom
                                                                                           1)
                                                                                          [(asset
                                                                                            "UGE"
                                                                                            "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                                           (asset
                                                                                            "BOND"
                                                                                            "Invesco Bond Fund")])])])])])])])]
                                                                            [(group
                                                                              "Bear"
                                                                              [(weight-equal
                                                                                [(filter
                                                                                  (rsi
                                                                                   {:window
                                                                                    10})
                                                                                  (select-bottom
                                                                                   1)
                                                                                  [(asset
                                                                                    "UGE"
                                                                                    "ProShares Trust - ProShares Ultra Consumer Staples")
                                                                                   (asset
                                                                                    "BOND"
                                                                                    "Invesco Bond Fund")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
       (group
        "EM Emerging Markets V0.4 (114,69,2009)"
        [(weight-equal
          [(if
            (< (rsi "EEM" {:window 15}) 30)
            [(asset
              "EDC"
              "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")]
            [(weight-equal
              [(if
                (>
                 (current-price "SHV")
                 (moving-average-price "SHV" {:window 50}))
                [(weight-equal
                  [(if
                    (>
                     (current-price "EEM")
                     (moving-average-price "EEM" {:window 200}))
                    [(group
                      "IEI vs IWM"
                      [(weight-equal
                        [(if
                          (>
                           (rsi "IEI" {:window 10})
                           (rsi "IWM" {:window 15}))
                          [(asset
                            "EDC"
                            "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")]
                          [(asset
                            "EDZ"
                            "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")])])])]
                    [(group
                      "IGIB vs EEM"
                      [(weight-equal
                        [(if
                          (>
                           (rsi "IGIB" {:window 15})
                           (rsi "EEM" {:window 15}))
                          [(asset
                            "EDC"
                            "Direxion Shares ETF Trust - Direxion Daily Emerging Markets Bull 3X Shares")]
                          [(asset
                            "EDZ"
                            "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")])])])])])]
                [(group
                  "IGIB vs SPY"
                  [(weight-equal
                    [(if
                      (>
                       (rsi "IGIB" {:window 10})
                       (rsi "SPY" {:window 10}))
                      [(asset "EEM" nil)]
                      [(asset
                        "EDZ"
                        "Direxion Shares ETF Trust - Direxion Daily MSCI Emerging Markets Bear -3x Shares")])])])])])])])])
       (group
        "Bonds Zoop V0.0 (144,38,2011)"
        [(weight-equal
          [(weight-equal
            [(if
              (>
               (current-price "TLT")
               (moving-average-price "TLT" {:window 200}))
              [(weight-equal
                [(if
                  (> (rsi "QLD" {:window 10}) 79)
                  [(asset
                    "UVXY"
                    "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
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
                              [(asset
                                "TMF"
                                "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                              [(asset
                                "TQQQ"
                                "ProShares UltraPro QQQ")])])]
                          [(weight-equal
                            [(if
                              (< (rsi "QLD" {:window 10}) 31)
                              [(asset "TQQQ" "ProShares UltraPro QQQ")]
                              [(asset
                                "BIL"
                                "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])]
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
                              (> (rsi "TMV" {:window 10}) 65)
                              [(asset
                                "TMV"
                                "Direxion Daily 20+ Year Treasury Bear 3x Shares")]
                              [(weight-equal
                                [(if
                                  (> (rsi "TMV" {:window 60}) 59)
                                  [(asset
                                    "TMF"
                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                                  [(asset
                                    "TMV"
                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])]
                          [(asset
                            "TMF"
                            "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])]
                      [(asset
                        "TMF"
                        "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])
       (group
        "Gold - V0.0 - (33,50,2009)"
        [(weight-equal
          [(if
            (>
             (moving-average-price "UGL" {:window 50})
             (moving-average-price "UGL" {:window 200}))
            [(weight-equal
              [(if
                (> (rsi "UGL" {:window 20}) 80)
                [(asset
                  "GLL"
                  "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                [(weight-equal
                  [(if
                    (> (rsi "UGL" {:window 10}) 90)
                    [(asset
                      "GLL"
                      "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                    [(weight-equal
                      [(if
                        (> (rsi "UGL" {:window 2}) 99.9)
                        [(asset
                          "GLL"
                          "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                        [(asset
                          "UGL"
                          "ProShares Trust - ProShares Ultra Gold 2x Shares")])])])])])])]
            [(weight-equal
              [(if
                (>
                 (moving-average-price "UGL" {:window 20})
                 (moving-average-price "UGL" {:window 50}))
                [(weight-equal
                  [(if
                    (> (rsi "UGL" {:window 20}) 75)
                    [(asset
                      "GLL"
                      "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                    [(weight-equal
                      [(if
                        (> (rsi "UGL" {:window 2}) 99.9)
                        [(asset
                          "GLL"
                          "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                        [(asset
                          "UGL"
                          "ProShares Trust - ProShares Ultra Gold 2x Shares")])])])])]
                [(weight-equal
                  [(if
                    (>
                     (moving-average-price "UGL" {:window 5})
                     (moving-average-price "UGL" {:window 10}))
                    [(weight-equal
                      [(if
                        (> (rsi "UGL" {:window 10}) 60)
                        [(asset
                          "GLL"
                          "ProShares Trust - ProShares UltraShort Gold -2x Shares")]
                        [(asset
                          "UGL"
                          "ProShares Trust - ProShares Ultra Gold 2x Shares")])])]
                    [(weight-equal
                      [(if
                        (< (rsi "UGL" {:window 20}) 30)
                        [(asset
                          "UGL"
                          "ProShares Trust - ProShares Ultra Gold 2x Shares")]
                        [(asset
                          "GLL"
                          "ProShares Trust - ProShares UltraShort Gold -2x Shares")])])])])])])])])])])])]))
