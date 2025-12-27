(defsymphony
 "Combo 10 General FrankRound's Chicken & Fried Rice V0.7 (96,11,2012)"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(group
    "Combo 10 General FrankRound's Chicken & Fried Rice V0.7 (96,11,2012)"
    [(weight-equal
      [(group
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
                          "ProShares Trust - ProShares UltraShort Gold -2x Shares")])])])])])])])])])
       (group
        "Bonds - V0.0 - (60,28,2009)"
        [(weight-equal
          [(if
            (> (rsi "TMF" {:window 10}) 85)
            [(asset
              "TMV"
              "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bear -3X Shares")]
            [(weight-equal
              [(if
                (< (rsi "TMF" {:window 10}) 32)
                [(asset
                  "TMF"
                  "Direxion Shares ETF Trust - Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                [(weight-equal
                  [(if
                    (>
                     (current-price "TLT")
                     (moving-average-price "TLT" {:window 200}))
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
                             (moving-average-price "TMF" {:window 10}))
                            [(asset
                              "TMF"
                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")]
                            [(asset
                              "BIL"
                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])]
                    [(weight-equal
                      [(if
                        (>
                         (moving-average-price "TMV" {:window 15})
                         (moving-average-price "TMV" {:window 50}))
                        [(weight-equal
                          [(if
                            (>
                             (current-price "TMV")
                             (moving-average-price
                              "TMV"
                              {:window 135}))
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
                          "Direxion Daily 20+ Year Treasury Bull 3X Shares")])])])])])])])])])
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
                      [(asset
                        "BOND"
                        "Pimco Exchange Traded Fund - PIMCO Active Bond ETF")])])])])])]
            [(weight-equal
              [(if
                (< (rsi "TQQQ" {:window 10}) 31)
                [(weight-equal
                  [(asset
                    "BOND"
                    "Pimco Exchange Traded Fund - PIMCO Active Bond ETF")])]
                [(weight-equal
                  [(if
                    (< (rsi "UPRO" {:window 10}) 31)
                    [(weight-equal
                      [(asset
                        "BOND"
                        "Pimco Exchange Traded Fund - PIMCO Active Bond ETF")])]
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
                                            [(weight-equal
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
                                                                      "XLP"
                                                                      "SSgA Active Trust - Consumer Staples Select Sector SPDR")
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
                                                                                "XLP"
                                                                                "SSgA Active Trust - Consumer Staples Select Sector SPDR")
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
                                                                                        "XLP"
                                                                                        "SSgA Active Trust - Consumer Staples Select Sector SPDR")
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
                                                                                "XLP"
                                                                                "SSgA Active Trust - Consumer Staples Select Sector SPDR")
                                                                               (asset
                                                                                "BOND"
                                                                                "Invesco Bond Fund")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
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
                                    [(weight-equal
                                      [(group
                                        "Vix Low"
                                        [(weight-equal
                                          [(if
                                            (<
                                             (rsi "SOXX" {:window 10})
                                             30)
                                            [(asset "SOXL" nil)]
                                            [(weight-equal
                                              [(if
                                                (<
                                                 (rsi
                                                  "QQQ"
                                                  {:window 10})
                                                 30)
                                                [(asset "TECL" nil)]
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
                                                                        "XLP"
                                                                        "SSgA Active Trust - Consumer Staples Select Sector SPDR")
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
                                                                  "XLP"
                                                                  "SSgA Active Trust - Consumer Staples Select Sector SPDR")
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
                                                                                    "XLP"
                                                                                    "SSgA Active Trust - Consumer Staples Select Sector SPDR")
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
                                                                                "XLP"
                                                                                "SSgA Active Trust - Consumer Staples Select Sector SPDR")
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
                                                                      nil)])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])])
       (group
        "Natural Gas Ng (17,50,2011)"
        [(weight-equal
          [(if
            (>
             (moving-average-price "FCG" {:window 100})
             (moving-average-price "FCG" {:window 500}))
            [(asset "BIL" nil)]
            [(weight-equal
              [(if
                (>
                 (moving-average-price "FCG" {:window 50})
                 (moving-average-price "FCG" {:window 400}))
                [(asset "FCG" nil)]
                [(group
                  "Long/Short"
                  [(weight-equal
                    [(if
                      (>
                       (current-price "FCG")
                       (moving-average-price "FCG" {:window 10}))
                      [(asset "FCG" nil)]
                      [(group
                        "KOLD Wrapper"
                        [(weight-equal
                          [(if
                            (< (rsi "UNG" {:window 10}) 25)
                            [(asset "BIL" nil)]
                            [(asset "KOLD" nil)])])])])])])
                 (asset "BIL" nil)])])])])])
       (group
        "Oil - V0.1 - (18,34,2009)"
        [(weight-equal
          [(if
            (< (rsi "UCO" {:window 10}) 14)
            [(asset "UCO" "ProShares Ultra Bloomberg Crude Oil")]
            [(weight-equal
              [(if
                (< (rsi "UCO" {:window 14}) 18)
                [(asset "UCO" "ProShares Ultra Bloomberg Crude Oil")]
                [(weight-equal
                  [(if
                    (< (rsi "UCO" {:window 20}) 22)
                    [(asset
                      "UCO"
                      "ProShares Ultra Bloomberg Crude Oil")]
                    [(group
                      "Oil Buy Signal"
                      [(weight-equal
                        [(if
                          (>
                           (current-price "DBO")
                           (moving-average-price "DBO" {:window 130}))
                          [(weight-equal
                            [(if
                              (>
                               (exponential-moving-average-price
                                "DBO"
                                {:window 8})
                               (moving-average-price
                                "DBO"
                                {:window 65}))
                              [(asset "DBO" "Invesco DB Oil Fund")]
                              [(asset
                                "SCO"
                                "ProShares Trust - ProShares UltraShort Bloomberg Crude Oil -2x Shares")])])]
                          [(asset
                            "BIL"
                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])])])])])])
       (group
        "ob os V0.1 (81,30,2011)"
        [(weight-equal
          [(if
            (< (rsi "QQQ" {:window 10}) 30)
            [(weight-equal
              [(filter
                (cumulative-return {:window 10})
                (select-bottom 1)
                [(asset
                  "TQQQ"
                  "ProShares Trust - ProShares UltraPro QQQ 3x Shares")
                 (asset
                  "TECL"
                  "Direxion Shares ETF Trust - Direxion Daily Technology Bull 3X Shares")
                 (asset
                  "SOXL"
                  "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")
                 (asset
                  "UPRO"
                  "ProShares Trust - ProShares UltraPro S&P 500 ETF 3x Shares")])])]
            [(weight-equal
              [(if
                (< (rsi "SPY" {:window 10}) 30)
                [(weight-equal
                  [(filter
                    (cumulative-return {:window 10})
                    (select-bottom 1)
                    [(asset
                      "TQQQ"
                      "ProShares Trust - ProShares UltraPro QQQ 3x Shares")
                     (asset
                      "TECL"
                      "Direxion Shares ETF Trust - Direxion Daily Technology Bull 3X Shares")
                     (asset
                      "SOXL"
                      "Direxion Shares ETF Trust - Direxion Daily Semiconductor Bull 3X Shares")
                     (asset
                      "UPRO"
                      "ProShares Trust - ProShares UltraPro S&P 500 ETF 3x Shares")])])]
                [(weight-equal
                  [(if
                    (> (rsi "QQQ" {:window 10}) 79)
                    [(weight-equal
                      [(asset
                        "UVXY"
                        "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")])]
                    [(weight-equal
                      [(if
                        (> (rsi "SPY" {:window 10}) 79)
                        [(weight-equal
                          [(asset
                            "UVXY"
                            "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")])]
                        [(weight-equal
                          [(filter
                            (rsi {:window 10})
                            (select-bottom 1)
                            [(asset
                              "XLP"
                              "SSgA Active Trust - Consumer Staples Select Sector SPDR")
                             (asset
                              "BOND"
                              "Pimco Exchange Traded Fund - PIMCO Active Bond ETF")])])])])])])])])])])])])])]))
