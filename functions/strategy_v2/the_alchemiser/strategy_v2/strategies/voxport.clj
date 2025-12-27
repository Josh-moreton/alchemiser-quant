(defsymphony
 "[VOXPORT] The Best Signals"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
    (> (rsi "QQQ" {:window 10}) 83)
    [(asset
      "UVXY"
      "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
    [(weight-equal
      [(if
        (> (rsi "SPY" {:window 10}) 81.5)
        [(asset
          "UVXY"
          "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
        [(weight-equal
          [(if
            (> (rsi "IOO" {:window 10}) 81.5)
            [(asset
              "UVXY"
              "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
            [(weight-equal
              [(if
                (> (rsi "VTV" {:window 10}) 83)
                [(asset
                  "UVXY"
                  "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
                [(weight-equal
                  [(if
                    (> (rsi "XLK" {:window 10}) 84)
                    [(asset
                      "UVXY"
                      "ProShares Trust - ProShares Ultra VIX Short-Term Futures ETF 2x Shares")]
                    [(weight-equal
                      [(if
                        (> (rsi "XLF" {:window 10}) 85)
                        [(asset
                          "BIL"
                          "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")]
                        [(weight-equal
                          [(filter
                            (cumulative-return {:window 10})
                            (select-top 4)
                            [(group
                              "HG"
                              [(weight-equal
                                [(group
                                  "Top 5 Leveraged | Holy Grail Structure | 2011-01-04"
                                  [(weight-equal
                                    [(if
                                      (>
                                       (current-price "SPY")
                                       (moving-average-price
                                        "SPY"
                                        {:window 200}))
                                      [(group
                                        "Compares"
                                        [(weight-equal
                                          [(group
                                            "20d TLT vs 20d PSQ | 2007-06-11"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "TLT"
                                                  {:window 20})
                                                 (rsi
                                                  "PSQ"
                                                  {:window 20}))
                                                [(asset "TQQQ" nil)]
                                                [(asset
                                                  "PSQ"
                                                  nil)])])])
                                           (group
                                            "20d AGG vs 60d SH | 2007-06-11"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "AGG"
                                                  {:window 20})
                                                 (rsi
                                                  "SH"
                                                  {:window 60}))
                                                [(asset "TQQQ" nil)]
                                                [(asset
                                                  "PSQ"
                                                  nil)])])])
                                           (group
                                            "20/60 -> 10/20 | 2007-05-30"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "AGG"
                                                  {:window 20})
                                                 (rsi
                                                  "SH"
                                                  {:window 60}))
                                                [(asset "TQQQ" nil)]
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "IEF"
                                                      {:window 10})
                                                     (rsi
                                                      "PSQ"
                                                      {:window 20}))
                                                    [(asset
                                                      "TQQQ"
                                                      nil)]
                                                    [(asset
                                                      "PSQ"
                                                      nil)])])])])])
                                           (group
                                            "60d BND vs 60d BIL | 2007-08-23"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (cumulative-return
                                                  "BND"
                                                  {:window 60})
                                                 (cumulative-return
                                                  "BIL"
                                                  {:window 60}))
                                                [(asset "TQQQ" nil)]
                                                [(asset
                                                  "PSQ"
                                                  nil)])])])
                                           (group
                                            "200d FDN vs 200d XLU | 2007-05-30"
                                            [(weight-equal
                                              [(if
                                                (>
                                                 (rsi
                                                  "FDN"
                                                  {:window 200})
                                                 (rsi
                                                  "XLU"
                                                  {:window 200}))
                                                [(asset "TQQQ" nil)]
                                                [(asset
                                                  "PSQ"
                                                  nil)])])])])])]
                                      [(weight-equal
                                        [(if
                                          (>
                                           (current-price "SPY")
                                           (moving-average-price
                                            "SPY"
                                            {:window 20}))
                                          [(group
                                            "Compares"
                                            [(weight-equal
                                              [(group
                                                "20d TLT vs 20d PSQ | 2007-06-11"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "TLT"
                                                      {:window 20})
                                                     (rsi
                                                      "PSQ"
                                                      {:window 20}))
                                                    [(asset
                                                      "TQQQ"
                                                      nil)]
                                                    [(asset
                                                      "PSQ"
                                                      nil)])])])
                                               (group
                                                "20d AGG vs 60d SH | 2007-06-11"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "AGG"
                                                      {:window 20})
                                                     (rsi
                                                      "SH"
                                                      {:window 60}))
                                                    [(asset
                                                      "TQQQ"
                                                      nil)]
                                                    [(asset
                                                      "PSQ"
                                                      nil)])])])
                                               (group
                                                "20/60 -> 10/20 | 2007-05-30"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "AGG"
                                                      {:window 20})
                                                     (rsi
                                                      "SH"
                                                      {:window 60}))
                                                    [(asset
                                                      "TQQQ"
                                                      nil)]
                                                    [(weight-equal
                                                      [(if
                                                        (>
                                                         (rsi
                                                          "IEF"
                                                          {:window 10})
                                                         (rsi
                                                          "PSQ"
                                                          {:window
                                                           20}))
                                                        [(asset
                                                          "TQQQ"
                                                          nil)]
                                                        [(asset
                                                          "PSQ"
                                                          nil)])])])])])
                                               (group
                                                "60d BND vs 60d BIL | 2007-08-23"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (cumulative-return
                                                      "BND"
                                                      {:window 60})
                                                     (cumulative-return
                                                      "BIL"
                                                      {:window 60}))
                                                    [(asset
                                                      "TQQQ"
                                                      nil)]
                                                    [(asset
                                                      "PSQ"
                                                      nil)])])])
                                               (group
                                                "200d FDN vs 200d XLU | 2007-05-30"
                                                [(weight-equal
                                                  [(if
                                                    (>
                                                     (rsi
                                                      "FDN"
                                                      {:window 200})
                                                     (rsi
                                                      "XLU"
                                                      {:window 200}))
                                                    [(asset
                                                      "TQQQ"
                                                      nil)]
                                                    [(asset
                                                      "PSQ"
                                                      nil)])])])])])]
                                          [(asset
                                            "PSQ"
                                            nil)])])])])])])])
                             (group
                              "KMLM"
                              [(weight-equal
                                [(group
                                  "KMLM Stuff"
                                  [(weight-equal
                                    [(group
                                      "20d MA"
                                      [(weight-equal
                                        [(if
                                          (<
                                           (current-price "KMLM")
                                           (moving-average-price
                                            "KMLM"
                                            {:window 20}))
                                          [(weight-equal
                                            [(asset "TQQQ" nil)])]
                                          [(weight-equal
                                            [(if
                                              (<
                                               (current-price "SPY")
                                               (moving-average-price
                                                "SPY"
                                                {:window 200}))
                                              [(asset "SQQQ" nil)]
                                              [(asset
                                                "PSQ"
                                                nil)])])])])])
                                     (group
                                      "XLK"
                                      [(weight-equal
                                        [(if
                                          (>
                                           (rsi "XLK" {:window 10})
                                           (rsi "KMLM" {:window 10}))
                                          [(weight-equal
                                            [(asset "TQQQ" nil)])]
                                          [(weight-equal
                                            [(if
                                              (<
                                               (current-price "SPY")
                                               (moving-average-price
                                                "SPY"
                                                {:window 200}))
                                              [(asset "SQQQ" nil)]
                                              [(asset
                                                "PSQ"
                                                nil)])])])])])
                                     (group
                                      "SPY"
                                      [(weight-equal
                                        [(if
                                          (>
                                           (rsi "SPY" {:window 10})
                                           (rsi "KMLM" {:window 10}))
                                          [(weight-equal
                                            [(asset "TQQQ" nil)])]
                                          [(weight-equal
                                            [(if
                                              (<
                                               (current-price "SPY")
                                               (moving-average-price
                                                "SPY"
                                                {:window 200}))
                                              [(asset "SQQQ" nil)]
                                              [(asset
                                                "PSQ"
                                                nil)])])])])])])])])])
                             (group
                              "Paretos Signals Compilation"
                              [(weight-equal
                                [(filter
                                  (cumulative-return {:window 10})
                                  (select-top 3)
                                  [(group
                                    "Bond Direction"
                                    [(weight-equal
                                      [(if
                                        (>
                                         (cumulative-return
                                          "BND"
                                          {:window 60})
                                         (cumulative-return
                                          "BIL"
                                          {:window 60}))
                                        [(group
                                          "Risk on"
                                          [(weight-equal
                                            [(group
                                              "Risk-On - Stable/Normal rates"
                                              [(weight-equal
                                                [(group
                                                  "SPY"
                                                  [(weight-equal
                                                    [(filter
                                                      (moving-average-return
                                                       {:window 20})
                                                      (select-top 3)
                                                      [(asset
                                                        "AAPL"
                                                        "Apple Inc.")
                                                       (asset
                                                        "MSFT"
                                                        "Microsoft Corporation")
                                                       (asset
                                                        "AMZN"
                                                        "Amazon.com, Inc.")
                                                       (asset
                                                        "NVDA"
                                                        "NVIDIA Corporation")
                                                       (asset
                                                        "TSLA"
                                                        "Tesla, Inc.")
                                                       (asset
                                                        "GOOG"
                                                        "Alphabet Inc. Class C")
                                                       (asset
                                                        "GOOGL"
                                                        "Alphabet Inc. Class A")
                                                       (asset
                                                        "META"
                                                        "Meta Platforms Inc. Class A")
                                                       (asset
                                                        "BRK/B"
                                                        "Berkshire Hathaway Inc. Class B")
                                                       (asset
                                                        "JNJ"
                                                        "Johnson & Johnson")
                                                       (asset
                                                        "JPM"
                                                        "JPMorgan Chase & Co.")
                                                       (asset
                                                        "XOM"
                                                        "Exxon Mobil Corporation")
                                                       (asset
                                                        "V"
                                                        "Visa Inc. Class A")
                                                       (asset
                                                        "LLY"
                                                        "Eli Lilly and Company")
                                                       (asset
                                                        "AVGO"
                                                        "Broadcom Inc")])])])
                                                 (group
                                                  "QQQ"
                                                  [(weight-equal
                                                    [(filter
                                                      (moving-average-return
                                                       {:window 20})
                                                      (select-top 3)
                                                      [(asset
                                                        "NFLX"
                                                        "Netflix, Inc.")
                                                       (asset
                                                        "CSCO"
                                                        "Cisco Systems, Inc.")
                                                       (asset
                                                        "COST"
                                                        "Costco Wholesale Corporation")
                                                       (asset
                                                        "AVGO"
                                                        "Broadcom Inc.")
                                                       (asset
                                                        "GOOG"
                                                        "Alphabet Inc. Class C")
                                                       (asset
                                                        "GOOGL"
                                                        "Alphabet Inc. Class A")
                                                       (asset
                                                        "META"
                                                        "Meta Platforms Inc. Class A")
                                                       (asset
                                                        "TSLA"
                                                        "Tesla, Inc.")
                                                       (asset
                                                        "AMZN"
                                                        "Amazon.com, Inc.")
                                                       (asset
                                                        "NVDA"
                                                        "NVIDIA Corporation")
                                                       (asset
                                                        "AAPL"
                                                        "Apple Inc.")
                                                       (asset
                                                        "MSFT"
                                                        "Microsoft Corporation")
                                                       (asset
                                                        "LIN"
                                                        "Linde Plc.")
                                                       (asset
                                                        "PLTR"
                                                        "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                       (asset
                                                        "TMUS"
                                                        "T-Mobile US Inc")])])])
                                                 (group
                                                  "DIA"
                                                  [(weight-equal
                                                    [(filter
                                                      (moving-average-return
                                                       {:window 20})
                                                      (select-top 3)
                                                      [(asset
                                                        "UNH"
                                                        "UnitedHealth Group Incorporated")
                                                       (asset
                                                        "MSFT"
                                                        "Microsoft Corporation")
                                                       (asset
                                                        "GS"
                                                        "Goldman Sachs Group, Inc.")
                                                       (asset
                                                        "HD"
                                                        "Home Depot, Inc.")
                                                       (asset
                                                        "MCD"
                                                        "McDonald's Corporation")
                                                       (asset
                                                        "TRV"
                                                        "Travelers Companies, Inc.")
                                                       (asset
                                                        "AXP"
                                                        "American Express Company")
                                                       (asset
                                                        "AAPL"
                                                        "Apple Inc.")
                                                       (asset
                                                        "CRM"
                                                        "Salesforce, Inc.")
                                                       (asset
                                                        "AMGN"
                                                        "Amgen Inc.")
                                                       (asset
                                                        "V"
                                                        "Visa Inc. Class A")
                                                       (asset
                                                        "CAT"
                                                        "Caterpillar Inc.")
                                                       (asset
                                                        "IBM"
                                                        "International Business Machines Corp.")
                                                       (asset
                                                        "JPM"
                                                        "JPMorgan Chase & Co.")])])])])])])])]
                                        [(group
                                          "Risk Off"
                                          [(weight-equal
                                            [(group
                                              "Commodities"
                                              [(weight-equal
                                                [(filter
                                                  (moving-average-return
                                                   {:window 10})
                                                  (select-top 2)
                                                  [(asset
                                                    "COM"
                                                    "Direxion Auspice Broad Commodity Strategy ETF")
                                                   (asset
                                                    "FAAR"
                                                    "First Trust Alternative Absolute Return Strategy ETF")
                                                   (asset
                                                    "FTGC"
                                                    "First Trust Global Tactical Commodity Strategy Fund")
                                                   (asset
                                                    "DBC"
                                                    "Invesco DB Commodity Index Tracking Fund")
                                                   (asset
                                                    "PDBC"
                                                    "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                   (asset
                                                    "DBA"
                                                    "Invesco DB Agriculture Fund")
                                                   (asset
                                                    "GLTR"
                                                    "abrdn Physical Precious Metals Basket Shares ETF")
                                                   (asset
                                                    "DBB"
                                                    "Invesco DB Base Metals Fund")])
                                                 (filter
                                                  (max-drawdown
                                                   {:window 20})
                                                  (select-bottom 2)
                                                  [(asset
                                                    "COM"
                                                    "Direxion Auspice Broad Commodity Strategy ETF")
                                                   (asset
                                                    "FAAR"
                                                    "First Trust Alternative Absolute Return Strategy ETF")
                                                   (asset
                                                    "FTGC"
                                                    "First Trust Global Tactical Commodity Strategy Fund")
                                                   (asset
                                                    "DBC"
                                                    "Invesco DB Commodity Index Tracking Fund")
                                                   (asset
                                                    "PDBC"
                                                    "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                   (asset
                                                    "DBA"
                                                    "Invesco DB Agriculture Fund")
                                                   (asset
                                                    "GLTR"
                                                    "abrdn Physical Precious Metals Basket Shares ETF")
                                                   (asset
                                                    "DBB"
                                                    "Invesco DB Base Metals Fund")])])])
                                             (group
                                              "Bonds"
                                              [(weight-equal
                                                [(filter
                                                  (moving-average-return
                                                   {:window 10})
                                                  (select-top 3)
                                                  [(asset
                                                    "AGG"
                                                    "iShares Core U.S. Aggregate Bond ETF")
                                                   (asset
                                                    "BND"
                                                    "Vanguard Total Bond Market ETF")
                                                   (asset
                                                    "BNDX"
                                                    "Vanguard Total International Bond ETF")
                                                   (asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                   (asset
                                                    "IEF"
                                                    "iShares 7-10 Year Treasury Bond ETF")
                                                   (asset
                                                    "EMB"
                                                    "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                   (asset
                                                    "BWX"
                                                    "SPDR Bloomberg International Treasury Bond ETF")
                                                   (asset
                                                    "SHV"
                                                    "iShares Short Treasury Bond ETF")
                                                   (asset
                                                    "VGSH"
                                                    "Vanguard Short-Term Treasury ETF")
                                                   (asset
                                                    "GBIL"
                                                    "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                   (asset
                                                    "TYD"
                                                    "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                   (asset
                                                    "HYG"
                                                    "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                   (asset
                                                    "TBT"
                                                    "ProShares UltraShort 20+ Year Treasury")
                                                   (asset
                                                    "TMV"
                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                 (filter
                                                  (max-drawdown
                                                   {:window 20})
                                                  (select-bottom 3)
                                                  [(asset
                                                    "AGG"
                                                    "iShares Core U.S. Aggregate Bond ETF")
                                                   (asset
                                                    "BND"
                                                    "Vanguard Total Bond Market ETF")
                                                   (asset
                                                    "BNDX"
                                                    "Vanguard Total International Bond ETF")
                                                   (asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                   (asset
                                                    "IEF"
                                                    "iShares 7-10 Year Treasury Bond ETF")
                                                   (asset
                                                    "EMB"
                                                    "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                   (asset
                                                    "BWX"
                                                    "SPDR Bloomberg International Treasury Bond ETF")
                                                   (asset
                                                    "SHV"
                                                    "iShares Short Treasury Bond ETF")
                                                   (asset
                                                    "VGSH"
                                                    "Vanguard Short-Term Treasury ETF")
                                                   (asset
                                                    "GBIL"
                                                    "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                   (asset
                                                    "TYD"
                                                    "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                   (asset
                                                    "HYG"
                                                    "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                   (asset
                                                    "TBT"
                                                    "ProShares UltraShort 20+ Year Treasury")
                                                   (asset
                                                    "TMV"
                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])
                                   (group
                                    "Market Trajectory (SPY MA)"
                                    [(weight-equal
                                      [(if
                                        (>
                                         (cumulative-return
                                          "SPY"
                                          {:window 50})
                                         (cumulative-return
                                          "SPY"
                                          {:window 200}))
                                        [(group
                                          "Risk on"
                                          [(weight-equal
                                            [(group
                                              "Risk-On - Stable/Normal rates"
                                              [(weight-equal
                                                [(group
                                                  "SPY"
                                                  [(weight-equal
                                                    [(filter
                                                      (moving-average-return
                                                       {:window 20})
                                                      (select-top 3)
                                                      [(asset
                                                        "AAPL"
                                                        "Apple Inc.")
                                                       (asset
                                                        "MSFT"
                                                        "Microsoft Corporation")
                                                       (asset
                                                        "AMZN"
                                                        "Amazon.com, Inc.")
                                                       (asset
                                                        "NVDA"
                                                        "NVIDIA Corporation")
                                                       (asset
                                                        "TSLA"
                                                        "Tesla, Inc.")
                                                       (asset
                                                        "GOOG"
                                                        "Alphabet Inc. Class C")
                                                       (asset
                                                        "GOOGL"
                                                        "Alphabet Inc. Class A")
                                                       (asset
                                                        "META"
                                                        "Meta Platforms Inc. Class A")
                                                       (asset
                                                        "BRK/B"
                                                        "Berkshire Hathaway Inc. Class B")
                                                       (asset
                                                        "JNJ"
                                                        "Johnson & Johnson")
                                                       (asset
                                                        "JPM"
                                                        "JPMorgan Chase & Co.")
                                                       (asset
                                                        "XOM"
                                                        "Exxon Mobil Corporation")
                                                       (asset
                                                        "V"
                                                        "Visa Inc. Class A")
                                                       (asset
                                                        "LLY"
                                                        "Eli Lilly and Company")
                                                       (asset
                                                        "AVGO"
                                                        "Broadcom Inc")])])])
                                                 (group
                                                  "QQQ"
                                                  [(weight-equal
                                                    [(filter
                                                      (moving-average-return
                                                       {:window 20})
                                                      (select-top 3)
                                                      [(asset
                                                        "NFLX"
                                                        "Netflix, Inc.")
                                                       (asset
                                                        "CSCO"
                                                        "Cisco Systems, Inc.")
                                                       (asset
                                                        "COST"
                                                        "Costco Wholesale Corporation")
                                                       (asset
                                                        "AVGO"
                                                        "Broadcom Inc.")
                                                       (asset
                                                        "GOOG"
                                                        "Alphabet Inc. Class C")
                                                       (asset
                                                        "GOOGL"
                                                        "Alphabet Inc. Class A")
                                                       (asset
                                                        "META"
                                                        "Meta Platforms Inc. Class A")
                                                       (asset
                                                        "TSLA"
                                                        "Tesla, Inc.")
                                                       (asset
                                                        "AMZN"
                                                        "Amazon.com, Inc.")
                                                       (asset
                                                        "NVDA"
                                                        "NVIDIA Corporation")
                                                       (asset
                                                        "AAPL"
                                                        "Apple Inc.")
                                                       (asset
                                                        "MSFT"
                                                        "Microsoft Corporation")
                                                       (asset
                                                        "LIN"
                                                        "Linde Plc.")
                                                       (asset
                                                        "PLTR"
                                                        "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                       (asset
                                                        "TMUS"
                                                        "T-Mobile US Inc")])])])
                                                 (group
                                                  "DIA"
                                                  [(weight-equal
                                                    [(filter
                                                      (moving-average-return
                                                       {:window 20})
                                                      (select-top 3)
                                                      [(asset
                                                        "UNH"
                                                        "UnitedHealth Group Incorporated")
                                                       (asset
                                                        "MSFT"
                                                        "Microsoft Corporation")
                                                       (asset
                                                        "GS"
                                                        "Goldman Sachs Group, Inc.")
                                                       (asset
                                                        "HD"
                                                        "Home Depot, Inc.")
                                                       (asset
                                                        "MCD"
                                                        "McDonald's Corporation")
                                                       (asset
                                                        "TRV"
                                                        "Travelers Companies, Inc.")
                                                       (asset
                                                        "AXP"
                                                        "American Express Company")
                                                       (asset
                                                        "AAPL"
                                                        "Apple Inc.")
                                                       (asset
                                                        "CRM"
                                                        "Salesforce, Inc.")
                                                       (asset
                                                        "AMGN"
                                                        "Amgen Inc.")
                                                       (asset
                                                        "V"
                                                        "Visa Inc. Class A")
                                                       (asset
                                                        "CAT"
                                                        "Caterpillar Inc.")
                                                       (asset
                                                        "IBM"
                                                        "International Business Machines Corp.")
                                                       (asset
                                                        "JPM"
                                                        "JPMorgan Chase & Co.")])])])])])])])]
                                        [(group
                                          "Risk Off"
                                          [(weight-equal
                                            [(group
                                              "Commodities"
                                              [(weight-equal
                                                [(filter
                                                  (moving-average-return
                                                   {:window 10})
                                                  (select-top 2)
                                                  [(asset
                                                    "COM"
                                                    "Direxion Auspice Broad Commodity Strategy ETF")
                                                   (asset
                                                    "FAAR"
                                                    "First Trust Alternative Absolute Return Strategy ETF")
                                                   (asset
                                                    "FTGC"
                                                    "First Trust Global Tactical Commodity Strategy Fund")
                                                   (asset
                                                    "DBC"
                                                    "Invesco DB Commodity Index Tracking Fund")
                                                   (asset
                                                    "PDBC"
                                                    "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                   (asset
                                                    "DBA"
                                                    "Invesco DB Agriculture Fund")
                                                   (asset
                                                    "GLTR"
                                                    "abrdn Physical Precious Metals Basket Shares ETF")
                                                   (asset
                                                    "DBB"
                                                    "Invesco DB Base Metals Fund")])
                                                 (filter
                                                  (max-drawdown
                                                   {:window 20})
                                                  (select-bottom 2)
                                                  [(asset
                                                    "COM"
                                                    "Direxion Auspice Broad Commodity Strategy ETF")
                                                   (asset
                                                    "FAAR"
                                                    "First Trust Alternative Absolute Return Strategy ETF")
                                                   (asset
                                                    "FTGC"
                                                    "First Trust Global Tactical Commodity Strategy Fund")
                                                   (asset
                                                    "DBC"
                                                    "Invesco DB Commodity Index Tracking Fund")
                                                   (asset
                                                    "PDBC"
                                                    "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                   (asset
                                                    "DBA"
                                                    "Invesco DB Agriculture Fund")
                                                   (asset
                                                    "GLTR"
                                                    "abrdn Physical Precious Metals Basket Shares ETF")
                                                   (asset
                                                    "DBB"
                                                    "Invesco DB Base Metals Fund")])])])
                                             (group
                                              "Bonds"
                                              [(weight-equal
                                                [(filter
                                                  (moving-average-return
                                                   {:window 10})
                                                  (select-top 3)
                                                  [(asset
                                                    "AGG"
                                                    "iShares Core U.S. Aggregate Bond ETF")
                                                   (asset
                                                    "BND"
                                                    "Vanguard Total Bond Market ETF")
                                                   (asset
                                                    "BNDX"
                                                    "Vanguard Total International Bond ETF")
                                                   (asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                   (asset
                                                    "IEF"
                                                    "iShares 7-10 Year Treasury Bond ETF")
                                                   (asset
                                                    "EMB"
                                                    "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                   (asset
                                                    "BWX"
                                                    "SPDR Bloomberg International Treasury Bond ETF")
                                                   (asset
                                                    "SHV"
                                                    "iShares Short Treasury Bond ETF")
                                                   (asset
                                                    "VGSH"
                                                    "Vanguard Short-Term Treasury ETF")
                                                   (asset
                                                    "GBIL"
                                                    "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                   (asset
                                                    "TYD"
                                                    "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                   (asset
                                                    "HYG"
                                                    "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                   (asset
                                                    "TBT"
                                                    "ProShares UltraShort 20+ Year Treasury")
                                                   (asset
                                                    "TMV"
                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                 (filter
                                                  (max-drawdown
                                                   {:window 20})
                                                  (select-bottom 3)
                                                  [(asset
                                                    "AGG"
                                                    "iShares Core U.S. Aggregate Bond ETF")
                                                   (asset
                                                    "BND"
                                                    "Vanguard Total Bond Market ETF")
                                                   (asset
                                                    "BNDX"
                                                    "Vanguard Total International Bond ETF")
                                                   (asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                   (asset
                                                    "IEF"
                                                    "iShares 7-10 Year Treasury Bond ETF")
                                                   (asset
                                                    "EMB"
                                                    "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                   (asset
                                                    "BWX"
                                                    "SPDR Bloomberg International Treasury Bond ETF")
                                                   (asset
                                                    "SHV"
                                                    "iShares Short Treasury Bond ETF")
                                                   (asset
                                                    "VGSH"
                                                    "Vanguard Short-Term Treasury ETF")
                                                   (asset
                                                    "GBIL"
                                                    "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                   (asset
                                                    "TYD"
                                                    "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                   (asset
                                                    "HYG"
                                                    "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                   (asset
                                                    "TBT"
                                                    "ProShares UltraShort 20+ Year Treasury")
                                                   (asset
                                                    "TMV"
                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])
                                   (group
                                    "Inflation Check"
                                    [(weight-equal
                                      [(if
                                        (>
                                         (cumulative-return
                                          "TIP"
                                          {:window 60})
                                         0)
                                        [(group
                                          "Risk on"
                                          [(weight-equal
                                            [(group
                                              "Risk-On - Stable/Normal rates"
                                              [(weight-equal
                                                [(group
                                                  "SPY"
                                                  [(weight-equal
                                                    [(filter
                                                      (moving-average-return
                                                       {:window 20})
                                                      (select-top 3)
                                                      [(asset
                                                        "AAPL"
                                                        "Apple Inc.")
                                                       (asset
                                                        "MSFT"
                                                        "Microsoft Corporation")
                                                       (asset
                                                        "AMZN"
                                                        "Amazon.com, Inc.")
                                                       (asset
                                                        "NVDA"
                                                        "NVIDIA Corporation")
                                                       (asset
                                                        "TSLA"
                                                        "Tesla, Inc.")
                                                       (asset
                                                        "GOOG"
                                                        "Alphabet Inc. Class C")
                                                       (asset
                                                        "GOOGL"
                                                        "Alphabet Inc. Class A")
                                                       (asset
                                                        "META"
                                                        "Meta Platforms Inc. Class A")
                                                       (asset
                                                        "BRK/B"
                                                        "Berkshire Hathaway Inc. Class B")
                                                       (asset
                                                        "JNJ"
                                                        "Johnson & Johnson")
                                                       (asset
                                                        "JPM"
                                                        "JPMorgan Chase & Co.")
                                                       (asset
                                                        "XOM"
                                                        "Exxon Mobil Corporation")
                                                       (asset
                                                        "V"
                                                        "Visa Inc. Class A")
                                                       (asset
                                                        "LLY"
                                                        "Eli Lilly and Company")
                                                       (asset
                                                        "AVGO"
                                                        "Broadcom Inc")])])])
                                                 (group
                                                  "QQQ"
                                                  [(weight-equal
                                                    [(filter
                                                      (moving-average-return
                                                       {:window 20})
                                                      (select-top 3)
                                                      [(asset
                                                        "NFLX"
                                                        "Netflix, Inc.")
                                                       (asset
                                                        "CSCO"
                                                        "Cisco Systems, Inc.")
                                                       (asset
                                                        "COST"
                                                        "Costco Wholesale Corporation")
                                                       (asset
                                                        "AVGO"
                                                        "Broadcom Inc.")
                                                       (asset
                                                        "GOOG"
                                                        "Alphabet Inc. Class C")
                                                       (asset
                                                        "GOOGL"
                                                        "Alphabet Inc. Class A")
                                                       (asset
                                                        "META"
                                                        "Meta Platforms Inc. Class A")
                                                       (asset
                                                        "TSLA"
                                                        "Tesla, Inc.")
                                                       (asset
                                                        "AMZN"
                                                        "Amazon.com, Inc.")
                                                       (asset
                                                        "NVDA"
                                                        "NVIDIA Corporation")
                                                       (asset
                                                        "AAPL"
                                                        "Apple Inc.")
                                                       (asset
                                                        "MSFT"
                                                        "Microsoft Corporation")
                                                       (asset
                                                        "LIN"
                                                        "Linde Plc.")
                                                       (asset
                                                        "PLTR"
                                                        "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                       (asset
                                                        "TMUS"
                                                        "T-Mobile US Inc")])])])
                                                 (group
                                                  "DIA"
                                                  [(weight-equal
                                                    [(filter
                                                      (moving-average-return
                                                       {:window 20})
                                                      (select-top 3)
                                                      [(asset
                                                        "UNH"
                                                        "UnitedHealth Group Incorporated")
                                                       (asset
                                                        "MSFT"
                                                        "Microsoft Corporation")
                                                       (asset
                                                        "GS"
                                                        "Goldman Sachs Group, Inc.")
                                                       (asset
                                                        "HD"
                                                        "Home Depot, Inc.")
                                                       (asset
                                                        "MCD"
                                                        "McDonald's Corporation")
                                                       (asset
                                                        "TRV"
                                                        "Travelers Companies, Inc.")
                                                       (asset
                                                        "AXP"
                                                        "American Express Company")
                                                       (asset
                                                        "AAPL"
                                                        "Apple Inc.")
                                                       (asset
                                                        "CRM"
                                                        "Salesforce, Inc.")
                                                       (asset
                                                        "AMGN"
                                                        "Amgen Inc.")
                                                       (asset
                                                        "V"
                                                        "Visa Inc. Class A")
                                                       (asset
                                                        "CAT"
                                                        "Caterpillar Inc.")
                                                       (asset
                                                        "IBM"
                                                        "International Business Machines Corp.")
                                                       (asset
                                                        "JPM"
                                                        "JPMorgan Chase & Co.")])])])])])])])]
                                        [(group
                                          "Risk Off"
                                          [(weight-equal
                                            [(group
                                              "Commodities"
                                              [(weight-equal
                                                [(filter
                                                  (moving-average-return
                                                   {:window 10})
                                                  (select-top 2)
                                                  [(asset
                                                    "COM"
                                                    "Direxion Auspice Broad Commodity Strategy ETF")
                                                   (asset
                                                    "FAAR"
                                                    "First Trust Alternative Absolute Return Strategy ETF")
                                                   (asset
                                                    "FTGC"
                                                    "First Trust Global Tactical Commodity Strategy Fund")
                                                   (asset
                                                    "DBC"
                                                    "Invesco DB Commodity Index Tracking Fund")
                                                   (asset
                                                    "PDBC"
                                                    "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                   (asset
                                                    "DBA"
                                                    "Invesco DB Agriculture Fund")
                                                   (asset
                                                    "GLTR"
                                                    "abrdn Physical Precious Metals Basket Shares ETF")
                                                   (asset
                                                    "DBB"
                                                    "Invesco DB Base Metals Fund")])
                                                 (filter
                                                  (max-drawdown
                                                   {:window 20})
                                                  (select-bottom 2)
                                                  [(asset
                                                    "COM"
                                                    "Direxion Auspice Broad Commodity Strategy ETF")
                                                   (asset
                                                    "FAAR"
                                                    "First Trust Alternative Absolute Return Strategy ETF")
                                                   (asset
                                                    "FTGC"
                                                    "First Trust Global Tactical Commodity Strategy Fund")
                                                   (asset
                                                    "DBC"
                                                    "Invesco DB Commodity Index Tracking Fund")
                                                   (asset
                                                    "PDBC"
                                                    "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                   (asset
                                                    "DBA"
                                                    "Invesco DB Agriculture Fund")
                                                   (asset
                                                    "GLTR"
                                                    "abrdn Physical Precious Metals Basket Shares ETF")
                                                   (asset
                                                    "DBB"
                                                    "Invesco DB Base Metals Fund")])])])
                                             (group
                                              "Bonds"
                                              [(weight-equal
                                                [(filter
                                                  (moving-average-return
                                                   {:window 10})
                                                  (select-top 3)
                                                  [(asset
                                                    "AGG"
                                                    "iShares Core U.S. Aggregate Bond ETF")
                                                   (asset
                                                    "BND"
                                                    "Vanguard Total Bond Market ETF")
                                                   (asset
                                                    "BNDX"
                                                    "Vanguard Total International Bond ETF")
                                                   (asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                   (asset
                                                    "IEF"
                                                    "iShares 7-10 Year Treasury Bond ETF")
                                                   (asset
                                                    "EMB"
                                                    "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                   (asset
                                                    "BWX"
                                                    "SPDR Bloomberg International Treasury Bond ETF")
                                                   (asset
                                                    "SHV"
                                                    "iShares Short Treasury Bond ETF")
                                                   (asset
                                                    "VGSH"
                                                    "Vanguard Short-Term Treasury ETF")
                                                   (asset
                                                    "GBIL"
                                                    "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                   (asset
                                                    "TYD"
                                                    "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                   (asset
                                                    "HYG"
                                                    "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                   (asset
                                                    "TBT"
                                                    "ProShares UltraShort 20+ Year Treasury")
                                                   (asset
                                                    "TMV"
                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                 (filter
                                                  (max-drawdown
                                                   {:window 20})
                                                  (select-bottom 3)
                                                  [(asset
                                                    "AGG"
                                                    "iShares Core U.S. Aggregate Bond ETF")
                                                   (asset
                                                    "BND"
                                                    "Vanguard Total Bond Market ETF")
                                                   (asset
                                                    "BNDX"
                                                    "Vanguard Total International Bond ETF")
                                                   (asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                   (asset
                                                    "IEF"
                                                    "iShares 7-10 Year Treasury Bond ETF")
                                                   (asset
                                                    "EMB"
                                                    "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                   (asset
                                                    "BWX"
                                                    "SPDR Bloomberg International Treasury Bond ETF")
                                                   (asset
                                                    "SHV"
                                                    "iShares Short Treasury Bond ETF")
                                                   (asset
                                                    "VGSH"
                                                    "Vanguard Short-Term Treasury ETF")
                                                   (asset
                                                    "GBIL"
                                                    "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                   (asset
                                                    "TYD"
                                                    "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                   (asset
                                                    "HYG"
                                                    "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                   (asset
                                                    "TBT"
                                                    "ProShares UltraShort 20+ Year Treasury")
                                                   (asset
                                                    "TMV"
                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])
                                   (group
                                    "HG"
                                    [(weight-equal
                                      [(if
                                        (>
                                         (current-price "SPY")
                                         (moving-average-price
                                          "SPY"
                                          {:window 200}))
                                        [(group
                                          "Compares"
                                          [(weight-equal
                                            [(group
                                              "20d TLT vs 20d PSQ | 2007-06-11"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (rsi
                                                    "TLT"
                                                    {:window 20})
                                                   (rsi
                                                    "PSQ"
                                                    {:window 20}))
                                                  [(group
                                                    "Risk on"
                                                    [(weight-equal
                                                      [(group
                                                        "Risk-On - Stable/Normal rates"
                                                        [(weight-equal
                                                          [(group
                                                            "SPY"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "AMZN"
                                                                  "Amazon.com, Inc.")
                                                                 (asset
                                                                  "NVDA"
                                                                  "NVIDIA Corporation")
                                                                 (asset
                                                                  "TSLA"
                                                                  "Tesla, Inc.")
                                                                 (asset
                                                                  "GOOG"
                                                                  "Alphabet Inc. Class C")
                                                                 (asset
                                                                  "GOOGL"
                                                                  "Alphabet Inc. Class A")
                                                                 (asset
                                                                  "META"
                                                                  "Meta Platforms Inc. Class A")
                                                                 (asset
                                                                  "BRK/B"
                                                                  "Berkshire Hathaway Inc. Class B")
                                                                 (asset
                                                                  "JNJ"
                                                                  "Johnson & Johnson")
                                                                 (asset
                                                                  "JPM"
                                                                  "JPMorgan Chase & Co.")
                                                                 (asset
                                                                  "XOM"
                                                                  "Exxon Mobil Corporation")
                                                                 (asset
                                                                  "V"
                                                                  "Visa Inc. Class A")
                                                                 (asset
                                                                  "LLY"
                                                                  "Eli Lilly and Company")
                                                                 (asset
                                                                  "AVGO"
                                                                  "Broadcom Inc")])])])
                                                           (group
                                                            "QQQ"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "NFLX"
                                                                  "Netflix, Inc.")
                                                                 (asset
                                                                  "CSCO"
                                                                  "Cisco Systems, Inc.")
                                                                 (asset
                                                                  "COST"
                                                                  "Costco Wholesale Corporation")
                                                                 (asset
                                                                  "AVGO"
                                                                  "Broadcom Inc.")
                                                                 (asset
                                                                  "GOOG"
                                                                  "Alphabet Inc. Class C")
                                                                 (asset
                                                                  "GOOGL"
                                                                  "Alphabet Inc. Class A")
                                                                 (asset
                                                                  "META"
                                                                  "Meta Platforms Inc. Class A")
                                                                 (asset
                                                                  "TSLA"
                                                                  "Tesla, Inc.")
                                                                 (asset
                                                                  "AMZN"
                                                                  "Amazon.com, Inc.")
                                                                 (asset
                                                                  "NVDA"
                                                                  "NVIDIA Corporation")
                                                                 (asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "LIN"
                                                                  "Linde Plc.")
                                                                 (asset
                                                                  "PLTR"
                                                                  "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                                 (asset
                                                                  "TMUS"
                                                                  "T-Mobile US Inc")])])])
                                                           (group
                                                            "DIA"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "UNH"
                                                                  "UnitedHealth Group Incorporated")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "GS"
                                                                  "Goldman Sachs Group, Inc.")
                                                                 (asset
                                                                  "HD"
                                                                  "Home Depot, Inc.")
                                                                 (asset
                                                                  "MCD"
                                                                  "McDonald's Corporation")
                                                                 (asset
                                                                  "TRV"
                                                                  "Travelers Companies, Inc.")
                                                                 (asset
                                                                  "AXP"
                                                                  "American Express Company")
                                                                 (asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "CRM"
                                                                  "Salesforce, Inc.")
                                                                 (asset
                                                                  "AMGN"
                                                                  "Amgen Inc.")
                                                                 (asset
                                                                  "V"
                                                                  "Visa Inc. Class A")
                                                                 (asset
                                                                  "CAT"
                                                                  "Caterpillar Inc.")
                                                                 (asset
                                                                  "IBM"
                                                                  "International Business Machines Corp.")
                                                                 (asset
                                                                  "JPM"
                                                                  "JPMorgan Chase & Co.")])])])])])])])]
                                                  [(group
                                                    "Risk Off"
                                                    [(weight-equal
                                                      [(group
                                                        "Commodities"
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              10})
                                                            (select-top
                                                             2)
                                                            [(asset
                                                              "COM"
                                                              "Direxion Auspice Broad Commodity Strategy ETF")
                                                             (asset
                                                              "FAAR"
                                                              "First Trust Alternative Absolute Return Strategy ETF")
                                                             (asset
                                                              "FTGC"
                                                              "First Trust Global Tactical Commodity Strategy Fund")
                                                             (asset
                                                              "DBC"
                                                              "Invesco DB Commodity Index Tracking Fund")
                                                             (asset
                                                              "PDBC"
                                                              "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                             (asset
                                                              "DBA"
                                                              "Invesco DB Agriculture Fund")
                                                             (asset
                                                              "GLTR"
                                                              "abrdn Physical Precious Metals Basket Shares ETF")
                                                             (asset
                                                              "DBB"
                                                              "Invesco DB Base Metals Fund")])
                                                           (filter
                                                            (max-drawdown
                                                             {:window
                                                              20})
                                                            (select-bottom
                                                             2)
                                                            [(asset
                                                              "COM"
                                                              "Direxion Auspice Broad Commodity Strategy ETF")
                                                             (asset
                                                              "FAAR"
                                                              "First Trust Alternative Absolute Return Strategy ETF")
                                                             (asset
                                                              "FTGC"
                                                              "First Trust Global Tactical Commodity Strategy Fund")
                                                             (asset
                                                              "DBC"
                                                              "Invesco DB Commodity Index Tracking Fund")
                                                             (asset
                                                              "PDBC"
                                                              "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                             (asset
                                                              "DBA"
                                                              "Invesco DB Agriculture Fund")
                                                             (asset
                                                              "GLTR"
                                                              "abrdn Physical Precious Metals Basket Shares ETF")
                                                             (asset
                                                              "DBB"
                                                              "Invesco DB Base Metals Fund")])])])
                                                       (group
                                                        "Bonds"
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              10})
                                                            (select-top
                                                             3)
                                                            [(asset
                                                              "AGG"
                                                              "iShares Core U.S. Aggregate Bond ETF")
                                                             (asset
                                                              "BND"
                                                              "Vanguard Total Bond Market ETF")
                                                             (asset
                                                              "BNDX"
                                                              "Vanguard Total International Bond ETF")
                                                             (asset
                                                              "BIL"
                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                             (asset
                                                              "IEF"
                                                              "iShares 7-10 Year Treasury Bond ETF")
                                                             (asset
                                                              "EMB"
                                                              "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                             (asset
                                                              "BWX"
                                                              "SPDR Bloomberg International Treasury Bond ETF")
                                                             (asset
                                                              "SHV"
                                                              "iShares Short Treasury Bond ETF")
                                                             (asset
                                                              "VGSH"
                                                              "Vanguard Short-Term Treasury ETF")
                                                             (asset
                                                              "GBIL"
                                                              "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                             (asset
                                                              "TYD"
                                                              "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                             (asset
                                                              "TMF"
                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                             (asset
                                                              "HYG"
                                                              "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                             (asset
                                                              "TBT"
                                                              "ProShares UltraShort 20+ Year Treasury")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                           (filter
                                                            (max-drawdown
                                                             {:window
                                                              20})
                                                            (select-bottom
                                                             3)
                                                            [(asset
                                                              "AGG"
                                                              "iShares Core U.S. Aggregate Bond ETF")
                                                             (asset
                                                              "BND"
                                                              "Vanguard Total Bond Market ETF")
                                                             (asset
                                                              "BNDX"
                                                              "Vanguard Total International Bond ETF")
                                                             (asset
                                                              "BIL"
                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                             (asset
                                                              "IEF"
                                                              "iShares 7-10 Year Treasury Bond ETF")
                                                             (asset
                                                              "EMB"
                                                              "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                             (asset
                                                              "BWX"
                                                              "SPDR Bloomberg International Treasury Bond ETF")
                                                             (asset
                                                              "SHV"
                                                              "iShares Short Treasury Bond ETF")
                                                             (asset
                                                              "VGSH"
                                                              "Vanguard Short-Term Treasury ETF")
                                                             (asset
                                                              "GBIL"
                                                              "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                             (asset
                                                              "TYD"
                                                              "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                             (asset
                                                              "TMF"
                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                             (asset
                                                              "HYG"
                                                              "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                             (asset
                                                              "TBT"
                                                              "ProShares UltraShort 20+ Year Treasury")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])
                                             (group
                                              "20d AGG vs 60d SH | 2007-06-11"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (rsi
                                                    "AGG"
                                                    {:window 20})
                                                   (rsi
                                                    "SH"
                                                    {:window 60}))
                                                  [(group
                                                    "Risk on"
                                                    [(weight-equal
                                                      [(group
                                                        "Risk-On - Stable/Normal rates"
                                                        [(weight-equal
                                                          [(group
                                                            "SPY"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "AMZN"
                                                                  "Amazon.com, Inc.")
                                                                 (asset
                                                                  "NVDA"
                                                                  "NVIDIA Corporation")
                                                                 (asset
                                                                  "TSLA"
                                                                  "Tesla, Inc.")
                                                                 (asset
                                                                  "GOOG"
                                                                  "Alphabet Inc. Class C")
                                                                 (asset
                                                                  "GOOGL"
                                                                  "Alphabet Inc. Class A")
                                                                 (asset
                                                                  "META"
                                                                  "Meta Platforms Inc. Class A")
                                                                 (asset
                                                                  "BRK/B"
                                                                  "Berkshire Hathaway Inc. Class B")
                                                                 (asset
                                                                  "JNJ"
                                                                  "Johnson & Johnson")
                                                                 (asset
                                                                  "JPM"
                                                                  "JPMorgan Chase & Co.")
                                                                 (asset
                                                                  "XOM"
                                                                  "Exxon Mobil Corporation")
                                                                 (asset
                                                                  "V"
                                                                  "Visa Inc. Class A")
                                                                 (asset
                                                                  "LLY"
                                                                  "Eli Lilly and Company")
                                                                 (asset
                                                                  "AVGO"
                                                                  "Broadcom Inc")])])])
                                                           (group
                                                            "QQQ"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "NFLX"
                                                                  "Netflix, Inc.")
                                                                 (asset
                                                                  "CSCO"
                                                                  "Cisco Systems, Inc.")
                                                                 (asset
                                                                  "COST"
                                                                  "Costco Wholesale Corporation")
                                                                 (asset
                                                                  "AVGO"
                                                                  "Broadcom Inc.")
                                                                 (asset
                                                                  "GOOG"
                                                                  "Alphabet Inc. Class C")
                                                                 (asset
                                                                  "GOOGL"
                                                                  "Alphabet Inc. Class A")
                                                                 (asset
                                                                  "META"
                                                                  "Meta Platforms Inc. Class A")
                                                                 (asset
                                                                  "TSLA"
                                                                  "Tesla, Inc.")
                                                                 (asset
                                                                  "AMZN"
                                                                  "Amazon.com, Inc.")
                                                                 (asset
                                                                  "NVDA"
                                                                  "NVIDIA Corporation")
                                                                 (asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "LIN"
                                                                  "Linde Plc.")
                                                                 (asset
                                                                  "PLTR"
                                                                  "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                                 (asset
                                                                  "TMUS"
                                                                  "T-Mobile US Inc")])])])
                                                           (group
                                                            "DIA"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "UNH"
                                                                  "UnitedHealth Group Incorporated")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "GS"
                                                                  "Goldman Sachs Group, Inc.")
                                                                 (asset
                                                                  "HD"
                                                                  "Home Depot, Inc.")
                                                                 (asset
                                                                  "MCD"
                                                                  "McDonald's Corporation")
                                                                 (asset
                                                                  "TRV"
                                                                  "Travelers Companies, Inc.")
                                                                 (asset
                                                                  "AXP"
                                                                  "American Express Company")
                                                                 (asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "CRM"
                                                                  "Salesforce, Inc.")
                                                                 (asset
                                                                  "AMGN"
                                                                  "Amgen Inc.")
                                                                 (asset
                                                                  "V"
                                                                  "Visa Inc. Class A")
                                                                 (asset
                                                                  "CAT"
                                                                  "Caterpillar Inc.")
                                                                 (asset
                                                                  "IBM"
                                                                  "International Business Machines Corp.")
                                                                 (asset
                                                                  "JPM"
                                                                  "JPMorgan Chase & Co.")])])])])])])])]
                                                  [(group
                                                    "Risk Off"
                                                    [(weight-equal
                                                      [(group
                                                        "Commodities"
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              10})
                                                            (select-top
                                                             2)
                                                            [(asset
                                                              "COM"
                                                              "Direxion Auspice Broad Commodity Strategy ETF")
                                                             (asset
                                                              "FAAR"
                                                              "First Trust Alternative Absolute Return Strategy ETF")
                                                             (asset
                                                              "FTGC"
                                                              "First Trust Global Tactical Commodity Strategy Fund")
                                                             (asset
                                                              "DBC"
                                                              "Invesco DB Commodity Index Tracking Fund")
                                                             (asset
                                                              "PDBC"
                                                              "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                             (asset
                                                              "DBA"
                                                              "Invesco DB Agriculture Fund")
                                                             (asset
                                                              "GLTR"
                                                              "abrdn Physical Precious Metals Basket Shares ETF")
                                                             (asset
                                                              "DBB"
                                                              "Invesco DB Base Metals Fund")])
                                                           (filter
                                                            (max-drawdown
                                                             {:window
                                                              20})
                                                            (select-bottom
                                                             2)
                                                            [(asset
                                                              "COM"
                                                              "Direxion Auspice Broad Commodity Strategy ETF")
                                                             (asset
                                                              "FAAR"
                                                              "First Trust Alternative Absolute Return Strategy ETF")
                                                             (asset
                                                              "FTGC"
                                                              "First Trust Global Tactical Commodity Strategy Fund")
                                                             (asset
                                                              "DBC"
                                                              "Invesco DB Commodity Index Tracking Fund")
                                                             (asset
                                                              "PDBC"
                                                              "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                             (asset
                                                              "DBA"
                                                              "Invesco DB Agriculture Fund")
                                                             (asset
                                                              "GLTR"
                                                              "abrdn Physical Precious Metals Basket Shares ETF")
                                                             (asset
                                                              "DBB"
                                                              "Invesco DB Base Metals Fund")])])])
                                                       (group
                                                        "Bonds"
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              10})
                                                            (select-top
                                                             3)
                                                            [(asset
                                                              "AGG"
                                                              "iShares Core U.S. Aggregate Bond ETF")
                                                             (asset
                                                              "BND"
                                                              "Vanguard Total Bond Market ETF")
                                                             (asset
                                                              "BNDX"
                                                              "Vanguard Total International Bond ETF")
                                                             (asset
                                                              "BIL"
                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                             (asset
                                                              "IEF"
                                                              "iShares 7-10 Year Treasury Bond ETF")
                                                             (asset
                                                              "EMB"
                                                              "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                             (asset
                                                              "BWX"
                                                              "SPDR Bloomberg International Treasury Bond ETF")
                                                             (asset
                                                              "SHV"
                                                              "iShares Short Treasury Bond ETF")
                                                             (asset
                                                              "VGSH"
                                                              "Vanguard Short-Term Treasury ETF")
                                                             (asset
                                                              "GBIL"
                                                              "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                             (asset
                                                              "TYD"
                                                              "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                             (asset
                                                              "TMF"
                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                             (asset
                                                              "HYG"
                                                              "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                             (asset
                                                              "TBT"
                                                              "ProShares UltraShort 20+ Year Treasury")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                           (filter
                                                            (max-drawdown
                                                             {:window
                                                              20})
                                                            (select-bottom
                                                             3)
                                                            [(asset
                                                              "AGG"
                                                              "iShares Core U.S. Aggregate Bond ETF")
                                                             (asset
                                                              "BND"
                                                              "Vanguard Total Bond Market ETF")
                                                             (asset
                                                              "BNDX"
                                                              "Vanguard Total International Bond ETF")
                                                             (asset
                                                              "BIL"
                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                             (asset
                                                              "IEF"
                                                              "iShares 7-10 Year Treasury Bond ETF")
                                                             (asset
                                                              "EMB"
                                                              "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                             (asset
                                                              "BWX"
                                                              "SPDR Bloomberg International Treasury Bond ETF")
                                                             (asset
                                                              "SHV"
                                                              "iShares Short Treasury Bond ETF")
                                                             (asset
                                                              "VGSH"
                                                              "Vanguard Short-Term Treasury ETF")
                                                             (asset
                                                              "GBIL"
                                                              "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                             (asset
                                                              "TYD"
                                                              "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                             (asset
                                                              "TMF"
                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                             (asset
                                                              "HYG"
                                                              "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                             (asset
                                                              "TBT"
                                                              "ProShares UltraShort 20+ Year Treasury")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])
                                             (group
                                              "20/60 -> 10/20 | 2007-05-30"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (rsi
                                                    "AGG"
                                                    {:window 20})
                                                   (rsi
                                                    "SH"
                                                    {:window 60}))
                                                  [(group
                                                    "Risk on"
                                                    [(weight-equal
                                                      [(group
                                                        "Risk-On - Stable/Normal rates"
                                                        [(weight-equal
                                                          [(group
                                                            "SPY"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "AMZN"
                                                                  "Amazon.com, Inc.")
                                                                 (asset
                                                                  "NVDA"
                                                                  "NVIDIA Corporation")
                                                                 (asset
                                                                  "TSLA"
                                                                  "Tesla, Inc.")
                                                                 (asset
                                                                  "GOOG"
                                                                  "Alphabet Inc. Class C")
                                                                 (asset
                                                                  "GOOGL"
                                                                  "Alphabet Inc. Class A")
                                                                 (asset
                                                                  "META"
                                                                  "Meta Platforms Inc. Class A")
                                                                 (asset
                                                                  "BRK/B"
                                                                  "Berkshire Hathaway Inc. Class B")
                                                                 (asset
                                                                  "JNJ"
                                                                  "Johnson & Johnson")
                                                                 (asset
                                                                  "JPM"
                                                                  "JPMorgan Chase & Co.")
                                                                 (asset
                                                                  "XOM"
                                                                  "Exxon Mobil Corporation")
                                                                 (asset
                                                                  "V"
                                                                  "Visa Inc. Class A")
                                                                 (asset
                                                                  "LLY"
                                                                  "Eli Lilly and Company")
                                                                 (asset
                                                                  "AVGO"
                                                                  "Broadcom Inc")])])])
                                                           (group
                                                            "QQQ"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "NFLX"
                                                                  "Netflix, Inc.")
                                                                 (asset
                                                                  "CSCO"
                                                                  "Cisco Systems, Inc.")
                                                                 (asset
                                                                  "COST"
                                                                  "Costco Wholesale Corporation")
                                                                 (asset
                                                                  "AVGO"
                                                                  "Broadcom Inc.")
                                                                 (asset
                                                                  "GOOG"
                                                                  "Alphabet Inc. Class C")
                                                                 (asset
                                                                  "GOOGL"
                                                                  "Alphabet Inc. Class A")
                                                                 (asset
                                                                  "META"
                                                                  "Meta Platforms Inc. Class A")
                                                                 (asset
                                                                  "TSLA"
                                                                  "Tesla, Inc.")
                                                                 (asset
                                                                  "AMZN"
                                                                  "Amazon.com, Inc.")
                                                                 (asset
                                                                  "NVDA"
                                                                  "NVIDIA Corporation")
                                                                 (asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "LIN"
                                                                  "Linde Plc.")
                                                                 (asset
                                                                  "PLTR"
                                                                  "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                                 (asset
                                                                  "TMUS"
                                                                  "T-Mobile US Inc")])])])
                                                           (group
                                                            "DIA"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "UNH"
                                                                  "UnitedHealth Group Incorporated")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "GS"
                                                                  "Goldman Sachs Group, Inc.")
                                                                 (asset
                                                                  "HD"
                                                                  "Home Depot, Inc.")
                                                                 (asset
                                                                  "MCD"
                                                                  "McDonald's Corporation")
                                                                 (asset
                                                                  "TRV"
                                                                  "Travelers Companies, Inc.")
                                                                 (asset
                                                                  "AXP"
                                                                  "American Express Company")
                                                                 (asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "CRM"
                                                                  "Salesforce, Inc.")
                                                                 (asset
                                                                  "AMGN"
                                                                  "Amgen Inc.")
                                                                 (asset
                                                                  "V"
                                                                  "Visa Inc. Class A")
                                                                 (asset
                                                                  "CAT"
                                                                  "Caterpillar Inc.")
                                                                 (asset
                                                                  "IBM"
                                                                  "International Business Machines Corp.")
                                                                 (asset
                                                                  "JPM"
                                                                  "JPMorgan Chase & Co.")])])])])])])])]
                                                  [(weight-equal
                                                    [(if
                                                      (>
                                                       (rsi
                                                        "IEF"
                                                        {:window 10})
                                                       (rsi
                                                        "PSQ"
                                                        {:window 20}))
                                                      [(group
                                                        "Risk on"
                                                        [(weight-equal
                                                          [(group
                                                            "Risk-On - Stable/Normal rates"
                                                            [(weight-equal
                                                              [(group
                                                                "SPY"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "AMZN"
                                                                      "Amazon.com, Inc.")
                                                                     (asset
                                                                      "NVDA"
                                                                      "NVIDIA Corporation")
                                                                     (asset
                                                                      "TSLA"
                                                                      "Tesla, Inc.")
                                                                     (asset
                                                                      "GOOG"
                                                                      "Alphabet Inc. Class C")
                                                                     (asset
                                                                      "GOOGL"
                                                                      "Alphabet Inc. Class A")
                                                                     (asset
                                                                      "META"
                                                                      "Meta Platforms Inc. Class A")
                                                                     (asset
                                                                      "BRK/B"
                                                                      "Berkshire Hathaway Inc. Class B")
                                                                     (asset
                                                                      "JNJ"
                                                                      "Johnson & Johnson")
                                                                     (asset
                                                                      "JPM"
                                                                      "JPMorgan Chase & Co.")
                                                                     (asset
                                                                      "XOM"
                                                                      "Exxon Mobil Corporation")
                                                                     (asset
                                                                      "V"
                                                                      "Visa Inc. Class A")
                                                                     (asset
                                                                      "LLY"
                                                                      "Eli Lilly and Company")
                                                                     (asset
                                                                      "AVGO"
                                                                      "Broadcom Inc")])])])
                                                               (group
                                                                "QQQ"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "NFLX"
                                                                      "Netflix, Inc.")
                                                                     (asset
                                                                      "CSCO"
                                                                      "Cisco Systems, Inc.")
                                                                     (asset
                                                                      "COST"
                                                                      "Costco Wholesale Corporation")
                                                                     (asset
                                                                      "AVGO"
                                                                      "Broadcom Inc.")
                                                                     (asset
                                                                      "GOOG"
                                                                      "Alphabet Inc. Class C")
                                                                     (asset
                                                                      "GOOGL"
                                                                      "Alphabet Inc. Class A")
                                                                     (asset
                                                                      "META"
                                                                      "Meta Platforms Inc. Class A")
                                                                     (asset
                                                                      "TSLA"
                                                                      "Tesla, Inc.")
                                                                     (asset
                                                                      "AMZN"
                                                                      "Amazon.com, Inc.")
                                                                     (asset
                                                                      "NVDA"
                                                                      "NVIDIA Corporation")
                                                                     (asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "LIN"
                                                                      "Linde Plc.")
                                                                     (asset
                                                                      "PLTR"
                                                                      "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                                     (asset
                                                                      "TMUS"
                                                                      "T-Mobile US Inc")])])])
                                                               (group
                                                                "DIA"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "UNH"
                                                                      "UnitedHealth Group Incorporated")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "GS"
                                                                      "Goldman Sachs Group, Inc.")
                                                                     (asset
                                                                      "HD"
                                                                      "Home Depot, Inc.")
                                                                     (asset
                                                                      "MCD"
                                                                      "McDonald's Corporation")
                                                                     (asset
                                                                      "TRV"
                                                                      "Travelers Companies, Inc.")
                                                                     (asset
                                                                      "AXP"
                                                                      "American Express Company")
                                                                     (asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "CRM"
                                                                      "Salesforce, Inc.")
                                                                     (asset
                                                                      "AMGN"
                                                                      "Amgen Inc.")
                                                                     (asset
                                                                      "V"
                                                                      "Visa Inc. Class A")
                                                                     (asset
                                                                      "CAT"
                                                                      "Caterpillar Inc.")
                                                                     (asset
                                                                      "IBM"
                                                                      "International Business Machines Corp.")
                                                                     (asset
                                                                      "JPM"
                                                                      "JPMorgan Chase & Co.")])])])])])])])]
                                                      [(group
                                                        "Risk Off"
                                                        [(weight-equal
                                                          [(group
                                                            "Commodities"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  10})
                                                                (select-top
                                                                 2)
                                                                [(asset
                                                                  "COM"
                                                                  "Direxion Auspice Broad Commodity Strategy ETF")
                                                                 (asset
                                                                  "FAAR"
                                                                  "First Trust Alternative Absolute Return Strategy ETF")
                                                                 (asset
                                                                  "FTGC"
                                                                  "First Trust Global Tactical Commodity Strategy Fund")
                                                                 (asset
                                                                  "DBC"
                                                                  "Invesco DB Commodity Index Tracking Fund")
                                                                 (asset
                                                                  "PDBC"
                                                                  "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                                 (asset
                                                                  "DBA"
                                                                  "Invesco DB Agriculture Fund")
                                                                 (asset
                                                                  "GLTR"
                                                                  "abrdn Physical Precious Metals Basket Shares ETF")
                                                                 (asset
                                                                  "DBB"
                                                                  "Invesco DB Base Metals Fund")])
                                                               (filter
                                                                (max-drawdown
                                                                 {:window
                                                                  20})
                                                                (select-bottom
                                                                 2)
                                                                [(asset
                                                                  "COM"
                                                                  "Direxion Auspice Broad Commodity Strategy ETF")
                                                                 (asset
                                                                  "FAAR"
                                                                  "First Trust Alternative Absolute Return Strategy ETF")
                                                                 (asset
                                                                  "FTGC"
                                                                  "First Trust Global Tactical Commodity Strategy Fund")
                                                                 (asset
                                                                  "DBC"
                                                                  "Invesco DB Commodity Index Tracking Fund")
                                                                 (asset
                                                                  "PDBC"
                                                                  "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                                 (asset
                                                                  "DBA"
                                                                  "Invesco DB Agriculture Fund")
                                                                 (asset
                                                                  "GLTR"
                                                                  "abrdn Physical Precious Metals Basket Shares ETF")
                                                                 (asset
                                                                  "DBB"
                                                                  "Invesco DB Base Metals Fund")])])])
                                                           (group
                                                            "Bonds"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  10})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "AGG"
                                                                  "iShares Core U.S. Aggregate Bond ETF")
                                                                 (asset
                                                                  "BND"
                                                                  "Vanguard Total Bond Market ETF")
                                                                 (asset
                                                                  "BNDX"
                                                                  "Vanguard Total International Bond ETF")
                                                                 (asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                 (asset
                                                                  "IEF"
                                                                  "iShares 7-10 Year Treasury Bond ETF")
                                                                 (asset
                                                                  "EMB"
                                                                  "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                                 (asset
                                                                  "BWX"
                                                                  "SPDR Bloomberg International Treasury Bond ETF")
                                                                 (asset
                                                                  "SHV"
                                                                  "iShares Short Treasury Bond ETF")
                                                                 (asset
                                                                  "VGSH"
                                                                  "Vanguard Short-Term Treasury ETF")
                                                                 (asset
                                                                  "GBIL"
                                                                  "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                                 (asset
                                                                  "TYD"
                                                                  "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                 (asset
                                                                  "HYG"
                                                                  "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                                 (asset
                                                                  "TBT"
                                                                  "ProShares UltraShort 20+ Year Treasury")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                               (filter
                                                                (max-drawdown
                                                                 {:window
                                                                  20})
                                                                (select-bottom
                                                                 3)
                                                                [(asset
                                                                  "AGG"
                                                                  "iShares Core U.S. Aggregate Bond ETF")
                                                                 (asset
                                                                  "BND"
                                                                  "Vanguard Total Bond Market ETF")
                                                                 (asset
                                                                  "BNDX"
                                                                  "Vanguard Total International Bond ETF")
                                                                 (asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                 (asset
                                                                  "IEF"
                                                                  "iShares 7-10 Year Treasury Bond ETF")
                                                                 (asset
                                                                  "EMB"
                                                                  "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                                 (asset
                                                                  "BWX"
                                                                  "SPDR Bloomberg International Treasury Bond ETF")
                                                                 (asset
                                                                  "SHV"
                                                                  "iShares Short Treasury Bond ETF")
                                                                 (asset
                                                                  "VGSH"
                                                                  "Vanguard Short-Term Treasury ETF")
                                                                 (asset
                                                                  "GBIL"
                                                                  "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                                 (asset
                                                                  "TYD"
                                                                  "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                 (asset
                                                                  "HYG"
                                                                  "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                                 (asset
                                                                  "TBT"
                                                                  "ProShares UltraShort 20+ Year Treasury")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])
                                             (group
                                              "60d BND vs 60d BIL | 2007-08-23"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (cumulative-return
                                                    "BND"
                                                    {:window 60})
                                                   (cumulative-return
                                                    "BIL"
                                                    {:window 60}))
                                                  [(group
                                                    "Risk on"
                                                    [(weight-equal
                                                      [(group
                                                        "Risk-On - Stable/Normal rates"
                                                        [(weight-equal
                                                          [(group
                                                            "SPY"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "AMZN"
                                                                  "Amazon.com, Inc.")
                                                                 (asset
                                                                  "NVDA"
                                                                  "NVIDIA Corporation")
                                                                 (asset
                                                                  "TSLA"
                                                                  "Tesla, Inc.")
                                                                 (asset
                                                                  "GOOG"
                                                                  "Alphabet Inc. Class C")
                                                                 (asset
                                                                  "GOOGL"
                                                                  "Alphabet Inc. Class A")
                                                                 (asset
                                                                  "META"
                                                                  "Meta Platforms Inc. Class A")
                                                                 (asset
                                                                  "BRK/B"
                                                                  "Berkshire Hathaway Inc. Class B")
                                                                 (asset
                                                                  "JNJ"
                                                                  "Johnson & Johnson")
                                                                 (asset
                                                                  "JPM"
                                                                  "JPMorgan Chase & Co.")
                                                                 (asset
                                                                  "XOM"
                                                                  "Exxon Mobil Corporation")
                                                                 (asset
                                                                  "V"
                                                                  "Visa Inc. Class A")
                                                                 (asset
                                                                  "LLY"
                                                                  "Eli Lilly and Company")
                                                                 (asset
                                                                  "AVGO"
                                                                  "Broadcom Inc")])])])
                                                           (group
                                                            "QQQ"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "NFLX"
                                                                  "Netflix, Inc.")
                                                                 (asset
                                                                  "CSCO"
                                                                  "Cisco Systems, Inc.")
                                                                 (asset
                                                                  "COST"
                                                                  "Costco Wholesale Corporation")
                                                                 (asset
                                                                  "AVGO"
                                                                  "Broadcom Inc.")
                                                                 (asset
                                                                  "GOOG"
                                                                  "Alphabet Inc. Class C")
                                                                 (asset
                                                                  "GOOGL"
                                                                  "Alphabet Inc. Class A")
                                                                 (asset
                                                                  "META"
                                                                  "Meta Platforms Inc. Class A")
                                                                 (asset
                                                                  "TSLA"
                                                                  "Tesla, Inc.")
                                                                 (asset
                                                                  "AMZN"
                                                                  "Amazon.com, Inc.")
                                                                 (asset
                                                                  "NVDA"
                                                                  "NVIDIA Corporation")
                                                                 (asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "LIN"
                                                                  "Linde Plc.")
                                                                 (asset
                                                                  "PLTR"
                                                                  "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                                 (asset
                                                                  "TMUS"
                                                                  "T-Mobile US Inc")])])])
                                                           (group
                                                            "DIA"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "UNH"
                                                                  "UnitedHealth Group Incorporated")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "GS"
                                                                  "Goldman Sachs Group, Inc.")
                                                                 (asset
                                                                  "HD"
                                                                  "Home Depot, Inc.")
                                                                 (asset
                                                                  "MCD"
                                                                  "McDonald's Corporation")
                                                                 (asset
                                                                  "TRV"
                                                                  "Travelers Companies, Inc.")
                                                                 (asset
                                                                  "AXP"
                                                                  "American Express Company")
                                                                 (asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "CRM"
                                                                  "Salesforce, Inc.")
                                                                 (asset
                                                                  "AMGN"
                                                                  "Amgen Inc.")
                                                                 (asset
                                                                  "V"
                                                                  "Visa Inc. Class A")
                                                                 (asset
                                                                  "CAT"
                                                                  "Caterpillar Inc.")
                                                                 (asset
                                                                  "IBM"
                                                                  "International Business Machines Corp.")
                                                                 (asset
                                                                  "JPM"
                                                                  "JPMorgan Chase & Co.")])])])])])])])]
                                                  [(group
                                                    "Risk Off"
                                                    [(weight-equal
                                                      [(group
                                                        "Commodities"
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              10})
                                                            (select-top
                                                             2)
                                                            [(asset
                                                              "COM"
                                                              "Direxion Auspice Broad Commodity Strategy ETF")
                                                             (asset
                                                              "FAAR"
                                                              "First Trust Alternative Absolute Return Strategy ETF")
                                                             (asset
                                                              "FTGC"
                                                              "First Trust Global Tactical Commodity Strategy Fund")
                                                             (asset
                                                              "DBC"
                                                              "Invesco DB Commodity Index Tracking Fund")
                                                             (asset
                                                              "PDBC"
                                                              "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                             (asset
                                                              "DBA"
                                                              "Invesco DB Agriculture Fund")
                                                             (asset
                                                              "GLTR"
                                                              "abrdn Physical Precious Metals Basket Shares ETF")
                                                             (asset
                                                              "DBB"
                                                              "Invesco DB Base Metals Fund")])
                                                           (filter
                                                            (max-drawdown
                                                             {:window
                                                              20})
                                                            (select-bottom
                                                             2)
                                                            [(asset
                                                              "COM"
                                                              "Direxion Auspice Broad Commodity Strategy ETF")
                                                             (asset
                                                              "FAAR"
                                                              "First Trust Alternative Absolute Return Strategy ETF")
                                                             (asset
                                                              "FTGC"
                                                              "First Trust Global Tactical Commodity Strategy Fund")
                                                             (asset
                                                              "DBC"
                                                              "Invesco DB Commodity Index Tracking Fund")
                                                             (asset
                                                              "PDBC"
                                                              "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                             (asset
                                                              "DBA"
                                                              "Invesco DB Agriculture Fund")
                                                             (asset
                                                              "GLTR"
                                                              "abrdn Physical Precious Metals Basket Shares ETF")
                                                             (asset
                                                              "DBB"
                                                              "Invesco DB Base Metals Fund")])])])
                                                       (group
                                                        "Bonds"
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              10})
                                                            (select-top
                                                             3)
                                                            [(asset
                                                              "AGG"
                                                              "iShares Core U.S. Aggregate Bond ETF")
                                                             (asset
                                                              "BND"
                                                              "Vanguard Total Bond Market ETF")
                                                             (asset
                                                              "BNDX"
                                                              "Vanguard Total International Bond ETF")
                                                             (asset
                                                              "BIL"
                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                             (asset
                                                              "IEF"
                                                              "iShares 7-10 Year Treasury Bond ETF")
                                                             (asset
                                                              "EMB"
                                                              "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                             (asset
                                                              "BWX"
                                                              "SPDR Bloomberg International Treasury Bond ETF")
                                                             (asset
                                                              "SHV"
                                                              "iShares Short Treasury Bond ETF")
                                                             (asset
                                                              "VGSH"
                                                              "Vanguard Short-Term Treasury ETF")
                                                             (asset
                                                              "GBIL"
                                                              "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                             (asset
                                                              "TYD"
                                                              "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                             (asset
                                                              "TMF"
                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                             (asset
                                                              "HYG"
                                                              "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                             (asset
                                                              "TBT"
                                                              "ProShares UltraShort 20+ Year Treasury")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                           (filter
                                                            (max-drawdown
                                                             {:window
                                                              20})
                                                            (select-bottom
                                                             3)
                                                            [(asset
                                                              "AGG"
                                                              "iShares Core U.S. Aggregate Bond ETF")
                                                             (asset
                                                              "BND"
                                                              "Vanguard Total Bond Market ETF")
                                                             (asset
                                                              "BNDX"
                                                              "Vanguard Total International Bond ETF")
                                                             (asset
                                                              "BIL"
                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                             (asset
                                                              "IEF"
                                                              "iShares 7-10 Year Treasury Bond ETF")
                                                             (asset
                                                              "EMB"
                                                              "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                             (asset
                                                              "BWX"
                                                              "SPDR Bloomberg International Treasury Bond ETF")
                                                             (asset
                                                              "SHV"
                                                              "iShares Short Treasury Bond ETF")
                                                             (asset
                                                              "VGSH"
                                                              "Vanguard Short-Term Treasury ETF")
                                                             (asset
                                                              "GBIL"
                                                              "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                             (asset
                                                              "TYD"
                                                              "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                             (asset
                                                              "TMF"
                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                             (asset
                                                              "HYG"
                                                              "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                             (asset
                                                              "TBT"
                                                              "ProShares UltraShort 20+ Year Treasury")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])
                                             (group
                                              "200d FDN vs 200d XLU | 2007-05-30"
                                              [(weight-equal
                                                [(if
                                                  (>
                                                   (rsi
                                                    "FDN"
                                                    {:window 200})
                                                   (rsi
                                                    "XLU"
                                                    {:window 200}))
                                                  [(group
                                                    "Risk on"
                                                    [(weight-equal
                                                      [(group
                                                        "Risk-On - Stable/Normal rates"
                                                        [(weight-equal
                                                          [(group
                                                            "SPY"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "AMZN"
                                                                  "Amazon.com, Inc.")
                                                                 (asset
                                                                  "NVDA"
                                                                  "NVIDIA Corporation")
                                                                 (asset
                                                                  "TSLA"
                                                                  "Tesla, Inc.")
                                                                 (asset
                                                                  "GOOG"
                                                                  "Alphabet Inc. Class C")
                                                                 (asset
                                                                  "GOOGL"
                                                                  "Alphabet Inc. Class A")
                                                                 (asset
                                                                  "META"
                                                                  "Meta Platforms Inc. Class A")
                                                                 (asset
                                                                  "BRK/B"
                                                                  "Berkshire Hathaway Inc. Class B")
                                                                 (asset
                                                                  "JNJ"
                                                                  "Johnson & Johnson")
                                                                 (asset
                                                                  "JPM"
                                                                  "JPMorgan Chase & Co.")
                                                                 (asset
                                                                  "XOM"
                                                                  "Exxon Mobil Corporation")
                                                                 (asset
                                                                  "V"
                                                                  "Visa Inc. Class A")
                                                                 (asset
                                                                  "LLY"
                                                                  "Eli Lilly and Company")
                                                                 (asset
                                                                  "AVGO"
                                                                  "Broadcom Inc")])])])
                                                           (group
                                                            "QQQ"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "NFLX"
                                                                  "Netflix, Inc.")
                                                                 (asset
                                                                  "CSCO"
                                                                  "Cisco Systems, Inc.")
                                                                 (asset
                                                                  "COST"
                                                                  "Costco Wholesale Corporation")
                                                                 (asset
                                                                  "AVGO"
                                                                  "Broadcom Inc.")
                                                                 (asset
                                                                  "GOOG"
                                                                  "Alphabet Inc. Class C")
                                                                 (asset
                                                                  "GOOGL"
                                                                  "Alphabet Inc. Class A")
                                                                 (asset
                                                                  "META"
                                                                  "Meta Platforms Inc. Class A")
                                                                 (asset
                                                                  "TSLA"
                                                                  "Tesla, Inc.")
                                                                 (asset
                                                                  "AMZN"
                                                                  "Amazon.com, Inc.")
                                                                 (asset
                                                                  "NVDA"
                                                                  "NVIDIA Corporation")
                                                                 (asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "LIN"
                                                                  "Linde Plc.")
                                                                 (asset
                                                                  "PLTR"
                                                                  "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                                 (asset
                                                                  "TMUS"
                                                                  "T-Mobile US Inc")])])])
                                                           (group
                                                            "DIA"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  20})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "UNH"
                                                                  "UnitedHealth Group Incorporated")
                                                                 (asset
                                                                  "MSFT"
                                                                  "Microsoft Corporation")
                                                                 (asset
                                                                  "GS"
                                                                  "Goldman Sachs Group, Inc.")
                                                                 (asset
                                                                  "HD"
                                                                  "Home Depot, Inc.")
                                                                 (asset
                                                                  "MCD"
                                                                  "McDonald's Corporation")
                                                                 (asset
                                                                  "TRV"
                                                                  "Travelers Companies, Inc.")
                                                                 (asset
                                                                  "AXP"
                                                                  "American Express Company")
                                                                 (asset
                                                                  "AAPL"
                                                                  "Apple Inc.")
                                                                 (asset
                                                                  "CRM"
                                                                  "Salesforce, Inc.")
                                                                 (asset
                                                                  "AMGN"
                                                                  "Amgen Inc.")
                                                                 (asset
                                                                  "V"
                                                                  "Visa Inc. Class A")
                                                                 (asset
                                                                  "CAT"
                                                                  "Caterpillar Inc.")
                                                                 (asset
                                                                  "IBM"
                                                                  "International Business Machines Corp.")
                                                                 (asset
                                                                  "JPM"
                                                                  "JPMorgan Chase & Co.")])])])])])])])]
                                                  [(group
                                                    "Risk Off"
                                                    [(weight-equal
                                                      [(group
                                                        "Commodities"
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              10})
                                                            (select-top
                                                             2)
                                                            [(asset
                                                              "COM"
                                                              "Direxion Auspice Broad Commodity Strategy ETF")
                                                             (asset
                                                              "FAAR"
                                                              "First Trust Alternative Absolute Return Strategy ETF")
                                                             (asset
                                                              "FTGC"
                                                              "First Trust Global Tactical Commodity Strategy Fund")
                                                             (asset
                                                              "DBC"
                                                              "Invesco DB Commodity Index Tracking Fund")
                                                             (asset
                                                              "PDBC"
                                                              "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                             (asset
                                                              "DBA"
                                                              "Invesco DB Agriculture Fund")
                                                             (asset
                                                              "GLTR"
                                                              "abrdn Physical Precious Metals Basket Shares ETF")
                                                             (asset
                                                              "DBB"
                                                              "Invesco DB Base Metals Fund")])
                                                           (filter
                                                            (max-drawdown
                                                             {:window
                                                              20})
                                                            (select-bottom
                                                             2)
                                                            [(asset
                                                              "COM"
                                                              "Direxion Auspice Broad Commodity Strategy ETF")
                                                             (asset
                                                              "FAAR"
                                                              "First Trust Alternative Absolute Return Strategy ETF")
                                                             (asset
                                                              "FTGC"
                                                              "First Trust Global Tactical Commodity Strategy Fund")
                                                             (asset
                                                              "DBC"
                                                              "Invesco DB Commodity Index Tracking Fund")
                                                             (asset
                                                              "PDBC"
                                                              "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                             (asset
                                                              "DBA"
                                                              "Invesco DB Agriculture Fund")
                                                             (asset
                                                              "GLTR"
                                                              "abrdn Physical Precious Metals Basket Shares ETF")
                                                             (asset
                                                              "DBB"
                                                              "Invesco DB Base Metals Fund")])])])
                                                       (group
                                                        "Bonds"
                                                        [(weight-equal
                                                          [(filter
                                                            (moving-average-return
                                                             {:window
                                                              10})
                                                            (select-top
                                                             3)
                                                            [(asset
                                                              "AGG"
                                                              "iShares Core U.S. Aggregate Bond ETF")
                                                             (asset
                                                              "BND"
                                                              "Vanguard Total Bond Market ETF")
                                                             (asset
                                                              "BNDX"
                                                              "Vanguard Total International Bond ETF")
                                                             (asset
                                                              "BIL"
                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                             (asset
                                                              "IEF"
                                                              "iShares 7-10 Year Treasury Bond ETF")
                                                             (asset
                                                              "EMB"
                                                              "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                             (asset
                                                              "BWX"
                                                              "SPDR Bloomberg International Treasury Bond ETF")
                                                             (asset
                                                              "SHV"
                                                              "iShares Short Treasury Bond ETF")
                                                             (asset
                                                              "VGSH"
                                                              "Vanguard Short-Term Treasury ETF")
                                                             (asset
                                                              "GBIL"
                                                              "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                             (asset
                                                              "TYD"
                                                              "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                             (asset
                                                              "TMF"
                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                             (asset
                                                              "HYG"
                                                              "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                             (asset
                                                              "TBT"
                                                              "ProShares UltraShort 20+ Year Treasury")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                           (filter
                                                            (max-drawdown
                                                             {:window
                                                              20})
                                                            (select-bottom
                                                             3)
                                                            [(asset
                                                              "AGG"
                                                              "iShares Core U.S. Aggregate Bond ETF")
                                                             (asset
                                                              "BND"
                                                              "Vanguard Total Bond Market ETF")
                                                             (asset
                                                              "BNDX"
                                                              "Vanguard Total International Bond ETF")
                                                             (asset
                                                              "BIL"
                                                              "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                             (asset
                                                              "IEF"
                                                              "iShares 7-10 Year Treasury Bond ETF")
                                                             (asset
                                                              "EMB"
                                                              "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                             (asset
                                                              "BWX"
                                                              "SPDR Bloomberg International Treasury Bond ETF")
                                                             (asset
                                                              "SHV"
                                                              "iShares Short Treasury Bond ETF")
                                                             (asset
                                                              "VGSH"
                                                              "Vanguard Short-Term Treasury ETF")
                                                             (asset
                                                              "GBIL"
                                                              "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                             (asset
                                                              "TYD"
                                                              "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                             (asset
                                                              "TMF"
                                                              "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                             (asset
                                                              "HYG"
                                                              "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                             (asset
                                                              "TBT"
                                                              "ProShares UltraShort 20+ Year Treasury")
                                                             (asset
                                                              "TMV"
                                                              "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])]
                                        [(weight-equal
                                          [(if
                                            (>
                                             (current-price "SPY")
                                             (moving-average-price
                                              "SPY"
                                              {:window 20}))
                                            [(group
                                              "Compares"
                                              [(weight-equal
                                                [(group
                                                  "20d TLT vs 20d PSQ | 2007-06-11"
                                                  [(weight-equal
                                                    [(if
                                                      (>
                                                       (rsi
                                                        "TLT"
                                                        {:window 20})
                                                       (rsi
                                                        "PSQ"
                                                        {:window 20}))
                                                      [(group
                                                        "Risk on"
                                                        [(weight-equal
                                                          [(group
                                                            "Risk-On - Stable/Normal rates"
                                                            [(weight-equal
                                                              [(group
                                                                "SPY"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "AMZN"
                                                                      "Amazon.com, Inc.")
                                                                     (asset
                                                                      "NVDA"
                                                                      "NVIDIA Corporation")
                                                                     (asset
                                                                      "TSLA"
                                                                      "Tesla, Inc.")
                                                                     (asset
                                                                      "GOOG"
                                                                      "Alphabet Inc. Class C")
                                                                     (asset
                                                                      "GOOGL"
                                                                      "Alphabet Inc. Class A")
                                                                     (asset
                                                                      "META"
                                                                      "Meta Platforms Inc. Class A")
                                                                     (asset
                                                                      "BRK/B"
                                                                      "Berkshire Hathaway Inc. Class B")
                                                                     (asset
                                                                      "JNJ"
                                                                      "Johnson & Johnson")
                                                                     (asset
                                                                      "JPM"
                                                                      "JPMorgan Chase & Co.")
                                                                     (asset
                                                                      "XOM"
                                                                      "Exxon Mobil Corporation")
                                                                     (asset
                                                                      "V"
                                                                      "Visa Inc. Class A")
                                                                     (asset
                                                                      "LLY"
                                                                      "Eli Lilly and Company")
                                                                     (asset
                                                                      "AVGO"
                                                                      "Broadcom Inc")])])])
                                                               (group
                                                                "QQQ"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "NFLX"
                                                                      "Netflix, Inc.")
                                                                     (asset
                                                                      "CSCO"
                                                                      "Cisco Systems, Inc.")
                                                                     (asset
                                                                      "COST"
                                                                      "Costco Wholesale Corporation")
                                                                     (asset
                                                                      "AVGO"
                                                                      "Broadcom Inc.")
                                                                     (asset
                                                                      "GOOG"
                                                                      "Alphabet Inc. Class C")
                                                                     (asset
                                                                      "GOOGL"
                                                                      "Alphabet Inc. Class A")
                                                                     (asset
                                                                      "META"
                                                                      "Meta Platforms Inc. Class A")
                                                                     (asset
                                                                      "TSLA"
                                                                      "Tesla, Inc.")
                                                                     (asset
                                                                      "AMZN"
                                                                      "Amazon.com, Inc.")
                                                                     (asset
                                                                      "NVDA"
                                                                      "NVIDIA Corporation")
                                                                     (asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "LIN"
                                                                      "Linde Plc.")
                                                                     (asset
                                                                      "PLTR"
                                                                      "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                                     (asset
                                                                      "TMUS"
                                                                      "T-Mobile US Inc")])])])
                                                               (group
                                                                "DIA"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "UNH"
                                                                      "UnitedHealth Group Incorporated")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "GS"
                                                                      "Goldman Sachs Group, Inc.")
                                                                     (asset
                                                                      "HD"
                                                                      "Home Depot, Inc.")
                                                                     (asset
                                                                      "MCD"
                                                                      "McDonald's Corporation")
                                                                     (asset
                                                                      "TRV"
                                                                      "Travelers Companies, Inc.")
                                                                     (asset
                                                                      "AXP"
                                                                      "American Express Company")
                                                                     (asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "CRM"
                                                                      "Salesforce, Inc.")
                                                                     (asset
                                                                      "AMGN"
                                                                      "Amgen Inc.")
                                                                     (asset
                                                                      "V"
                                                                      "Visa Inc. Class A")
                                                                     (asset
                                                                      "CAT"
                                                                      "Caterpillar Inc.")
                                                                     (asset
                                                                      "IBM"
                                                                      "International Business Machines Corp.")
                                                                     (asset
                                                                      "JPM"
                                                                      "JPMorgan Chase & Co.")])])])])])])])]
                                                      [(group
                                                        "Risk Off"
                                                        [(weight-equal
                                                          [(group
                                                            "Commodities"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  10})
                                                                (select-top
                                                                 2)
                                                                [(asset
                                                                  "COM"
                                                                  "Direxion Auspice Broad Commodity Strategy ETF")
                                                                 (asset
                                                                  "FAAR"
                                                                  "First Trust Alternative Absolute Return Strategy ETF")
                                                                 (asset
                                                                  "FTGC"
                                                                  "First Trust Global Tactical Commodity Strategy Fund")
                                                                 (asset
                                                                  "DBC"
                                                                  "Invesco DB Commodity Index Tracking Fund")
                                                                 (asset
                                                                  "PDBC"
                                                                  "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                                 (asset
                                                                  "DBA"
                                                                  "Invesco DB Agriculture Fund")
                                                                 (asset
                                                                  "GLTR"
                                                                  "abrdn Physical Precious Metals Basket Shares ETF")
                                                                 (asset
                                                                  "DBB"
                                                                  "Invesco DB Base Metals Fund")])
                                                               (filter
                                                                (max-drawdown
                                                                 {:window
                                                                  20})
                                                                (select-bottom
                                                                 2)
                                                                [(asset
                                                                  "COM"
                                                                  "Direxion Auspice Broad Commodity Strategy ETF")
                                                                 (asset
                                                                  "FAAR"
                                                                  "First Trust Alternative Absolute Return Strategy ETF")
                                                                 (asset
                                                                  "FTGC"
                                                                  "First Trust Global Tactical Commodity Strategy Fund")
                                                                 (asset
                                                                  "DBC"
                                                                  "Invesco DB Commodity Index Tracking Fund")
                                                                 (asset
                                                                  "PDBC"
                                                                  "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                                 (asset
                                                                  "DBA"
                                                                  "Invesco DB Agriculture Fund")
                                                                 (asset
                                                                  "GLTR"
                                                                  "abrdn Physical Precious Metals Basket Shares ETF")
                                                                 (asset
                                                                  "DBB"
                                                                  "Invesco DB Base Metals Fund")])])])
                                                           (group
                                                            "Bonds"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  10})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "AGG"
                                                                  "iShares Core U.S. Aggregate Bond ETF")
                                                                 (asset
                                                                  "BND"
                                                                  "Vanguard Total Bond Market ETF")
                                                                 (asset
                                                                  "BNDX"
                                                                  "Vanguard Total International Bond ETF")
                                                                 (asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                 (asset
                                                                  "IEF"
                                                                  "iShares 7-10 Year Treasury Bond ETF")
                                                                 (asset
                                                                  "EMB"
                                                                  "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                                 (asset
                                                                  "BWX"
                                                                  "SPDR Bloomberg International Treasury Bond ETF")
                                                                 (asset
                                                                  "SHV"
                                                                  "iShares Short Treasury Bond ETF")
                                                                 (asset
                                                                  "VGSH"
                                                                  "Vanguard Short-Term Treasury ETF")
                                                                 (asset
                                                                  "GBIL"
                                                                  "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                                 (asset
                                                                  "TYD"
                                                                  "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                 (asset
                                                                  "HYG"
                                                                  "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                                 (asset
                                                                  "TBT"
                                                                  "ProShares UltraShort 20+ Year Treasury")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                               (filter
                                                                (max-drawdown
                                                                 {:window
                                                                  20})
                                                                (select-bottom
                                                                 3)
                                                                [(asset
                                                                  "AGG"
                                                                  "iShares Core U.S. Aggregate Bond ETF")
                                                                 (asset
                                                                  "BND"
                                                                  "Vanguard Total Bond Market ETF")
                                                                 (asset
                                                                  "BNDX"
                                                                  "Vanguard Total International Bond ETF")
                                                                 (asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                 (asset
                                                                  "IEF"
                                                                  "iShares 7-10 Year Treasury Bond ETF")
                                                                 (asset
                                                                  "EMB"
                                                                  "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                                 (asset
                                                                  "BWX"
                                                                  "SPDR Bloomberg International Treasury Bond ETF")
                                                                 (asset
                                                                  "SHV"
                                                                  "iShares Short Treasury Bond ETF")
                                                                 (asset
                                                                  "VGSH"
                                                                  "Vanguard Short-Term Treasury ETF")
                                                                 (asset
                                                                  "GBIL"
                                                                  "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                                 (asset
                                                                  "TYD"
                                                                  "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                 (asset
                                                                  "HYG"
                                                                  "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                                 (asset
                                                                  "TBT"
                                                                  "ProShares UltraShort 20+ Year Treasury")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])
                                                 (group
                                                  "20d AGG vs 60d SH | 2007-06-11"
                                                  [(weight-equal
                                                    [(if
                                                      (>
                                                       (rsi
                                                        "AGG"
                                                        {:window 20})
                                                       (rsi
                                                        "SH"
                                                        {:window 60}))
                                                      [(group
                                                        "Risk on"
                                                        [(weight-equal
                                                          [(group
                                                            "Risk-On - Stable/Normal rates"
                                                            [(weight-equal
                                                              [(group
                                                                "SPY"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "AMZN"
                                                                      "Amazon.com, Inc.")
                                                                     (asset
                                                                      "NVDA"
                                                                      "NVIDIA Corporation")
                                                                     (asset
                                                                      "TSLA"
                                                                      "Tesla, Inc.")
                                                                     (asset
                                                                      "GOOG"
                                                                      "Alphabet Inc. Class C")
                                                                     (asset
                                                                      "GOOGL"
                                                                      "Alphabet Inc. Class A")
                                                                     (asset
                                                                      "META"
                                                                      "Meta Platforms Inc. Class A")
                                                                     (asset
                                                                      "BRK/B"
                                                                      "Berkshire Hathaway Inc. Class B")
                                                                     (asset
                                                                      "JNJ"
                                                                      "Johnson & Johnson")
                                                                     (asset
                                                                      "JPM"
                                                                      "JPMorgan Chase & Co.")
                                                                     (asset
                                                                      "XOM"
                                                                      "Exxon Mobil Corporation")
                                                                     (asset
                                                                      "V"
                                                                      "Visa Inc. Class A")
                                                                     (asset
                                                                      "LLY"
                                                                      "Eli Lilly and Company")
                                                                     (asset
                                                                      "AVGO"
                                                                      "Broadcom Inc")])])])
                                                               (group
                                                                "QQQ"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "NFLX"
                                                                      "Netflix, Inc.")
                                                                     (asset
                                                                      "CSCO"
                                                                      "Cisco Systems, Inc.")
                                                                     (asset
                                                                      "COST"
                                                                      "Costco Wholesale Corporation")
                                                                     (asset
                                                                      "AVGO"
                                                                      "Broadcom Inc.")
                                                                     (asset
                                                                      "GOOG"
                                                                      "Alphabet Inc. Class C")
                                                                     (asset
                                                                      "GOOGL"
                                                                      "Alphabet Inc. Class A")
                                                                     (asset
                                                                      "META"
                                                                      "Meta Platforms Inc. Class A")
                                                                     (asset
                                                                      "TSLA"
                                                                      "Tesla, Inc.")
                                                                     (asset
                                                                      "AMZN"
                                                                      "Amazon.com, Inc.")
                                                                     (asset
                                                                      "NVDA"
                                                                      "NVIDIA Corporation")
                                                                     (asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "LIN"
                                                                      "Linde Plc.")
                                                                     (asset
                                                                      "PLTR"
                                                                      "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                                     (asset
                                                                      "TMUS"
                                                                      "T-Mobile US Inc")])])])
                                                               (group
                                                                "DIA"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "UNH"
                                                                      "UnitedHealth Group Incorporated")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "GS"
                                                                      "Goldman Sachs Group, Inc.")
                                                                     (asset
                                                                      "HD"
                                                                      "Home Depot, Inc.")
                                                                     (asset
                                                                      "MCD"
                                                                      "McDonald's Corporation")
                                                                     (asset
                                                                      "TRV"
                                                                      "Travelers Companies, Inc.")
                                                                     (asset
                                                                      "AXP"
                                                                      "American Express Company")
                                                                     (asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "CRM"
                                                                      "Salesforce, Inc.")
                                                                     (asset
                                                                      "AMGN"
                                                                      "Amgen Inc.")
                                                                     (asset
                                                                      "V"
                                                                      "Visa Inc. Class A")
                                                                     (asset
                                                                      "CAT"
                                                                      "Caterpillar Inc.")
                                                                     (asset
                                                                      "IBM"
                                                                      "International Business Machines Corp.")
                                                                     (asset
                                                                      "JPM"
                                                                      "JPMorgan Chase & Co.")])])])])])])])]
                                                      [(group
                                                        "Risk Off"
                                                        [(weight-equal
                                                          [(group
                                                            "Commodities"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  10})
                                                                (select-top
                                                                 2)
                                                                [(asset
                                                                  "COM"
                                                                  "Direxion Auspice Broad Commodity Strategy ETF")
                                                                 (asset
                                                                  "FAAR"
                                                                  "First Trust Alternative Absolute Return Strategy ETF")
                                                                 (asset
                                                                  "FTGC"
                                                                  "First Trust Global Tactical Commodity Strategy Fund")
                                                                 (asset
                                                                  "DBC"
                                                                  "Invesco DB Commodity Index Tracking Fund")
                                                                 (asset
                                                                  "PDBC"
                                                                  "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                                 (asset
                                                                  "DBA"
                                                                  "Invesco DB Agriculture Fund")
                                                                 (asset
                                                                  "GLTR"
                                                                  "abrdn Physical Precious Metals Basket Shares ETF")
                                                                 (asset
                                                                  "DBB"
                                                                  "Invesco DB Base Metals Fund")])
                                                               (filter
                                                                (max-drawdown
                                                                 {:window
                                                                  20})
                                                                (select-bottom
                                                                 2)
                                                                [(asset
                                                                  "COM"
                                                                  "Direxion Auspice Broad Commodity Strategy ETF")
                                                                 (asset
                                                                  "FAAR"
                                                                  "First Trust Alternative Absolute Return Strategy ETF")
                                                                 (asset
                                                                  "FTGC"
                                                                  "First Trust Global Tactical Commodity Strategy Fund")
                                                                 (asset
                                                                  "DBC"
                                                                  "Invesco DB Commodity Index Tracking Fund")
                                                                 (asset
                                                                  "PDBC"
                                                                  "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                                 (asset
                                                                  "DBA"
                                                                  "Invesco DB Agriculture Fund")
                                                                 (asset
                                                                  "GLTR"
                                                                  "abrdn Physical Precious Metals Basket Shares ETF")
                                                                 (asset
                                                                  "DBB"
                                                                  "Invesco DB Base Metals Fund")])])])
                                                           (group
                                                            "Bonds"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  10})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "AGG"
                                                                  "iShares Core U.S. Aggregate Bond ETF")
                                                                 (asset
                                                                  "BND"
                                                                  "Vanguard Total Bond Market ETF")
                                                                 (asset
                                                                  "BNDX"
                                                                  "Vanguard Total International Bond ETF")
                                                                 (asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                 (asset
                                                                  "IEF"
                                                                  "iShares 7-10 Year Treasury Bond ETF")
                                                                 (asset
                                                                  "EMB"
                                                                  "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                                 (asset
                                                                  "BWX"
                                                                  "SPDR Bloomberg International Treasury Bond ETF")
                                                                 (asset
                                                                  "SHV"
                                                                  "iShares Short Treasury Bond ETF")
                                                                 (asset
                                                                  "VGSH"
                                                                  "Vanguard Short-Term Treasury ETF")
                                                                 (asset
                                                                  "GBIL"
                                                                  "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                                 (asset
                                                                  "TYD"
                                                                  "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                 (asset
                                                                  "HYG"
                                                                  "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                                 (asset
                                                                  "TBT"
                                                                  "ProShares UltraShort 20+ Year Treasury")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                               (filter
                                                                (max-drawdown
                                                                 {:window
                                                                  20})
                                                                (select-bottom
                                                                 3)
                                                                [(asset
                                                                  "AGG"
                                                                  "iShares Core U.S. Aggregate Bond ETF")
                                                                 (asset
                                                                  "BND"
                                                                  "Vanguard Total Bond Market ETF")
                                                                 (asset
                                                                  "BNDX"
                                                                  "Vanguard Total International Bond ETF")
                                                                 (asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                 (asset
                                                                  "IEF"
                                                                  "iShares 7-10 Year Treasury Bond ETF")
                                                                 (asset
                                                                  "EMB"
                                                                  "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                                 (asset
                                                                  "BWX"
                                                                  "SPDR Bloomberg International Treasury Bond ETF")
                                                                 (asset
                                                                  "SHV"
                                                                  "iShares Short Treasury Bond ETF")
                                                                 (asset
                                                                  "VGSH"
                                                                  "Vanguard Short-Term Treasury ETF")
                                                                 (asset
                                                                  "GBIL"
                                                                  "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                                 (asset
                                                                  "TYD"
                                                                  "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                 (asset
                                                                  "HYG"
                                                                  "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                                 (asset
                                                                  "TBT"
                                                                  "ProShares UltraShort 20+ Year Treasury")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])
                                                 (group
                                                  "20/60 -> 10/20 | 2007-05-30"
                                                  [(weight-equal
                                                    [(if
                                                      (>
                                                       (rsi
                                                        "AGG"
                                                        {:window 20})
                                                       (rsi
                                                        "SH"
                                                        {:window 60}))
                                                      [(group
                                                        "Risk on"
                                                        [(weight-equal
                                                          [(group
                                                            "Risk-On - Stable/Normal rates"
                                                            [(weight-equal
                                                              [(group
                                                                "SPY"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "AMZN"
                                                                      "Amazon.com, Inc.")
                                                                     (asset
                                                                      "NVDA"
                                                                      "NVIDIA Corporation")
                                                                     (asset
                                                                      "TSLA"
                                                                      "Tesla, Inc.")
                                                                     (asset
                                                                      "GOOG"
                                                                      "Alphabet Inc. Class C")
                                                                     (asset
                                                                      "GOOGL"
                                                                      "Alphabet Inc. Class A")
                                                                     (asset
                                                                      "META"
                                                                      "Meta Platforms Inc. Class A")
                                                                     (asset
                                                                      "BRK/B"
                                                                      "Berkshire Hathaway Inc. Class B")
                                                                     (asset
                                                                      "JNJ"
                                                                      "Johnson & Johnson")
                                                                     (asset
                                                                      "JPM"
                                                                      "JPMorgan Chase & Co.")
                                                                     (asset
                                                                      "XOM"
                                                                      "Exxon Mobil Corporation")
                                                                     (asset
                                                                      "V"
                                                                      "Visa Inc. Class A")
                                                                     (asset
                                                                      "LLY"
                                                                      "Eli Lilly and Company")
                                                                     (asset
                                                                      "AVGO"
                                                                      "Broadcom Inc")])])])
                                                               (group
                                                                "QQQ"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "NFLX"
                                                                      "Netflix, Inc.")
                                                                     (asset
                                                                      "CSCO"
                                                                      "Cisco Systems, Inc.")
                                                                     (asset
                                                                      "COST"
                                                                      "Costco Wholesale Corporation")
                                                                     (asset
                                                                      "AVGO"
                                                                      "Broadcom Inc.")
                                                                     (asset
                                                                      "GOOG"
                                                                      "Alphabet Inc. Class C")
                                                                     (asset
                                                                      "GOOGL"
                                                                      "Alphabet Inc. Class A")
                                                                     (asset
                                                                      "META"
                                                                      "Meta Platforms Inc. Class A")
                                                                     (asset
                                                                      "TSLA"
                                                                      "Tesla, Inc.")
                                                                     (asset
                                                                      "AMZN"
                                                                      "Amazon.com, Inc.")
                                                                     (asset
                                                                      "NVDA"
                                                                      "NVIDIA Corporation")
                                                                     (asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "LIN"
                                                                      "Linde Plc.")
                                                                     (asset
                                                                      "PLTR"
                                                                      "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                                     (asset
                                                                      "TMUS"
                                                                      "T-Mobile US Inc")])])])
                                                               (group
                                                                "DIA"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "UNH"
                                                                      "UnitedHealth Group Incorporated")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "GS"
                                                                      "Goldman Sachs Group, Inc.")
                                                                     (asset
                                                                      "HD"
                                                                      "Home Depot, Inc.")
                                                                     (asset
                                                                      "MCD"
                                                                      "McDonald's Corporation")
                                                                     (asset
                                                                      "TRV"
                                                                      "Travelers Companies, Inc.")
                                                                     (asset
                                                                      "AXP"
                                                                      "American Express Company")
                                                                     (asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "CRM"
                                                                      "Salesforce, Inc.")
                                                                     (asset
                                                                      "AMGN"
                                                                      "Amgen Inc.")
                                                                     (asset
                                                                      "V"
                                                                      "Visa Inc. Class A")
                                                                     (asset
                                                                      "CAT"
                                                                      "Caterpillar Inc.")
                                                                     (asset
                                                                      "IBM"
                                                                      "International Business Machines Corp.")
                                                                     (asset
                                                                      "JPM"
                                                                      "JPMorgan Chase & Co.")])])])])])])])]
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
                                                          [(group
                                                            "Risk on"
                                                            [(weight-equal
                                                              [(group
                                                                "Risk-On - Stable/Normal rates"
                                                                [(weight-equal
                                                                  [(group
                                                                    "SPY"
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          20})
                                                                        (select-top
                                                                         3)
                                                                        [(asset
                                                                          "AAPL"
                                                                          "Apple Inc.")
                                                                         (asset
                                                                          "MSFT"
                                                                          "Microsoft Corporation")
                                                                         (asset
                                                                          "AMZN"
                                                                          "Amazon.com, Inc.")
                                                                         (asset
                                                                          "NVDA"
                                                                          "NVIDIA Corporation")
                                                                         (asset
                                                                          "TSLA"
                                                                          "Tesla, Inc.")
                                                                         (asset
                                                                          "GOOG"
                                                                          "Alphabet Inc. Class C")
                                                                         (asset
                                                                          "GOOGL"
                                                                          "Alphabet Inc. Class A")
                                                                         (asset
                                                                          "META"
                                                                          "Meta Platforms Inc. Class A")
                                                                         (asset
                                                                          "BRK/B"
                                                                          "Berkshire Hathaway Inc. Class B")
                                                                         (asset
                                                                          "JNJ"
                                                                          "Johnson & Johnson")
                                                                         (asset
                                                                          "JPM"
                                                                          "JPMorgan Chase & Co.")
                                                                         (asset
                                                                          "XOM"
                                                                          "Exxon Mobil Corporation")
                                                                         (asset
                                                                          "V"
                                                                          "Visa Inc. Class A")
                                                                         (asset
                                                                          "LLY"
                                                                          "Eli Lilly and Company")
                                                                         (asset
                                                                          "AVGO"
                                                                          "Broadcom Inc")])])])
                                                                   (group
                                                                    "QQQ"
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          20})
                                                                        (select-top
                                                                         3)
                                                                        [(asset
                                                                          "NFLX"
                                                                          "Netflix, Inc.")
                                                                         (asset
                                                                          "CSCO"
                                                                          "Cisco Systems, Inc.")
                                                                         (asset
                                                                          "COST"
                                                                          "Costco Wholesale Corporation")
                                                                         (asset
                                                                          "AVGO"
                                                                          "Broadcom Inc.")
                                                                         (asset
                                                                          "GOOG"
                                                                          "Alphabet Inc. Class C")
                                                                         (asset
                                                                          "GOOGL"
                                                                          "Alphabet Inc. Class A")
                                                                         (asset
                                                                          "META"
                                                                          "Meta Platforms Inc. Class A")
                                                                         (asset
                                                                          "TSLA"
                                                                          "Tesla, Inc.")
                                                                         (asset
                                                                          "AMZN"
                                                                          "Amazon.com, Inc.")
                                                                         (asset
                                                                          "NVDA"
                                                                          "NVIDIA Corporation")
                                                                         (asset
                                                                          "AAPL"
                                                                          "Apple Inc.")
                                                                         (asset
                                                                          "MSFT"
                                                                          "Microsoft Corporation")
                                                                         (asset
                                                                          "LIN"
                                                                          "Linde Plc.")
                                                                         (asset
                                                                          "PLTR"
                                                                          "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                                         (asset
                                                                          "TMUS"
                                                                          "T-Mobile US Inc")])])])
                                                                   (group
                                                                    "DIA"
                                                                    [(weight-equal
                                                                      [(filter
                                                                        (moving-average-return
                                                                         {:window
                                                                          20})
                                                                        (select-top
                                                                         3)
                                                                        [(asset
                                                                          "UNH"
                                                                          "UnitedHealth Group Incorporated")
                                                                         (asset
                                                                          "MSFT"
                                                                          "Microsoft Corporation")
                                                                         (asset
                                                                          "GS"
                                                                          "Goldman Sachs Group, Inc.")
                                                                         (asset
                                                                          "HD"
                                                                          "Home Depot, Inc.")
                                                                         (asset
                                                                          "MCD"
                                                                          "McDonald's Corporation")
                                                                         (asset
                                                                          "TRV"
                                                                          "Travelers Companies, Inc.")
                                                                         (asset
                                                                          "AXP"
                                                                          "American Express Company")
                                                                         (asset
                                                                          "AAPL"
                                                                          "Apple Inc.")
                                                                         (asset
                                                                          "CRM"
                                                                          "Salesforce, Inc.")
                                                                         (asset
                                                                          "AMGN"
                                                                          "Amgen Inc.")
                                                                         (asset
                                                                          "V"
                                                                          "Visa Inc. Class A")
                                                                         (asset
                                                                          "CAT"
                                                                          "Caterpillar Inc.")
                                                                         (asset
                                                                          "IBM"
                                                                          "International Business Machines Corp.")
                                                                         (asset
                                                                          "JPM"
                                                                          "JPMorgan Chase & Co.")])])])])])])])]
                                                          [(group
                                                            "Risk Off"
                                                            [(weight-equal
                                                              [(group
                                                                "Commodities"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      10})
                                                                    (select-top
                                                                     2)
                                                                    [(asset
                                                                      "COM"
                                                                      "Direxion Auspice Broad Commodity Strategy ETF")
                                                                     (asset
                                                                      "FAAR"
                                                                      "First Trust Alternative Absolute Return Strategy ETF")
                                                                     (asset
                                                                      "FTGC"
                                                                      "First Trust Global Tactical Commodity Strategy Fund")
                                                                     (asset
                                                                      "DBC"
                                                                      "Invesco DB Commodity Index Tracking Fund")
                                                                     (asset
                                                                      "PDBC"
                                                                      "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                                     (asset
                                                                      "DBA"
                                                                      "Invesco DB Agriculture Fund")
                                                                     (asset
                                                                      "GLTR"
                                                                      "abrdn Physical Precious Metals Basket Shares ETF")
                                                                     (asset
                                                                      "DBB"
                                                                      "Invesco DB Base Metals Fund")])
                                                                   (filter
                                                                    (max-drawdown
                                                                     {:window
                                                                      20})
                                                                    (select-bottom
                                                                     2)
                                                                    [(asset
                                                                      "COM"
                                                                      "Direxion Auspice Broad Commodity Strategy ETF")
                                                                     (asset
                                                                      "FAAR"
                                                                      "First Trust Alternative Absolute Return Strategy ETF")
                                                                     (asset
                                                                      "FTGC"
                                                                      "First Trust Global Tactical Commodity Strategy Fund")
                                                                     (asset
                                                                      "DBC"
                                                                      "Invesco DB Commodity Index Tracking Fund")
                                                                     (asset
                                                                      "PDBC"
                                                                      "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                                     (asset
                                                                      "DBA"
                                                                      "Invesco DB Agriculture Fund")
                                                                     (asset
                                                                      "GLTR"
                                                                      "abrdn Physical Precious Metals Basket Shares ETF")
                                                                     (asset
                                                                      "DBB"
                                                                      "Invesco DB Base Metals Fund")])])])
                                                               (group
                                                                "Bonds"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      10})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "AGG"
                                                                      "iShares Core U.S. Aggregate Bond ETF")
                                                                     (asset
                                                                      "BND"
                                                                      "Vanguard Total Bond Market ETF")
                                                                     (asset
                                                                      "BNDX"
                                                                      "Vanguard Total International Bond ETF")
                                                                     (asset
                                                                      "BIL"
                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                     (asset
                                                                      "IEF"
                                                                      "iShares 7-10 Year Treasury Bond ETF")
                                                                     (asset
                                                                      "EMB"
                                                                      "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                                     (asset
                                                                      "BWX"
                                                                      "SPDR Bloomberg International Treasury Bond ETF")
                                                                     (asset
                                                                      "SHV"
                                                                      "iShares Short Treasury Bond ETF")
                                                                     (asset
                                                                      "VGSH"
                                                                      "Vanguard Short-Term Treasury ETF")
                                                                     (asset
                                                                      "GBIL"
                                                                      "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                                     (asset
                                                                      "TYD"
                                                                      "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                                     (asset
                                                                      "TMF"
                                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                     (asset
                                                                      "HYG"
                                                                      "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                                     (asset
                                                                      "TBT"
                                                                      "ProShares UltraShort 20+ Year Treasury")
                                                                     (asset
                                                                      "TMV"
                                                                      "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                                   (filter
                                                                    (max-drawdown
                                                                     {:window
                                                                      20})
                                                                    (select-bottom
                                                                     3)
                                                                    [(asset
                                                                      "AGG"
                                                                      "iShares Core U.S. Aggregate Bond ETF")
                                                                     (asset
                                                                      "BND"
                                                                      "Vanguard Total Bond Market ETF")
                                                                     (asset
                                                                      "BNDX"
                                                                      "Vanguard Total International Bond ETF")
                                                                     (asset
                                                                      "BIL"
                                                                      "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                     (asset
                                                                      "IEF"
                                                                      "iShares 7-10 Year Treasury Bond ETF")
                                                                     (asset
                                                                      "EMB"
                                                                      "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                                     (asset
                                                                      "BWX"
                                                                      "SPDR Bloomberg International Treasury Bond ETF")
                                                                     (asset
                                                                      "SHV"
                                                                      "iShares Short Treasury Bond ETF")
                                                                     (asset
                                                                      "VGSH"
                                                                      "Vanguard Short-Term Treasury ETF")
                                                                     (asset
                                                                      "GBIL"
                                                                      "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                                     (asset
                                                                      "TYD"
                                                                      "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                                     (asset
                                                                      "TMF"
                                                                      "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                     (asset
                                                                      "HYG"
                                                                      "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                                     (asset
                                                                      "TBT"
                                                                      "ProShares UltraShort 20+ Year Treasury")
                                                                     (asset
                                                                      "TMV"
                                                                      "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])
                                                 (group
                                                  "60d BND vs 60d BIL | 2007-08-23"
                                                  [(weight-equal
                                                    [(if
                                                      (>
                                                       (cumulative-return
                                                        "BND"
                                                        {:window 60})
                                                       (cumulative-return
                                                        "BIL"
                                                        {:window 60}))
                                                      [(group
                                                        "Risk on"
                                                        [(weight-equal
                                                          [(group
                                                            "Risk-On - Stable/Normal rates"
                                                            [(weight-equal
                                                              [(group
                                                                "SPY"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "AMZN"
                                                                      "Amazon.com, Inc.")
                                                                     (asset
                                                                      "NVDA"
                                                                      "NVIDIA Corporation")
                                                                     (asset
                                                                      "TSLA"
                                                                      "Tesla, Inc.")
                                                                     (asset
                                                                      "GOOG"
                                                                      "Alphabet Inc. Class C")
                                                                     (asset
                                                                      "GOOGL"
                                                                      "Alphabet Inc. Class A")
                                                                     (asset
                                                                      "META"
                                                                      "Meta Platforms Inc. Class A")
                                                                     (asset
                                                                      "BRK/B"
                                                                      "Berkshire Hathaway Inc. Class B")
                                                                     (asset
                                                                      "JNJ"
                                                                      "Johnson & Johnson")
                                                                     (asset
                                                                      "JPM"
                                                                      "JPMorgan Chase & Co.")
                                                                     (asset
                                                                      "XOM"
                                                                      "Exxon Mobil Corporation")
                                                                     (asset
                                                                      "V"
                                                                      "Visa Inc. Class A")
                                                                     (asset
                                                                      "LLY"
                                                                      "Eli Lilly and Company")
                                                                     (asset
                                                                      "AVGO"
                                                                      "Broadcom Inc")])])])
                                                               (group
                                                                "QQQ"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "NFLX"
                                                                      "Netflix, Inc.")
                                                                     (asset
                                                                      "CSCO"
                                                                      "Cisco Systems, Inc.")
                                                                     (asset
                                                                      "COST"
                                                                      "Costco Wholesale Corporation")
                                                                     (asset
                                                                      "AVGO"
                                                                      "Broadcom Inc.")
                                                                     (asset
                                                                      "GOOG"
                                                                      "Alphabet Inc. Class C")
                                                                     (asset
                                                                      "GOOGL"
                                                                      "Alphabet Inc. Class A")
                                                                     (asset
                                                                      "META"
                                                                      "Meta Platforms Inc. Class A")
                                                                     (asset
                                                                      "TSLA"
                                                                      "Tesla, Inc.")
                                                                     (asset
                                                                      "AMZN"
                                                                      "Amazon.com, Inc.")
                                                                     (asset
                                                                      "NVDA"
                                                                      "NVIDIA Corporation")
                                                                     (asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "LIN"
                                                                      "Linde Plc.")
                                                                     (asset
                                                                      "PLTR"
                                                                      "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                                     (asset
                                                                      "TMUS"
                                                                      "T-Mobile US Inc")])])])
                                                               (group
                                                                "DIA"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "UNH"
                                                                      "UnitedHealth Group Incorporated")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "GS"
                                                                      "Goldman Sachs Group, Inc.")
                                                                     (asset
                                                                      "HD"
                                                                      "Home Depot, Inc.")
                                                                     (asset
                                                                      "MCD"
                                                                      "McDonald's Corporation")
                                                                     (asset
                                                                      "TRV"
                                                                      "Travelers Companies, Inc.")
                                                                     (asset
                                                                      "AXP"
                                                                      "American Express Company")
                                                                     (asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "CRM"
                                                                      "Salesforce, Inc.")
                                                                     (asset
                                                                      "AMGN"
                                                                      "Amgen Inc.")
                                                                     (asset
                                                                      "V"
                                                                      "Visa Inc. Class A")
                                                                     (asset
                                                                      "CAT"
                                                                      "Caterpillar Inc.")
                                                                     (asset
                                                                      "IBM"
                                                                      "International Business Machines Corp.")
                                                                     (asset
                                                                      "JPM"
                                                                      "JPMorgan Chase & Co.")])])])])])])])]
                                                      [(group
                                                        "Risk Off"
                                                        [(weight-equal
                                                          [(group
                                                            "Commodities"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  10})
                                                                (select-top
                                                                 2)
                                                                [(asset
                                                                  "COM"
                                                                  "Direxion Auspice Broad Commodity Strategy ETF")
                                                                 (asset
                                                                  "FAAR"
                                                                  "First Trust Alternative Absolute Return Strategy ETF")
                                                                 (asset
                                                                  "FTGC"
                                                                  "First Trust Global Tactical Commodity Strategy Fund")
                                                                 (asset
                                                                  "DBC"
                                                                  "Invesco DB Commodity Index Tracking Fund")
                                                                 (asset
                                                                  "PDBC"
                                                                  "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                                 (asset
                                                                  "DBA"
                                                                  "Invesco DB Agriculture Fund")
                                                                 (asset
                                                                  "GLTR"
                                                                  "abrdn Physical Precious Metals Basket Shares ETF")
                                                                 (asset
                                                                  "DBB"
                                                                  "Invesco DB Base Metals Fund")])
                                                               (filter
                                                                (max-drawdown
                                                                 {:window
                                                                  20})
                                                                (select-bottom
                                                                 2)
                                                                [(asset
                                                                  "COM"
                                                                  "Direxion Auspice Broad Commodity Strategy ETF")
                                                                 (asset
                                                                  "FAAR"
                                                                  "First Trust Alternative Absolute Return Strategy ETF")
                                                                 (asset
                                                                  "FTGC"
                                                                  "First Trust Global Tactical Commodity Strategy Fund")
                                                                 (asset
                                                                  "DBC"
                                                                  "Invesco DB Commodity Index Tracking Fund")
                                                                 (asset
                                                                  "PDBC"
                                                                  "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                                 (asset
                                                                  "DBA"
                                                                  "Invesco DB Agriculture Fund")
                                                                 (asset
                                                                  "GLTR"
                                                                  "abrdn Physical Precious Metals Basket Shares ETF")
                                                                 (asset
                                                                  "DBB"
                                                                  "Invesco DB Base Metals Fund")])])])
                                                           (group
                                                            "Bonds"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  10})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "AGG"
                                                                  "iShares Core U.S. Aggregate Bond ETF")
                                                                 (asset
                                                                  "BND"
                                                                  "Vanguard Total Bond Market ETF")
                                                                 (asset
                                                                  "BNDX"
                                                                  "Vanguard Total International Bond ETF")
                                                                 (asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                 (asset
                                                                  "IEF"
                                                                  "iShares 7-10 Year Treasury Bond ETF")
                                                                 (asset
                                                                  "EMB"
                                                                  "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                                 (asset
                                                                  "BWX"
                                                                  "SPDR Bloomberg International Treasury Bond ETF")
                                                                 (asset
                                                                  "SHV"
                                                                  "iShares Short Treasury Bond ETF")
                                                                 (asset
                                                                  "VGSH"
                                                                  "Vanguard Short-Term Treasury ETF")
                                                                 (asset
                                                                  "GBIL"
                                                                  "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                                 (asset
                                                                  "TYD"
                                                                  "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                 (asset
                                                                  "HYG"
                                                                  "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                                 (asset
                                                                  "TBT"
                                                                  "ProShares UltraShort 20+ Year Treasury")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                               (filter
                                                                (max-drawdown
                                                                 {:window
                                                                  20})
                                                                (select-bottom
                                                                 3)
                                                                [(asset
                                                                  "AGG"
                                                                  "iShares Core U.S. Aggregate Bond ETF")
                                                                 (asset
                                                                  "BND"
                                                                  "Vanguard Total Bond Market ETF")
                                                                 (asset
                                                                  "BNDX"
                                                                  "Vanguard Total International Bond ETF")
                                                                 (asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                 (asset
                                                                  "IEF"
                                                                  "iShares 7-10 Year Treasury Bond ETF")
                                                                 (asset
                                                                  "EMB"
                                                                  "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                                 (asset
                                                                  "BWX"
                                                                  "SPDR Bloomberg International Treasury Bond ETF")
                                                                 (asset
                                                                  "SHV"
                                                                  "iShares Short Treasury Bond ETF")
                                                                 (asset
                                                                  "VGSH"
                                                                  "Vanguard Short-Term Treasury ETF")
                                                                 (asset
                                                                  "GBIL"
                                                                  "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                                 (asset
                                                                  "TYD"
                                                                  "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                 (asset
                                                                  "HYG"
                                                                  "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                                 (asset
                                                                  "TBT"
                                                                  "ProShares UltraShort 20+ Year Treasury")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])
                                                 (group
                                                  "200d FDN vs 200d XLU | 2007-05-30"
                                                  [(weight-equal
                                                    [(if
                                                      (>
                                                       (rsi
                                                        "FDN"
                                                        {:window 200})
                                                       (rsi
                                                        "XLU"
                                                        {:window 200}))
                                                      [(group
                                                        "Risk on"
                                                        [(weight-equal
                                                          [(group
                                                            "Risk-On - Stable/Normal rates"
                                                            [(weight-equal
                                                              [(group
                                                                "SPY"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "AMZN"
                                                                      "Amazon.com, Inc.")
                                                                     (asset
                                                                      "NVDA"
                                                                      "NVIDIA Corporation")
                                                                     (asset
                                                                      "TSLA"
                                                                      "Tesla, Inc.")
                                                                     (asset
                                                                      "GOOG"
                                                                      "Alphabet Inc. Class C")
                                                                     (asset
                                                                      "GOOGL"
                                                                      "Alphabet Inc. Class A")
                                                                     (asset
                                                                      "META"
                                                                      "Meta Platforms Inc. Class A")
                                                                     (asset
                                                                      "BRK/B"
                                                                      "Berkshire Hathaway Inc. Class B")
                                                                     (asset
                                                                      "JNJ"
                                                                      "Johnson & Johnson")
                                                                     (asset
                                                                      "JPM"
                                                                      "JPMorgan Chase & Co.")
                                                                     (asset
                                                                      "XOM"
                                                                      "Exxon Mobil Corporation")
                                                                     (asset
                                                                      "V"
                                                                      "Visa Inc. Class A")
                                                                     (asset
                                                                      "LLY"
                                                                      "Eli Lilly and Company")
                                                                     (asset
                                                                      "AVGO"
                                                                      "Broadcom Inc")])])])
                                                               (group
                                                                "QQQ"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "NFLX"
                                                                      "Netflix, Inc.")
                                                                     (asset
                                                                      "CSCO"
                                                                      "Cisco Systems, Inc.")
                                                                     (asset
                                                                      "COST"
                                                                      "Costco Wholesale Corporation")
                                                                     (asset
                                                                      "AVGO"
                                                                      "Broadcom Inc.")
                                                                     (asset
                                                                      "GOOG"
                                                                      "Alphabet Inc. Class C")
                                                                     (asset
                                                                      "GOOGL"
                                                                      "Alphabet Inc. Class A")
                                                                     (asset
                                                                      "META"
                                                                      "Meta Platforms Inc. Class A")
                                                                     (asset
                                                                      "TSLA"
                                                                      "Tesla, Inc.")
                                                                     (asset
                                                                      "AMZN"
                                                                      "Amazon.com, Inc.")
                                                                     (asset
                                                                      "NVDA"
                                                                      "NVIDIA Corporation")
                                                                     (asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "LIN"
                                                                      "Linde Plc.")
                                                                     (asset
                                                                      "PLTR"
                                                                      "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                                     (asset
                                                                      "TMUS"
                                                                      "T-Mobile US Inc")])])])
                                                               (group
                                                                "DIA"
                                                                [(weight-equal
                                                                  [(filter
                                                                    (moving-average-return
                                                                     {:window
                                                                      20})
                                                                    (select-top
                                                                     3)
                                                                    [(asset
                                                                      "UNH"
                                                                      "UnitedHealth Group Incorporated")
                                                                     (asset
                                                                      "MSFT"
                                                                      "Microsoft Corporation")
                                                                     (asset
                                                                      "GS"
                                                                      "Goldman Sachs Group, Inc.")
                                                                     (asset
                                                                      "HD"
                                                                      "Home Depot, Inc.")
                                                                     (asset
                                                                      "MCD"
                                                                      "McDonald's Corporation")
                                                                     (asset
                                                                      "TRV"
                                                                      "Travelers Companies, Inc.")
                                                                     (asset
                                                                      "AXP"
                                                                      "American Express Company")
                                                                     (asset
                                                                      "AAPL"
                                                                      "Apple Inc.")
                                                                     (asset
                                                                      "CRM"
                                                                      "Salesforce, Inc.")
                                                                     (asset
                                                                      "AMGN"
                                                                      "Amgen Inc.")
                                                                     (asset
                                                                      "V"
                                                                      "Visa Inc. Class A")
                                                                     (asset
                                                                      "CAT"
                                                                      "Caterpillar Inc.")
                                                                     (asset
                                                                      "IBM"
                                                                      "International Business Machines Corp.")
                                                                     (asset
                                                                      "JPM"
                                                                      "JPMorgan Chase & Co.")])])])])])])])]
                                                      [(group
                                                        "Risk Off"
                                                        [(weight-equal
                                                          [(group
                                                            "Commodities"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  10})
                                                                (select-top
                                                                 2)
                                                                [(asset
                                                                  "COM"
                                                                  "Direxion Auspice Broad Commodity Strategy ETF")
                                                                 (asset
                                                                  "FAAR"
                                                                  "First Trust Alternative Absolute Return Strategy ETF")
                                                                 (asset
                                                                  "FTGC"
                                                                  "First Trust Global Tactical Commodity Strategy Fund")
                                                                 (asset
                                                                  "DBC"
                                                                  "Invesco DB Commodity Index Tracking Fund")
                                                                 (asset
                                                                  "PDBC"
                                                                  "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                                 (asset
                                                                  "DBA"
                                                                  "Invesco DB Agriculture Fund")
                                                                 (asset
                                                                  "GLTR"
                                                                  "abrdn Physical Precious Metals Basket Shares ETF")
                                                                 (asset
                                                                  "DBB"
                                                                  "Invesco DB Base Metals Fund")])
                                                               (filter
                                                                (max-drawdown
                                                                 {:window
                                                                  20})
                                                                (select-bottom
                                                                 2)
                                                                [(asset
                                                                  "COM"
                                                                  "Direxion Auspice Broad Commodity Strategy ETF")
                                                                 (asset
                                                                  "FAAR"
                                                                  "First Trust Alternative Absolute Return Strategy ETF")
                                                                 (asset
                                                                  "FTGC"
                                                                  "First Trust Global Tactical Commodity Strategy Fund")
                                                                 (asset
                                                                  "DBC"
                                                                  "Invesco DB Commodity Index Tracking Fund")
                                                                 (asset
                                                                  "PDBC"
                                                                  "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                                 (asset
                                                                  "DBA"
                                                                  "Invesco DB Agriculture Fund")
                                                                 (asset
                                                                  "GLTR"
                                                                  "abrdn Physical Precious Metals Basket Shares ETF")
                                                                 (asset
                                                                  "DBB"
                                                                  "Invesco DB Base Metals Fund")])])])
                                                           (group
                                                            "Bonds"
                                                            [(weight-equal
                                                              [(filter
                                                                (moving-average-return
                                                                 {:window
                                                                  10})
                                                                (select-top
                                                                 3)
                                                                [(asset
                                                                  "AGG"
                                                                  "iShares Core U.S. Aggregate Bond ETF")
                                                                 (asset
                                                                  "BND"
                                                                  "Vanguard Total Bond Market ETF")
                                                                 (asset
                                                                  "BNDX"
                                                                  "Vanguard Total International Bond ETF")
                                                                 (asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                 (asset
                                                                  "IEF"
                                                                  "iShares 7-10 Year Treasury Bond ETF")
                                                                 (asset
                                                                  "EMB"
                                                                  "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                                 (asset
                                                                  "BWX"
                                                                  "SPDR Bloomberg International Treasury Bond ETF")
                                                                 (asset
                                                                  "SHV"
                                                                  "iShares Short Treasury Bond ETF")
                                                                 (asset
                                                                  "VGSH"
                                                                  "Vanguard Short-Term Treasury ETF")
                                                                 (asset
                                                                  "GBIL"
                                                                  "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                                 (asset
                                                                  "TYD"
                                                                  "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                 (asset
                                                                  "HYG"
                                                                  "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                                 (asset
                                                                  "TBT"
                                                                  "ProShares UltraShort 20+ Year Treasury")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                               (filter
                                                                (max-drawdown
                                                                 {:window
                                                                  20})
                                                                (select-bottom
                                                                 3)
                                                                [(asset
                                                                  "AGG"
                                                                  "iShares Core U.S. Aggregate Bond ETF")
                                                                 (asset
                                                                  "BND"
                                                                  "Vanguard Total Bond Market ETF")
                                                                 (asset
                                                                  "BNDX"
                                                                  "Vanguard Total International Bond ETF")
                                                                 (asset
                                                                  "BIL"
                                                                  "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                                 (asset
                                                                  "IEF"
                                                                  "iShares 7-10 Year Treasury Bond ETF")
                                                                 (asset
                                                                  "EMB"
                                                                  "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                                 (asset
                                                                  "BWX"
                                                                  "SPDR Bloomberg International Treasury Bond ETF")
                                                                 (asset
                                                                  "SHV"
                                                                  "iShares Short Treasury Bond ETF")
                                                                 (asset
                                                                  "VGSH"
                                                                  "Vanguard Short-Term Treasury ETF")
                                                                 (asset
                                                                  "GBIL"
                                                                  "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                                 (asset
                                                                  "TYD"
                                                                  "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                                 (asset
                                                                  "TMF"
                                                                  "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                                 (asset
                                                                  "HYG"
                                                                  "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                                 (asset
                                                                  "TBT"
                                                                  "ProShares UltraShort 20+ Year Treasury")
                                                                 (asset
                                                                  "TMV"
                                                                  "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])]
                                            [(asset
                                              "BIL"
                                              "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")])])])])])
                                   (group
                                    "FTLT"
                                    [(weight-equal
                                      [(if
                                        (>
                                         (current-price "SPY")
                                         (moving-average-price
                                          "SPY"
                                          {:window 200}))
                                        [(group
                                          "Risk on"
                                          [(weight-equal
                                            [(group
                                              "Risk-On - Stable/Normal rates"
                                              [(weight-equal
                                                [(group
                                                  "SPY"
                                                  [(weight-equal
                                                    [(filter
                                                      (moving-average-return
                                                       {:window 20})
                                                      (select-top 3)
                                                      [(asset
                                                        "AAPL"
                                                        "Apple Inc.")
                                                       (asset
                                                        "MSFT"
                                                        "Microsoft Corporation")
                                                       (asset
                                                        "AMZN"
                                                        "Amazon.com, Inc.")
                                                       (asset
                                                        "NVDA"
                                                        "NVIDIA Corporation")
                                                       (asset
                                                        "TSLA"
                                                        "Tesla, Inc.")
                                                       (asset
                                                        "GOOG"
                                                        "Alphabet Inc. Class C")
                                                       (asset
                                                        "GOOGL"
                                                        "Alphabet Inc. Class A")
                                                       (asset
                                                        "META"
                                                        "Meta Platforms Inc. Class A")
                                                       (asset
                                                        "BRK/B"
                                                        "Berkshire Hathaway Inc. Class B")
                                                       (asset
                                                        "JNJ"
                                                        "Johnson & Johnson")
                                                       (asset
                                                        "JPM"
                                                        "JPMorgan Chase & Co.")
                                                       (asset
                                                        "XOM"
                                                        "Exxon Mobil Corporation")
                                                       (asset
                                                        "V"
                                                        "Visa Inc. Class A")
                                                       (asset
                                                        "LLY"
                                                        "Eli Lilly and Company")
                                                       (asset
                                                        "AVGO"
                                                        "Broadcom Inc")])])])
                                                 (group
                                                  "QQQ"
                                                  [(weight-equal
                                                    [(filter
                                                      (moving-average-return
                                                       {:window 20})
                                                      (select-top 3)
                                                      [(asset
                                                        "NFLX"
                                                        "Netflix, Inc.")
                                                       (asset
                                                        "CSCO"
                                                        "Cisco Systems, Inc.")
                                                       (asset
                                                        "COST"
                                                        "Costco Wholesale Corporation")
                                                       (asset
                                                        "AVGO"
                                                        "Broadcom Inc.")
                                                       (asset
                                                        "GOOG"
                                                        "Alphabet Inc. Class C")
                                                       (asset
                                                        "GOOGL"
                                                        "Alphabet Inc. Class A")
                                                       (asset
                                                        "META"
                                                        "Meta Platforms Inc. Class A")
                                                       (asset
                                                        "TSLA"
                                                        "Tesla, Inc.")
                                                       (asset
                                                        "AMZN"
                                                        "Amazon.com, Inc.")
                                                       (asset
                                                        "NVDA"
                                                        "NVIDIA Corporation")
                                                       (asset
                                                        "AAPL"
                                                        "Apple Inc.")
                                                       (asset
                                                        "MSFT"
                                                        "Microsoft Corporation")
                                                       (asset
                                                        "LIN"
                                                        "Linde Plc.")
                                                       (asset
                                                        "PLTR"
                                                        "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                       (asset
                                                        "TMUS"
                                                        "T-Mobile US Inc")])])])
                                                 (group
                                                  "DIA"
                                                  [(weight-equal
                                                    [(filter
                                                      (moving-average-return
                                                       {:window 20})
                                                      (select-top 3)
                                                      [(asset
                                                        "UNH"
                                                        "UnitedHealth Group Incorporated")
                                                       (asset
                                                        "MSFT"
                                                        "Microsoft Corporation")
                                                       (asset
                                                        "GS"
                                                        "Goldman Sachs Group, Inc.")
                                                       (asset
                                                        "HD"
                                                        "Home Depot, Inc.")
                                                       (asset
                                                        "MCD"
                                                        "McDonald's Corporation")
                                                       (asset
                                                        "TRV"
                                                        "Travelers Companies, Inc.")
                                                       (asset
                                                        "AXP"
                                                        "American Express Company")
                                                       (asset
                                                        "AAPL"
                                                        "Apple Inc.")
                                                       (asset
                                                        "CRM"
                                                        "Salesforce, Inc.")
                                                       (asset
                                                        "AMGN"
                                                        "Amgen Inc.")
                                                       (asset
                                                        "V"
                                                        "Visa Inc. Class A")
                                                       (asset
                                                        "CAT"
                                                        "Caterpillar Inc.")
                                                       (asset
                                                        "IBM"
                                                        "International Business Machines Corp.")
                                                       (asset
                                                        "JPM"
                                                        "JPMorgan Chase & Co.")])])])])])])])]
                                        [(group
                                          "Risk Off"
                                          [(weight-equal
                                            [(group
                                              "Commodities"
                                              [(weight-equal
                                                [(filter
                                                  (moving-average-return
                                                   {:window 10})
                                                  (select-top 2)
                                                  [(asset
                                                    "COM"
                                                    "Direxion Auspice Broad Commodity Strategy ETF")
                                                   (asset
                                                    "FAAR"
                                                    "First Trust Alternative Absolute Return Strategy ETF")
                                                   (asset
                                                    "FTGC"
                                                    "First Trust Global Tactical Commodity Strategy Fund")
                                                   (asset
                                                    "DBC"
                                                    "Invesco DB Commodity Index Tracking Fund")
                                                   (asset
                                                    "PDBC"
                                                    "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                   (asset
                                                    "DBA"
                                                    "Invesco DB Agriculture Fund")
                                                   (asset
                                                    "GLTR"
                                                    "abrdn Physical Precious Metals Basket Shares ETF")
                                                   (asset
                                                    "DBB"
                                                    "Invesco DB Base Metals Fund")])
                                                 (filter
                                                  (max-drawdown
                                                   {:window 20})
                                                  (select-bottom 2)
                                                  [(asset
                                                    "COM"
                                                    "Direxion Auspice Broad Commodity Strategy ETF")
                                                   (asset
                                                    "FAAR"
                                                    "First Trust Alternative Absolute Return Strategy ETF")
                                                   (asset
                                                    "FTGC"
                                                    "First Trust Global Tactical Commodity Strategy Fund")
                                                   (asset
                                                    "DBC"
                                                    "Invesco DB Commodity Index Tracking Fund")
                                                   (asset
                                                    "PDBC"
                                                    "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                   (asset
                                                    "DBA"
                                                    "Invesco DB Agriculture Fund")
                                                   (asset
                                                    "GLTR"
                                                    "abrdn Physical Precious Metals Basket Shares ETF")
                                                   (asset
                                                    "DBB"
                                                    "Invesco DB Base Metals Fund")])])])
                                             (group
                                              "Bonds"
                                              [(weight-equal
                                                [(filter
                                                  (moving-average-return
                                                   {:window 10})
                                                  (select-top 3)
                                                  [(asset
                                                    "AGG"
                                                    "iShares Core U.S. Aggregate Bond ETF")
                                                   (asset
                                                    "BND"
                                                    "Vanguard Total Bond Market ETF")
                                                   (asset
                                                    "BNDX"
                                                    "Vanguard Total International Bond ETF")
                                                   (asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                   (asset
                                                    "IEF"
                                                    "iShares 7-10 Year Treasury Bond ETF")
                                                   (asset
                                                    "EMB"
                                                    "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                   (asset
                                                    "BWX"
                                                    "SPDR Bloomberg International Treasury Bond ETF")
                                                   (asset
                                                    "SHV"
                                                    "iShares Short Treasury Bond ETF")
                                                   (asset
                                                    "VGSH"
                                                    "Vanguard Short-Term Treasury ETF")
                                                   (asset
                                                    "GBIL"
                                                    "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                   (asset
                                                    "TYD"
                                                    "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                   (asset
                                                    "HYG"
                                                    "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                   (asset
                                                    "TBT"
                                                    "ProShares UltraShort 20+ Year Treasury")
                                                   (asset
                                                    "TMV"
                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                 (filter
                                                  (max-drawdown
                                                   {:window 20})
                                                  (select-bottom 3)
                                                  [(asset
                                                    "AGG"
                                                    "iShares Core U.S. Aggregate Bond ETF")
                                                   (asset
                                                    "BND"
                                                    "Vanguard Total Bond Market ETF")
                                                   (asset
                                                    "BNDX"
                                                    "Vanguard Total International Bond ETF")
                                                   (asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                   (asset
                                                    "IEF"
                                                    "iShares 7-10 Year Treasury Bond ETF")
                                                   (asset
                                                    "EMB"
                                                    "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                   (asset
                                                    "BWX"
                                                    "SPDR Bloomberg International Treasury Bond ETF")
                                                   (asset
                                                    "SHV"
                                                    "iShares Short Treasury Bond ETF")
                                                   (asset
                                                    "VGSH"
                                                    "Vanguard Short-Term Treasury ETF")
                                                   (asset
                                                    "GBIL"
                                                    "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                   (asset
                                                    "TYD"
                                                    "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                   (asset
                                                    "HYG"
                                                    "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                   (asset
                                                    "TBT"
                                                    "ProShares UltraShort 20+ Year Treasury")
                                                   (asset
                                                    "TMV"
                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])
                                   (group
                                    "KMLM"
                                    [(weight-equal
                                      [(if
                                        (>
                                         (rsi "XLK" {:window 10})
                                         (rsi "KMLM" {:window 10}))
                                        [(weight-equal
                                          [(group
                                            "Risk on"
                                            [(weight-equal
                                              [(group
                                                "Risk-On - Stable/Normal rates"
                                                [(weight-equal
                                                  [(group
                                                    "SPY"
                                                    [(weight-equal
                                                      [(filter
                                                        (moving-average-return
                                                         {:window 20})
                                                        (select-top 3)
                                                        [(asset
                                                          "AAPL"
                                                          "Apple Inc.")
                                                         (asset
                                                          "MSFT"
                                                          "Microsoft Corporation")
                                                         (asset
                                                          "AMZN"
                                                          "Amazon.com, Inc.")
                                                         (asset
                                                          "NVDA"
                                                          "NVIDIA Corporation")
                                                         (asset
                                                          "TSLA"
                                                          "Tesla, Inc.")
                                                         (asset
                                                          "GOOG"
                                                          "Alphabet Inc. Class C")
                                                         (asset
                                                          "GOOGL"
                                                          "Alphabet Inc. Class A")
                                                         (asset
                                                          "META"
                                                          "Meta Platforms Inc. Class A")
                                                         (asset
                                                          "BRK/B"
                                                          "Berkshire Hathaway Inc. Class B")
                                                         (asset
                                                          "JNJ"
                                                          "Johnson & Johnson")
                                                         (asset
                                                          "JPM"
                                                          "JPMorgan Chase & Co.")
                                                         (asset
                                                          "XOM"
                                                          "Exxon Mobil Corporation")
                                                         (asset
                                                          "V"
                                                          "Visa Inc. Class A")
                                                         (asset
                                                          "LLY"
                                                          "Eli Lilly and Company")
                                                         (asset
                                                          "AVGO"
                                                          "Broadcom Inc")])])])
                                                   (group
                                                    "QQQ"
                                                    [(weight-equal
                                                      [(filter
                                                        (moving-average-return
                                                         {:window 20})
                                                        (select-top 3)
                                                        [(asset
                                                          "NFLX"
                                                          "Netflix, Inc.")
                                                         (asset
                                                          "CSCO"
                                                          "Cisco Systems, Inc.")
                                                         (asset
                                                          "COST"
                                                          "Costco Wholesale Corporation")
                                                         (asset
                                                          "AVGO"
                                                          "Broadcom Inc.")
                                                         (asset
                                                          "GOOG"
                                                          "Alphabet Inc. Class C")
                                                         (asset
                                                          "GOOGL"
                                                          "Alphabet Inc. Class A")
                                                         (asset
                                                          "META"
                                                          "Meta Platforms Inc. Class A")
                                                         (asset
                                                          "TSLA"
                                                          "Tesla, Inc.")
                                                         (asset
                                                          "AMZN"
                                                          "Amazon.com, Inc.")
                                                         (asset
                                                          "NVDA"
                                                          "NVIDIA Corporation")
                                                         (asset
                                                          "AAPL"
                                                          "Apple Inc.")
                                                         (asset
                                                          "MSFT"
                                                          "Microsoft Corporation")
                                                         (asset
                                                          "LIN"
                                                          "Linde Plc.")
                                                         (asset
                                                          "PLTR"
                                                          "Palantir Technologies Inc - Ordinary Shares - Class A")
                                                         (asset
                                                          "TMUS"
                                                          "T-Mobile US Inc")])])])
                                                   (group
                                                    "DIA"
                                                    [(weight-equal
                                                      [(filter
                                                        (moving-average-return
                                                         {:window 20})
                                                        (select-top 3)
                                                        [(asset
                                                          "UNH"
                                                          "UnitedHealth Group Incorporated")
                                                         (asset
                                                          "MSFT"
                                                          "Microsoft Corporation")
                                                         (asset
                                                          "GS"
                                                          "Goldman Sachs Group, Inc.")
                                                         (asset
                                                          "HD"
                                                          "Home Depot, Inc.")
                                                         (asset
                                                          "MCD"
                                                          "McDonald's Corporation")
                                                         (asset
                                                          "TRV"
                                                          "Travelers Companies, Inc.")
                                                         (asset
                                                          "AXP"
                                                          "American Express Company")
                                                         (asset
                                                          "AAPL"
                                                          "Apple Inc.")
                                                         (asset
                                                          "CRM"
                                                          "Salesforce, Inc.")
                                                         (asset
                                                          "AMGN"
                                                          "Amgen Inc.")
                                                         (asset
                                                          "V"
                                                          "Visa Inc. Class A")
                                                         (asset
                                                          "CAT"
                                                          "Caterpillar Inc.")
                                                         (asset
                                                          "IBM"
                                                          "International Business Machines Corp.")
                                                         (asset
                                                          "JPM"
                                                          "JPMorgan Chase & Co.")])])])])])])])])]
                                        [(group
                                          "Risk Off"
                                          [(weight-equal
                                            [(group
                                              "Commodities"
                                              [(weight-equal
                                                [(filter
                                                  (moving-average-return
                                                   {:window 10})
                                                  (select-top 2)
                                                  [(asset
                                                    "COM"
                                                    "Direxion Auspice Broad Commodity Strategy ETF")
                                                   (asset
                                                    "FAAR"
                                                    "First Trust Alternative Absolute Return Strategy ETF")
                                                   (asset
                                                    "FTGC"
                                                    "First Trust Global Tactical Commodity Strategy Fund")
                                                   (asset
                                                    "DBC"
                                                    "Invesco DB Commodity Index Tracking Fund")
                                                   (asset
                                                    "PDBC"
                                                    "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                   (asset
                                                    "DBA"
                                                    "Invesco DB Agriculture Fund")
                                                   (asset
                                                    "GLTR"
                                                    "abrdn Physical Precious Metals Basket Shares ETF")
                                                   (asset
                                                    "DBB"
                                                    "Invesco DB Base Metals Fund")])
                                                 (filter
                                                  (max-drawdown
                                                   {:window 20})
                                                  (select-bottom 2)
                                                  [(asset
                                                    "COM"
                                                    "Direxion Auspice Broad Commodity Strategy ETF")
                                                   (asset
                                                    "FAAR"
                                                    "First Trust Alternative Absolute Return Strategy ETF")
                                                   (asset
                                                    "FTGC"
                                                    "First Trust Global Tactical Commodity Strategy Fund")
                                                   (asset
                                                    "DBC"
                                                    "Invesco DB Commodity Index Tracking Fund")
                                                   (asset
                                                    "PDBC"
                                                    "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF")
                                                   (asset
                                                    "DBA"
                                                    "Invesco DB Agriculture Fund")
                                                   (asset
                                                    "GLTR"
                                                    "abrdn Physical Precious Metals Basket Shares ETF")
                                                   (asset
                                                    "DBB"
                                                    "Invesco DB Base Metals Fund")])])])
                                             (group
                                              "Bonds"
                                              [(weight-equal
                                                [(filter
                                                  (moving-average-return
                                                   {:window 10})
                                                  (select-top 3)
                                                  [(asset
                                                    "AGG"
                                                    "iShares Core U.S. Aggregate Bond ETF")
                                                   (asset
                                                    "BND"
                                                    "Vanguard Total Bond Market ETF")
                                                   (asset
                                                    "BNDX"
                                                    "Vanguard Total International Bond ETF")
                                                   (asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                   (asset
                                                    "IEF"
                                                    "iShares 7-10 Year Treasury Bond ETF")
                                                   (asset
                                                    "EMB"
                                                    "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                   (asset
                                                    "BWX"
                                                    "SPDR Bloomberg International Treasury Bond ETF")
                                                   (asset
                                                    "SHV"
                                                    "iShares Short Treasury Bond ETF")
                                                   (asset
                                                    "VGSH"
                                                    "Vanguard Short-Term Treasury ETF")
                                                   (asset
                                                    "GBIL"
                                                    "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                   (asset
                                                    "TYD"
                                                    "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                   (asset
                                                    "HYG"
                                                    "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                   (asset
                                                    "TBT"
                                                    "ProShares UltraShort 20+ Year Treasury")
                                                   (asset
                                                    "TMV"
                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])
                                                 (filter
                                                  (max-drawdown
                                                   {:window 20})
                                                  (select-bottom 3)
                                                  [(asset
                                                    "AGG"
                                                    "iShares Core U.S. Aggregate Bond ETF")
                                                   (asset
                                                    "BND"
                                                    "Vanguard Total Bond Market ETF")
                                                   (asset
                                                    "BNDX"
                                                    "Vanguard Total International Bond ETF")
                                                   (asset
                                                    "BIL"
                                                    "SPDR Bloomberg 1-3 Month T-Bill ETF")
                                                   (asset
                                                    "IEF"
                                                    "iShares 7-10 Year Treasury Bond ETF")
                                                   (asset
                                                    "EMB"
                                                    "iShares JP Morgan USD Emerging Markets Bond ETF")
                                                   (asset
                                                    "BWX"
                                                    "SPDR Bloomberg International Treasury Bond ETF")
                                                   (asset
                                                    "SHV"
                                                    "iShares Short Treasury Bond ETF")
                                                   (asset
                                                    "VGSH"
                                                    "Vanguard Short-Term Treasury ETF")
                                                   (asset
                                                    "GBIL"
                                                    "Goldman Sachs Access Treasury 0-1 Year ETF")
                                                   (asset
                                                    "TYD"
                                                    "Direxion Daily 7-10 Year Treasury Bull 3x Shares")
                                                   (asset
                                                    "TMF"
                                                    "Direxion Daily 20+ Year Treasury Bull 3X Shares")
                                                   (asset
                                                    "HYG"
                                                    "iShares iBoxx $ High Yield Corporate Bond ETF")
                                                   (asset
                                                    "TBT"
                                                    "ProShares UltraShort 20+ Year Treasury")
                                                   (asset
                                                    "TMV"
                                                    "Direxion Daily 20+ Year Treasury Bear 3x Shares")])])])])])])])])])])])
                             (group
                              "FTLT"
                              [(weight-equal
                                [(if
                                  (>
                                   (current-price "SPY")
                                   (moving-average-price
                                    "SPY"
                                    {:window 200}))
                                  [(weight-equal
                                    [(if
                                      (> (rsi "QQQ" {:window 10}) 79)
                                      [(asset
                                        "BIL"
                                        "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")]
                                      [(weight-equal
                                        [(if
                                          (>
                                           (rsi "SPY" {:window 10})
                                           80)
                                          [(asset
                                            "BIL"
                                            "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF")]
                                          [(weight-equal
                                            [(if
                                              (>
                                               (rsi "QQQ" {:window 60})
                                               60)
                                              [(weight-specified
                                                1
                                                (asset
                                                 "QQQ"
                                                 "Invesco Capital Management LLC - Invesco QQQ Trust Series 1"))]
                                              [(asset
                                                "TQQQ"
                                                "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])
                                           (weight-equal
                                            [(asset
                                              "TQQQ"
                                              "ProShares Trust - ProShares UltraPro QQQ 3x Shares")])])])])])]
                                  [(weight-equal
                                    [(if
                                      (< (rsi "TQQQ" {:window 10}) 31)
                                      [(asset
                                        "TQQQ"
                                        "ProShares Trust - ProShares UltraPro QQQ 3x Shares")]
                                      [(weight-equal
                                        [(if
                                          (<
                                           (rsi "SPY" {:window 10})
                                           30)
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
                                                   (rsi
                                                    "SQQQ"
                                                    {:window 10})
                                                   31)
                                                  [(asset
                                                    "SQQQ"
                                                    "ProShares UltraPro Short QQQ")]
                                                  [(asset
                                                    "TQQQ"
                                                    "ProShares UltraPro QQQ")])])])])])])])])])])])])])])])])])])])])])])])])]))
